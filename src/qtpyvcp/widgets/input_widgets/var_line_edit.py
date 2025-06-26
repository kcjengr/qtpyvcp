import os
import re
import linuxcnc
from qtpy.QtCore import Property, QTimer
from qtpy.QtWidgets import QLineEdit
from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

class VCPVarLineEdit(VCPSettingsLineEdit):
    """
    Universal LinuxCNC Parameter Line Edit Widget with automatic configuration.
    
    This widget extends VCPSettingsLineEdit to provide direct LinuxCNC parameter access
    with automatic configuration detection. It eliminates precision loss that occurs when
    values are passed through subroutines by setting full-precision values directly in
    LinuxCNC's parameter table via MDI commands.
    
    The widget automatically configures itself by reading the LinuxCNC ini file to
    determine the parameter file location, making it universally compatible with any
    LinuxCNC configuration without manual setup.
    
    Key Features:
    - Fully automatic configuration from LinuxCNC ini file
    - High-precision parameter storage via MDI commands  
    - Universal compatibility across different machine configurations
    - Configurable auto-write functionality with delays
    - Direct parameter file reading for initialization
    - Built-in error handling and logging
    
    Usage:
    - Simply set the varParameterNumber property in Qt Designer
    - Widget automatically detects and uses the correct parameter file
    - No manual path configuration required
    """
    
    def __init__(self, parent=None):
        super(VCPVarLineEdit, self).__init__(parent)
        
        # Set appropriate focus policy for line edit
        from qtpy.QtCore import Qt
        self.setFocusPolicy(Qt.ClickFocus)
        
        # Widget properties
        self._var_parameter_number = 0
        self._auto_write_enabled = True
        self._write_delay = 500  # ms delay before writing to prevent excessive writes
        
        # Get LinuxCNC ini file and parameter file path automatically
        self._ini_file = None
        self._parameter_file_path = None
        self._config_dir = None
        self._loadIniConfiguration()
        
        # Timer for delayed writing
        self._write_timer = QTimer()
        self._write_timer.setSingleShot(True)
        self._write_timer.timeout.connect(self._writeToLinuxCNC)
        
        # Connect to value changes
        self.textChanged.connect(self._onTextChanged)

    def _loadIniConfiguration(self):
        """Load LinuxCNC ini file and extract parameter file path"""
        try:
            # Get the ini file path from environment variable
            ini_file_name = os.getenv('INI_FILE_NAME')
            if not ini_file_name:
                LOG.warning("VCPVarLineEdit: INI_FILE_NAME environment variable not set")
                return
                
            # Load the ini file
            self._ini_file = linuxcnc.ini(ini_file_name)
            
            # Get config directory from environment
            self._config_dir = os.getenv('CONFIG_DIR', os.path.dirname(ini_file_name))
            
            # Get parameter file from [RS274NGC] section
            parameter_file = self._ini_file.find('RS274NGC', 'PARAMETER_FILE')
            if parameter_file:
                # Handle relative paths by joining with config directory
                if not os.path.isabs(parameter_file):
                    self._parameter_file_path = os.path.join(self._config_dir, parameter_file)
                else:
                    self._parameter_file_path = parameter_file
                    
                LOG.debug(f"VCPVarLineEdit: Parameter file path: {self._parameter_file_path}")
            else:
                LOG.warning("VCPVarLineEdit: PARAMETER_FILE not found in [RS274NGC] section of ini file")
                
        except Exception as e:
            LOG.error(f"VCPVarLineEdit: Error loading ini configuration: {e}")
            self._ini_file = None
            self._parameter_file_path = None

    def getParameterFilePath(self):
        """Get the automatically detected parameter file path"""
        return self._parameter_file_path

    def getConfigurationInfo(self):
        """
        Get debugging information about the current configuration.
        
        Returns:
            dict: Configuration information including paths and settings
        """
        return {
            'ini_file_env': os.getenv('INI_FILE_NAME'),
            'config_dir': self._config_dir,
            'parameter_file_path': self._parameter_file_path,
            'effective_parameter_file_path': self.getParameterFilePath(),
            'var_parameter_number': self._var_parameter_number,
            'auto_write_enabled': self._auto_write_enabled,
            'write_delay': self._write_delay,
            'parameter_file_exists': os.path.exists(self.getParameterFilePath()) if self.getParameterFilePath() else False
        }

    @Property(int)
    def varParameterNumber(self):
        """LinuxCNC parameter number to write to (e.g., 3014 for #3014)"""
        return self._var_parameter_number

    @varParameterNumber.setter
    def varParameterNumber(self, param_num):
        self._var_parameter_number = int(param_num)
        # Optionally load the current value from the var file when parameter number is set
        if param_num > 0 and self.getParameterFilePath():
            # Use a timer to defer loading until after widget is fully initialized
            QTimer.singleShot(100, self.loadParameterValue)

    @Property(bool)
    def autoWriteEnabled(self):
        """Whether to automatically write changes to LinuxCNC parameters"""
        return self._auto_write_enabled

    @autoWriteEnabled.setter
    def autoWriteEnabled(self, enabled):
        self._auto_write_enabled = bool(enabled)

    @Property(int)
    def writeDelay(self):
        """Delay in milliseconds before writing to LinuxCNC after text changes"""
        return self._write_delay

    @writeDelay.setter
    def writeDelay(self, delay):
        self._write_delay = int(delay)
        
    def _onTextChanged(self):
        """Handle text changes and schedule LinuxCNC parameter update if auto-write is enabled"""
        if self._auto_write_enabled and self._var_parameter_number > 0:
            # Reset the timer to delay the write
            self._write_timer.stop()
            self._write_timer.start(self._write_delay)

    def writeToLinuxCNC(self, force=False):
        """
        Public method to manually trigger writing to LinuxCNC parameters.
        
        Args:
            force (bool): If True, write immediately without delay
        """
        if force:
            self._writeToLinuxCNC()
        else:
            self._onTextChanged()

    def _writeToLinuxCNC(self):
        """Write the current high-precision value to LinuxCNC via MDI command"""
        if not self._var_parameter_number > 0:
            LOG.warning("VCPVarLineEdit: parameter number not set")
            return

        try:
            # Get the high-precision value
            if self._high_precision_storage and self._internal_value is not None:
                value = self._internal_value
                LOG.debug(f"VCPVarLineEdit: Using high-precision internal value: {value}")
            else:
                try:
                    value = float(self.text())
                    LOG.debug(f"VCPVarLineEdit: Using text value: {value}")
                except ValueError:
                    LOG.warning(f"VCPVarLineEdit: Invalid numeric value: '{self.text()}'")
                    return

            # Use LinuxCNC MDI command to set parameter
            try:
                from qtpyvcp.actions.machine_actions import issue_mdi
                
                # Format the MDI command to set the parameter
                # Using the #NNNN format for numbered parameters (not #<_NNNN>)
                mdi_command = f"#{self._var_parameter_number} = {value:.15g}"
                
                LOG.debug(f"VCPVarLineEdit: Issuing MDI command: {mdi_command}")
                issue_mdi(mdi_command)
                
                LOG.info(f"VCPVarLineEdit: Set parameter #{self._var_parameter_number} = {value} via MDI")
                
            except ImportError:
                LOG.error("VCPVarLineEdit: Could not import issue_mdi from qtpyvcp.actions.machine_actions")
                # Fallback to direct LinuxCNC command interface
                self._writeToLinuxCNCDirect(value)
                
        except Exception as e:
            LOG.error(f"VCPVarLineEdit: Error setting parameter via MDI: {e}")
            # Try fallback method
            try:
                self._writeToLinuxCNCDirect(value)
            except Exception as fallback_error:
                LOG.error(f"VCPVarLineEdit: Fallback method also failed: {fallback_error}")

    def _writeToLinuxCNCDirect(self, value):
        """
        Fallback method to write directly to LinuxCNC using the command interface
        
        Args:
            value (float): The value to set
        """
        try:
            import linuxcnc
            command = linuxcnc.command()
            
            # Set the parameter using LinuxCNC's MDI command interface
            mdi_cmd = f"#<_{self._var_parameter_number}> = {value:.15g}"
            command.mdi(mdi_cmd)
            
            LOG.info(f"VCPVarLineEdit: Set parameter #{self._var_parameter_number} = {value} via direct LinuxCNC command")
            
        except Exception as e:
            LOG.error(f"VCPVarLineEdit: Error setting parameter via direct LinuxCNC command: {e}")
            raise

    def readParameterFromVarFile(self, parameter_number=None):
        """
        Read a parameter value directly from the var file.
        
        Args:
            parameter_number (int): Parameter number to read. If None, uses self._var_parameter_number
            
        Returns:
            float or None: The parameter value, or None if not found or error
        """
        param_num = parameter_number or self._var_parameter_number
        if not param_num:
            LOG.warning("VCPVarLineEdit: No parameter number specified for reading")
            return None
            
        var_file_path = self.getParameterFilePath()
        if not var_file_path or not os.path.exists(var_file_path):
            LOG.warning(f"VCPVarLineEdit: Parameter file not found: {var_file_path}")
            return None
            
        try:
            with open(var_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    # Parse parameter line: "parameter_number<tab>value"
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            file_param_num = int(parts[0])
                            if file_param_num == param_num:
                                value = float(parts[1])
                                LOG.debug(f"VCPVarLineEdit: Read parameter #{param_num} = {value} from var file")
                                return value
                        except ValueError:
                            continue
                            
            LOG.debug(f"VCPVarLineEdit: Parameter #{param_num} not found in var file")
            return None
            
        except Exception as e:
            LOG.error(f"VCPVarLineEdit: Error reading parameter from var file: {e}")
            return None

    def loadParameterValue(self):
        """Load the parameter value from the var file into the widget"""
        if self._var_parameter_number > 0:
            value = self.readParameterFromVarFile()
            if value is not None:
                # Temporarily disable auto-write to prevent feedback loop
                old_auto_write = self._auto_write_enabled
                self._auto_write_enabled = False
                self.setValue(value)
                self._auto_write_enabled = old_auto_write
                LOG.debug(f"VCPVarLineEdit: Loaded parameter #{self._var_parameter_number} = {value}")
            else:
                LOG.debug(f"VCPVarLineEdit: Could not load parameter #{self._var_parameter_number}")

    def setValue(self, value):
        """Override setValue to trigger LinuxCNC parameter update"""
        super(VCPVarLineEdit, self).setValue(value)
        
        # Schedule LinuxCNC parameter update after settings are updated
        if self._auto_write_enabled:
            self._onTextChanged()

    def onReturnPressed(self):
        """Override to ensure LinuxCNC parameter is updated on return press"""
        super(VCPVarLineEdit, self).onReturnPressed()
        
        # Force immediate write to LinuxCNC parameter on return press
        if self._auto_write_enabled:
            self.writeToLinuxCNC(force=True)