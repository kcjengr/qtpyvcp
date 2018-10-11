#!/usr/bin/env python

from QtPyVCP.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from action_button import ActionButton
class ActionButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionButton
    def extensions(self):
        return [ActionButtonPluginExtension,]

from PyQt5.QtWidgets import QDialog
class ActionButtonPluginExtension(_PluginExtension):
    def __init__(self, widget):
        super(ActionButtonPluginExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Edit Action...", self.editAction)

    def editAction(self, state):
        edit_rules_dialog = QDialog(parent=None)
        edit_rules_dialog.exec_()

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
