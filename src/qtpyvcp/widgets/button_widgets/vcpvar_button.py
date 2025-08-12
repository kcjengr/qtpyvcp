import os
import sys
from qtpy.QtCore import Property, QTimer
from qtpy.QtWidgets import QPushButton
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.widgets.base_widgets.var_widget_mixin import VarWidgetMixin
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

class VCPVarPushButton(QPushButton, VCPWidget, VarWidgetMixin):
    """
    LinuxCNC Parameter Push Button Widget with automatic var file integration.
    
    This widget extends QPushButton to provide direct LinuxCNC parameter access
    with automatic configuration detection and boolean/integer output support.
    
    Key Features:
    - Automatic LinuxCNC var file configuration detection
    - Configurable output type (boolean or 0/1 integer)
    - Button state persistence to LinuxCNC var parameters
    - Automatic parameter loading at startup
    - Configurable write delays for timing control
    - VCP rules functionality inherited from VCPWidget
    - Safety monitoring with machine state validation
    
    Usage:
    - Set varParameterNumber property in Qt Designer
    - Configure outputAsInt for desired output format
    - Widget automatically handles var file read/write operations
    - Widget automatically disables when machine is not in safe state
    """

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Text': ['setText', str],
        'Checked': ['setChecked', bool],
        'Value': ['setValue', [bool, int]],
    })

    def __init__(self, parent=None):
        super(VCPVarPushButton, self).__init__(parent)
        
        # Initialize VarWidgetMixin
        VarWidgetMixin.__init__(self)
        
        # Make button checkable by default for toggle behavior
        self.setCheckable(True)
        
        # Widget properties for var parameter functionality
        self._auto_write_enabled = True
        self._write_delay = 500  # ms delay before writing to prevent excessive writes
        self._output_as_int = False  # Default to boolean output
        self._require_homed = True  # Safety feature: require machine to be homed
        
        # Status monitoring for safety
        self._status = None
        self._original_enabled_state = True
        
        # Internal state tracking
        self._internal_value = False
        self._user_just_toggled = False
        
        # Timer for delayed writing
        self._write_timer = QTimer()
        self._write_timer.setSingleShot(True)
        self._write_timer.timeout.connect(self._writeToLinuxCNC)
        
        # Connect to toggle changes
        self.toggled.connect(self._onToggled)

    def getParameterFilePath(self):
        """Get the automatically detected parameter file path"""
        return self.var_file_manager.var_file_path if self.var_file_manager else None

    def getConfigurationInfo(self):
        """
        Get debugging information about the current configuration.
        
        Returns:
            dict: Configuration information including paths and settings
        """
        var_file_path = self.getParameterFilePath()
        return {
            'var_file_path': var_file_path,
            'var_parameter_number': self.var_parameter_number,
            'auto_write_enabled': self._auto_write_enabled,
            'write_delay': self._write_delay,
            'output_as_int': self._output_as_int,
            'require_homed': self._require_homed,
            'var_monitoring_enabled': self.var_monitoring_enabled,
            'parameter_file_exists': os.path.exists(var_file_path) if var_file_path else False
        }

    @Property(int)
    def varParameterNumber(self):
        """LinuxCNC parameter number to write to (e.g., 3014 for #3014)"""
        return self.var_parameter_number

    @varParameterNumber.setter
    def varParameterNumber(self, param_num):
        self.var_parameter_number = int(param_num)

    @Property(bool)
    def autoWriteEnabled(self):
        """Whether to automatically write changes to LinuxCNC parameters"""
        return self._auto_write_enabled

    @autoWriteEnabled.setter
    def autoWriteEnabled(self, enabled):
        self._auto_write_enabled = bool(enabled)

    @Property(int)
    def writeDelay(self):
        """Delay in milliseconds before writing to LinuxCNC after button toggle"""
        return self._write_delay

    @writeDelay.setter
    def writeDelay(self, delay):
        self._write_delay = int(delay)

    @Property(bool)
    def outputAsInt(self):
        """If True, value() returns 0/1 integers. If False (default), returns True/False booleans."""
        return self._output_as_int

    @outputAsInt.setter
    def outputAsInt(self, use_int):
        self._output_as_int = bool(use_int)

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
            LOG.warning("VCPVarPushButton: Status plugin not available")
            return
            
        # Connect to all homed status signal
        self._status.all_axes_homed.notify(self._updateEnabledState)
        LOG.debug("VCPVarPushButton: Connected to status plugin for homing monitoring")
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

    def value(self):
        """Return the current checked state as boolean or integer based on outputAsInt property"""
        checked_state = self.isChecked()
        if self._output_as_int:
            return 1 if checked_state else 0
        else:
            return checked_state

    def setValue(self, value):
        """Set the checked state from a boolean, integer, or compatible value"""
        if isinstance(value, bool):
            self.setChecked(value)
        elif isinstance(value, (int, float)):
            self.setChecked(bool(value))
        elif isinstance(value, str):
            # Handle string representations of boolean values
            value_lower = value.lower().strip()
            if value_lower in ('true', '1', 'yes', 'on'):
                self.setChecked(True)
            elif value_lower in ('false', '0', 'no', 'off'):
                self.setChecked(False)
            else:
                # For numeric strings, convert to float then to bool
                self.setChecked(bool(float(value)))
        else:
            self.setChecked(bool(value))

    def text(self):
        """Override text() to return empty string so parameter collection uses value() instead"""
        return ""  # Return empty string so get_val() falls through to value() method

    def setDisplayChecked(self, checked):
        """Set checked state without triggering signals (for loading from var file)"""
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)

    def _onToggled(self, checked):
        """Handle button toggle and schedule LinuxCNC parameter update if auto-write is enabled"""
        LOG.debug(f"VCPVarPushButton: Button toggled to {checked}")
        
        # Update internal value when user toggles
        self._internal_value = checked
        self._user_just_toggled = True
        
        if self._auto_write_enabled and self.var_parameter_number > 0:
            # Reset the timer to delay the write
            self._write_timer.stop()
            self._write_timer.start(self._write_delay)
        
        # Reset the flag after a short delay
        QTimer.singleShot(100, lambda: setattr(self, '_user_just_toggled', False))

    def writeToLinuxCNC(self, force=False):
        """
        Public method to manually trigger writing to LinuxCNC parameters.
        
        Args:
            force (bool): If True, write immediately without delay
        """
        if force:
            self._writeToLinuxCNC()
        else:
            self._onToggled(self.isChecked())

    def _writeToLinuxCNC(self):
        """Write the current button state to LinuxCNC via MDI command"""
        if not self.var_parameter_number > 0:
            LOG.warning("VCPVarPushButton: parameter number not set")
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
                LOG.warning("VCPVarPushButton: Cannot write parameter - machine not in safe state")
                return

        # Get the button state as 0 or 1
        if self._internal_value is not None:
            value = 1 if self._internal_value else 0
            LOG.debug(f"VCPVarPushButton: Using internal value: {value}")
        else:
            value = 1 if self.isChecked() else 0
            LOG.debug(f"VCPVarPushButton: Using button checked state: {value}")

        # Use LinuxCNC MDI command to set parameter
        mdi_command = f"#{self.var_parameter_number} = {value}"
        
        LOG.debug(f"VCPVarPushButton: Issuing MDI command: {mdi_command}")
        issue_mdi(mdi_command)
        
        LOG.info(f"VCPVarPushButton: Set parameter #{self.var_parameter_number} = {value} via MDI")

    # VarWidgetMixin abstract method implementations
    def _load_parameter_value(self, value):
        """Load parameter value from var file manager into the widget"""
        if value is not None:
            # Temporarily disable auto-write to prevent feedback loop
            old_auto_write = self._auto_write_enabled
            self._auto_write_enabled = False
            # Convert numeric value to boolean (non-zero = True)
            self.setDisplayChecked(bool(value))
            self._auto_write_enabled = old_auto_write
            LOG.debug(f"VCPVarPushButton: Loaded parameter #{self.var_parameter_number} = {bool(value)}")
        else:
            LOG.debug(f"VCPVarPushButton: Could not load parameter #{self.var_parameter_number}")

    def _get_widget_value(self):
        """Get the current widget value for comparison"""
        return 1.0 if self.isChecked() else 0.0

    def initialize(self):
        """Initialize the widget - called by VCP system"""
        # Initialize VarWidgetMixin (sets up var file monitoring)
        self._setup_var_monitoring()
        
        # Connect to status plugin for safety monitoring
        self._connectStatusPlugin()
        
        LOG.info(f"VCPVarPushButton initialized: param #{self.var_parameter_number}, auto_write={self._auto_write_enabled}, require_homed={self._require_homed}")

    def terminate(self):
        """Cleanup when widget is destroyed"""
        # Cleanup VarWidgetMixin (disconnects from var file monitoring)
        self._cleanup_var_monitoring()
        
        # Disconnect from status plugin
        if self._status:
            self._status.all_axes_homed.signal.disconnect(self._updateEnabledState)
        
        # Restore original enabled state
        if hasattr(self, '_original_enabled_state'):
            self.setEnabled(self._original_enabled_state)
        
        if self._write_timer.isActive():
            self._write_timer.stop()
        LOG.debug("VCPVarPushButton terminated")
