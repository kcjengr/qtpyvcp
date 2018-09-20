#!/usr/bin/env python

from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtCore import pyqtProperty

from QtPyVCP.actions import bindWidget

class ActionSpinBox(QSpinBox):
    """General purpose spinbox for setting QtPyVCP action values.

    Args:
        parent (QWidget) : The parent widget of the button, or None.

    Attributes:
        _action_name (str) : The fully qualified name of the action
            method the spinbox triggers:
    """
    def __init__(self, parent=None):
        super(ActionSpinBox, self).__init__(parent)

        self._action_name = ''

    @pyqtProperty(str)
    def actionName(self):
        """The `actionName` property for setting the action method the spinbox
            should trigger.

        Returns:
            str : The action name.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        """Sets the name of the action method the spinbox should trigger and
            binds the widget to that action.

        Args:
            action_name (str) : A fully qualified action name.
        """
        self._action_name = action_name
        bindWidget(self, action_name)
