#!/usr/bin/env python

from qtpy.QtWidgets import QCheckBox
from qtpy.QtCore import Property

from qtpyvcp.widgets import CMDWidget
from qtpyvcp.actions import bindWidget

class ActionCheckBox(QCheckBox, CMDWidget):
    """General purpose checkbox for triggering QtPyVCP actions.

    Args:
        parent (QWidget, optional) : The parent widget of the checkbox, or None.
        action (str, optional) : The name of the action the checkbox should trigger.
    """
    def __init__(self, parent=None, action=None):
        super(ActionCheckBox, self).__init__(parent)

        self._action_name = ''
        if action is not None:
            self.actionName = action

    @Property(str)
    def actionName(self):
        """Property for the name of the action the checkbox triggers (str).

        When this property is set it calls :meth:`QtPyVCP.actions.bindWidget`
        to bind the widget to the action.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        self._action_name = action_name
        bindWidget(self, action_name)
