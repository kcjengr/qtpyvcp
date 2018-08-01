#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import _DesignerPlugin

from entry_widget import EntryWidget
class EntryPlugin(_DesignerPlugin):
    def pluginClass(self):
        return EntryWidget
    def toolTip(self):
        return "MDI command entry"

from action_button import ActionButton
class ActionButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionButton
    def toolTip(self):
        return "MDI command entry"

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
