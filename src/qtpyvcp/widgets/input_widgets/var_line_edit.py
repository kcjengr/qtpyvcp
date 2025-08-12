import os
import locale
from qtpy.QtCore import Property, QTimer
from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
from qtpyvcp.widgets.base_widgets import VarWidgetMixin
from qtpyvcp.utilities import logger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.actions.machine_actions import issue_mdi

LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER') != None

def _safe_import_linuxcnc():
    """Import linuxcnc with intelligent error handling"""
    if IN_DESIGNER:
        # Expected in designer mode - don't log
        return None
    
    try:
        import linuxcnc
        return linuxcnc
    except ImportError as e:
        # Unexpected in runtime mode - log the error
        LOG.error(f"Failed to import linuxcnc in runtime mode: {e}")
        return None

def _cnc_float(value):
    """
    Convert string to float using CNC-standard decimal point format.
    
    This function ensures that CNC decimal values (like "1234.5678") are always
    parsed correctly regardless of system locale. It temporarily switches to
    C locale for parsing to avoid locale-dependent float() behavior.
    
    Args:
        value: String or numeric value to convert to float
        
    Returns:
        float: The parsed value
        
    Raises:
        ValueError: If the value cannot be parsed as a CNC decimal number
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        raise ValueError(f"Cannot convert {type(value).__name__} to CNC float")
    
    value = value.strip()
    if not value:
        return 0.0
    
    # Save current locale
    current_locale = locale.getlocale(locale.LC_NUMERIC)
    
    try:
        # Temporarily set C locale for CNC-standard parsing
        locale.setlocale(locale.LC_NUMERIC, 'C')
        result = float(value)
        return result
    except (ValueError, locale.Error) as e:
        raise ValueError(f"Invalid CNC decimal format: '{value}'. Use format like 1234.5678")
    finally:
        # Restore original locale
        try:
            if current_locale[0] is not None:
                locale.setlocale(locale.LC_NUMERIC, current_locale)
        except locale.Error:
            # If we can't restore the locale, log but don't fail
            LOG.warning(f"Could not restore locale {current_locale}")
            pass

class VCPVarLineEdit(VCPLineEdit, VarWidgetMixin):
    """
    LinuxCNC Parameter Line Edit Widget with automatic var file integration.
    
    This widget extends VCPLineEdit to provide direct LinuxCNC parameter access
    with automatic configuration detection. It reads/writes LinuxCNC var parameters
    directly via MDI commands and var file reading.
    
    Key Features:
    - Fully automatic configuration from LinuxCNC ini file
    - 6-decimal precision parameter storage (LinuxCNC var parameter limit)
    - Universal compatibility across different machine configurations
    - Configurable display formatting with displayDecimals property
    - Configurable auto-write functionality with delays
    - Direct parameter file reading for initialization
    - VCP rules functionality from VCPLineEdit base class
    - Safety monitoring with machine state validation
    
    Usage:
    - Simply set the varParameterNumber property in Qt Designer
    - Widget automatically detects and uses the correct parameter file
    - Set displayDecimals property to control display formatting
    - No manual path configuration required
    - Widget automatically disables when machine is not in safe state
    """
    
    def __init__(self, parent=None):
        VCPLineEdit.__init__(self, parent)
        VarWidgetMixin.__init__(self)
        
        # Widget properties for var parameter functionality
        self._auto_write_enabled = True
        self._write_delay = 500  # ms delay before writing to prevent excessive writes
        self._display_decimals = 4  # User-configurable display formatting
        self._require_homed = True  # Safety feature: require machine to be homed
        
        # Status monitoring for safety
        self._status = None
        self._original_enabled_state = True
        
        # Internal 6-decimal storage (LinuxCNC var parameter limit)
        self._internal_value = None
        self._user_just_edited = False
        
        # LinuxCNC configuration (legacy - will be removed)
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
        self.editingFinished.connect(self.onEditingFinished)

    def _loadIniConfiguration(self):
        """Load LinuxCNC ini file and extract parameter file path"""
        linuxcnc = _safe_import_linuxcnc()
        if linuxcnc is None:
            return  # Skip when linuxcnc unavailable (designer mode or error already logged)
            
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
        if not parameter_file:
            LOG.warning("VCPVarLineEdit: PARAMETER_FILE not found in [RS274NGC] section of ini file")
            return
            
        # Handle relative paths by joining with config directory
        if not os.path.isabs(parameter_file):
            self._parameter_file_path = os.path.join(self._config_dir, parameter_file)
        else:
            self._parameter_file_path = parameter_file
            
        LOG.debug(f"VCPVarLineEdit: Parameter file path: {self._parameter_file_path}")

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
            'var_parameter_number': self.var_parameter_number,
            'auto_write_enabled': self._auto_write_enabled,
            'write_delay': self._write_delay,
            'display_decimals': self._display_decimals,
            'var_monitoring_enabled': self.var_monitoring_enabled,
            'parameter_file_exists': os.path.exists(self.getParameterFilePath()) if self.getParameterFilePath() else False
        }

    @Property(int)
    def varParameterNumber(self):
        """LinuxCNC parameter number to write to (e.g., 3014 for #3014)"""
        return self.var_parameter_number

    @varParameterNumber.setter
    def varParameterNumber(self, param_num):
        self.var_parameter_number = param_num
        # Load the current value from VarFileManager when parameter number is set
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

    @Property(int)
    def displayDecimals(self):
        """Number of decimal places to display in the widget"""
        return self._display_decimals

    @displayDecimals.setter
    def displayDecimals(self, decimals):
        self._display_decimals = max(0, min(decimals, 6))  # Cap at 6 decimals max
        # Update display immediately when decimals setting changes
        if self._internal_value is not None:
            self.setDisplayValue(self._internal_value)

    @Property(bool)
    def requireHomed(self):
        """Whether to require machine to be homed before enabling the widget"""
        return self._require_homed

    @requireHomed.setter
    def requireHomed(self, require):
        self._require_homed = bool(require)
        # Re-evaluate enabled state when this property changes
        self._updateEnabledState()

    def _connectStatusPlugin(self):
        """Connect to the status plugin for monitoring machine state"""
        self._status = getPlugin('status')
        if not self._status:
            LOG.warning("VCPVarLineEdit: Status plugin not available")
            return
            
        # Connect to all homed status signal
        self._status.all_axes_homed.notify(self._updateEnabledState)
        LOG.debug("VCPVarLineEdit: Connected to status plugin for homing monitoring")
        # Update initial state
        self._updateEnabledState()

    def _updateEnabledState(self):
        """Update widget enabled state based on machine state"""
        if not self._require_homed:
            # If homing not required, use original enabled state
            super().setEnabled(self._original_enabled_state)
            return
            
        if self._status is None:
            # If no status plugin, default to disabled for safety
            super().setEnabled(False)
            self.setToolTip("Status plugin not available - widget disabled for safety")
            return
            
        # Check if machine is in safe state for parameter editing
        linuxcnc = _safe_import_linuxcnc()
        if linuxcnc is None:
            # Disable widget when linuxcnc unavailable
            super().setEnabled(False)
            self.setToolTip("LinuxCNC not available - widget disabled")
            return
            
        stat = linuxcnc.stat()
        stat.poll()
        
        # Check machine state: ON, HOMED, and IDLE (same as MDI button safety)
        is_machine_on = stat.task_state == linuxcnc.STATE_ON
        is_all_homed = self._status.allHomed()
        is_idle = stat.interp_state == linuxcnc.INTERP_IDLE
        
        is_safe = is_machine_on and is_all_homed and is_idle
        
        if is_safe:
            super().setEnabled(self._original_enabled_state)
            self.setToolTip("")  # Clear any safety tooltip
        else:
            super().setEnabled(False)
            if not is_machine_on:
                self.setToolTip("Widget disabled: Machine must be ON")
            elif not is_all_homed:
                self.setToolTip("Widget disabled: Machine must be HOMED")
            elif not is_idle:
                self.setToolTip("Widget disabled: Machine must be IDLE")

    def setEnabled(self, enabled):
        """Override setEnabled to track original state and respect safety requirements"""
        self._original_enabled_state = enabled
        self._updateEnabledState()

    def formatValue(self, value):
        """Format value for display using displayDecimals setting"""
        if isinstance(value, (int, float)):
            return f"{_cnc_float(value):.{self._display_decimals}f}"
        elif isinstance(value, str):
            # Parse string as float and format it
            float_value = _cnc_float(value)
            return f"{float_value:.{self._display_decimals}f}"
        else:
            return str(value)

    def setValue(self, value):
        """Set the value with 6-decimal internal storage and formatted display"""
        float_value = _cnc_float(value)
        
        # Always store with 6-decimal precision (LinuxCNC var limit)
        self._internal_value = round(float_value, 6)
        
        # Format for display using user-configurable decimals
        self.setDisplayValue(self._internal_value)

    def value(self):
        """Return the stored 6-decimal precision value"""
        if self._internal_value is not None:
            return self._internal_value
        else:
            return round(_cnc_float(self.text()), 6) if self.text() else 0.0

    def setDisplayValue(self, value):
        """Set display value with consistent formatting using displayDecimals"""
        # Skip settings notifications if user just edited to prevent overriding
        if self._user_just_edited:
            return
        
        self.blockSignals(True)
        
        # Always format using displayDecimals setting
        float_value = _cnc_float(value)
        display_text = self.formatValue(float_value)
        self.setText(display_text)
        
        self.blockSignals(False)

    def onEditingFinished(self):
        """Handle user editing with 6-decimal precision storage and display formatting"""
        user_text = self.text()
        if not user_text.strip():
            return
            
        user_value = _cnc_float(user_text)
        
        # Set flag to prevent settings notification from overriding
        self._user_just_edited = True
        
        # Store with 6-decimal precision (LinuxCNC var limit)
        self._internal_value = round(user_value, 6)
        
        # Format display using displayDecimals setting
        formatted_text = self.formatValue(self._internal_value)
        
        self.blockSignals(True)
        self.setText(formatted_text)
        self.blockSignals(False)
        
        self._user_just_edited = False

    def _onTextChanged(self):
        """Handle text changes and schedule LinuxCNC parameter update if auto-write is enabled"""
        # Update internal value when user types
        if self.text():
            try:
                self._internal_value = round(_cnc_float(self.text()), 6)
            except ValueError:
                # Invalid input - don't update internal value yet
                pass
            
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
        """Write the current 6-decimal precision value to LinuxCNC via MDI command"""
        if not self.var_parameter_number > 0:
            LOG.warning("VCPVarLineEdit: parameter number not set")
            return

        # Safety check: ensure machine is in safe state if required
        if self._require_homed and self._status:
            linuxcnc = _safe_import_linuxcnc()
            if linuxcnc is None:
                return  # Skip writing when linuxcnc unavailable
                
            stat = linuxcnc.stat()
            stat.poll()
            
            # Check machine state: ON, HOMED, and IDLE
            is_machine_on = stat.task_state == linuxcnc.STATE_ON
            is_all_homed = self._status.allHomed()
            is_idle = stat.interp_state == linuxcnc.INTERP_IDLE
            
            if not (is_machine_on and is_all_homed and is_idle):
                LOG.warning("VCPVarLineEdit: Cannot write parameter - machine not in safe state")
                return

        # Get the 6-decimal precision value
        if self._internal_value is not None:
            value = self._internal_value
            LOG.debug(f"VCPVarLineEdit: Using internal 6-decimal value: {value}")
        else:
            value = round(_cnc_float(self.text()), 6)
            LOG.debug(f"VCPVarLineEdit: Using text value rounded to 6 decimals: {value}")

        # Use LinuxCNC MDI command to set parameter with 6-decimal precision
        mdi_command = f"#{self.var_parameter_number} = {value:.6f}"
        
        LOG.debug(f"VCPVarLineEdit: Issuing MDI command: {mdi_command}")
        issue_mdi(mdi_command)
        
        LOG.info(f"VCPVarLineEdit: Set parameter #{self.var_parameter_number} = {value:.6f} via MDI")

    def readParameterFromVarFile(self, parameter_number=None):
        """
        Read a parameter value directly from the var file.
        
        Args:
            parameter_number (int): Parameter number to read. If None, uses self._var_parameter_number
            
        Returns:
            float or None: The parameter value with 6-decimal precision, or None if not found
        """
        param_num = parameter_number or self._var_parameter_number
        if not param_num:
            LOG.warning("VCPVarLineEdit: No parameter number specified for reading")
            return None
            
        var_file_path = self.getParameterFilePath()
        if not var_file_path or not os.path.exists(var_file_path):
            LOG.warning(f"VCPVarLineEdit: Parameter file not found: {var_file_path}")
            return None
            
        with open(var_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Parse parameter line: "parameter_number<tab>value"
                parts = line.split('\t')
                if len(parts) >= 2:
                    file_param_num = int(parts[0])
                    if file_param_num == param_num:
                        # Round to 6 decimals to match LinuxCNC var precision
                        value = round(_cnc_float(parts[1]), 6)
                        LOG.debug(f"VCPVarLineEdit: Read parameter #{param_num} = {value:.6f} from var file")
                        return value
                        
        LOG.debug(f"VCPVarLineEdit: Parameter #{param_num} not found in var file")
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
                LOG.debug(f"VCPVarLineEdit: Loaded parameter #{self._var_parameter_number} = {value:.6f}")
            else:
                LOG.debug(f"VCPVarLineEdit: Could not load parameter #{self._var_parameter_number}")

    def onReturnPressed(self):
        """Override to ensure LinuxCNC parameter is updated on return press"""
        # Call parent onReturnPressed for VCP rules functionality
        super(VCPVarLineEdit, self).onReturnPressed()
        
        # Force immediate write to LinuxCNC parameter on return press
        if self._auto_write_enabled:
            self.writeToLinuxCNC(force=True)

    def initialize(self):
        """Initialize the widget - called by VCP system"""
        # Initialize VarWidgetMixin (sets up var file monitoring)
        self._setup_var_monitoring()
        
        # Connect to status plugin for safety monitoring
        self._connectStatusPlugin()
        
        LOG.info(f"VCPVarLineEdit initialized: param #{self.var_parameter_number}, auto_write={self._auto_write_enabled}, require_homed={self._require_homed}")

    def terminate(self):
        """Cleanup when widget is destroyed"""
        # Cleanup var file monitoring
        self._cleanup_var_monitoring()
        
        # Disconnect from status plugin
        if self._status:
            self._status.all_axes_homed.signal.disconnect(self._updateEnabledState)
        
        # Restore original enabled state
        if hasattr(self, '_original_enabled_state'):
            self.setEnabled(self._original_enabled_state)
        
        if self._write_timer.isActive():
            self._write_timer.stop()
        LOG.debug("VCPVarLineEdit terminated")

    # VarWidgetMixin abstract method implementations
    def _load_parameter_value(self, value):
        """Load a parameter value from var file into the line edit widget"""
        # Temporarily disable auto-write to prevent feedback loops
        old_auto_write = self._auto_write_enabled
        self._auto_write_enabled = False
        
        # Set the value using existing setValue method
        self.setValue(value)
        
        # Restore auto-write setting
        self._auto_write_enabled = old_auto_write
        
        LOG.debug(f"VCPVarLineEdit: Loaded parameter value {value} from var file")

    def _get_widget_value(self):
        """Get the current value from the line edit widget"""
        return self.value()

    def _on_parameter_changed(self, param_number, new_value):
        """Handle parameter change notifications from VarFileManager"""
        if param_number == self.var_parameter_number and new_value is not None:
            LOG.debug(f"VCPVarLineEdit: Parameter #{param_number} changed to {new_value}")
            self._load_parameter_value(new_value)
