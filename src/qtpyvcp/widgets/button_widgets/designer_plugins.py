from qtpyvcp.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from .action_button import ActionButton
class ActionButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionButton

from .action_checkbox import ActionCheckBox
class ActionCheckBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionCheckBox

from .action_spinbox import ActionSpinBox
class ActionSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionSpinBox

from .subcall_button import SubCallButton
class MacroButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return SubCallButton
    def toolTip(self):
        return "Execute a macro"

from .led_button import LEDButton
class LedButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return LEDButton
    def toolTip(self):
        return "LED button"

from .mdi_button import MDIButton
class MDIButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return MDIButton

from .dialog_button import DialogButton
class DialogButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DialogButton

from .vcpvar_button import VCPVarPushButton
class VCPVarPushButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPVarPushButton
    def toolTip(self):
        return "LinuxCNC Parameter Push Button with automatic var file integration"
    def objectName(self):
        return "vcpVarPushButton"
    def whatsThis(self):
        return """
        LinuxCNC Parameter Push Button Widget
        
        This button automatically connects to LinuxCNC parameter files and provides
        direct read/write access to numbered parameters (like #3014). The widget 
        automatically detects the correct parameter file from your LinuxCNC configuration.
        
        Key Properties:
        - varParameterNumber: The parameter number to read/write (e.g., 3014 for #3014)
        - outputAsInt: If true, returns 0/1 integers, otherwise boolean True/False
        - autoWriteEnabled: Automatically write changes to LinuxCNC
        - writeDelay: Delay in milliseconds before writing changes
        """