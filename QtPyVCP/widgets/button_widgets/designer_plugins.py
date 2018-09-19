#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import _DesignerPlugin

from action_button import ActionButton
class ActionButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionButton

from subcall_button import SubCallButton
class MacroButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return SubCallButton
    def toolTip(self):
        return "Execute a macro"

from axis_button import AxisActionButton
class AxisActionButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return AxisActionButton
    def toolTip(self):
        return "Axis/Joint action button"

from jog_button import JogButton
class JogButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return JogButton
    def toolTip(self):
        return "Axis/Joint jog button"

from led_button import LEDButton
class LedButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return LEDButton
    def toolTip(self):
        return "LED button"

from action_checkbox import ActionCheckBox
class ActionCheckBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionCheckBox
