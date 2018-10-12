#!/usr/bin/env python

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtProperty

from QtPyVCP.actions import bindWidget

print QPushButton

class ActionButton(QPushButton):
    """General purpose button for triggering QtPyVCP actions.

    Args:
        action (str, optional) : The name of the action the button should trigger.
        parent (QWidget, optional) : The parent widget of the button, or None.
    """
    def __init__(self, action=None, parent=None):
        super(ActionButton, self).__init__(parent)

        self._action_name = ''
        if action is not None:
            self.actionName = action

    @pyqtProperty(str)
    def actionName(self):
        """Property for the name of the action the button triggers (str).

        When this property is set it calls :meth:`QtPyVCP.actions.bindWidget`
        to bind the widget to the action.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        self._action_name = action_name
        bindWidget(self, action_name)
