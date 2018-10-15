#!/usr/bin/env python

from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtCore import pyqtProperty

from qtpyvcp.actions import bindWidget

class ActionSpinBox(QSpinBox):
    """Action spinbox for triggering QtPyVCP actions that take a numeric argument.

    On spinbox valueChange the action will be triggered with the spinbox
    value passed as the action argument.

    Args:
        parent (QWidget, optional) : The parent widget of the spindbox, or None.
        action (str, optional) : The name of the action the spindbox should trigger.
    """
    def __init__(self, parent=None, action=None):
        super(ActionSpinBox, self).__init__(parent)

        self._action_name = ''
        if action is not None:
            self.actionName = action

    @pyqtProperty(str)
    def actionName(self):
        """Property for the name of the action the spindbox triggers (str).

        When this property is set it calls :meth:`QtPyVCP.actions.bindWidget`
        to bind the widget to the action.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        self._action_name = action_name
        bindWidget(self, action_name)
