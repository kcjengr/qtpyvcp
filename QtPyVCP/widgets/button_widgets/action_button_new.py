#!/usr/bin/env python

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtProperty

from QtPyVCP.actions import bindWidget

class ActionButtonNew(QPushButton):
    """docstring for ActionCheckBox."""
    def __init__(self, parent=None):
        super(ActionButtonNew, self).__init__(parent)

        self._action_name = ''

    @pyqtProperty(str)
    def actionName(self):
        """The fully qualified name of the action the button should trigger.

        Returns:
            str : The action name.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        """Sets the name of the action the button should trigger.

        Args:
            action_name (str) : A fully qualified action name.
        """
        self._action_name = action_name
        bindWidget(self, action_name)
