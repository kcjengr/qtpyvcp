#!/usr/bin/env python

from qtpyvcp.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from action_button import ActionButton
class ActionButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionButton

from action_checkbox import ActionCheckBox
class ActionCheckBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionCheckBox

from action_spinbox import ActionSpinBox
class ActionSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionSpinBox

from subcall_button import SubCallButton
class MacroButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return SubCallButton
    def toolTip(self):
        return "Execute a macro"

from led_button import LEDButton
class LedButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return LEDButton
    def toolTip(self):
        return "LED button"

from mdi_button import MDIButton
class MDIButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return MDIButton

from dialog_button import DialogButton
class DialogButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DialogButton