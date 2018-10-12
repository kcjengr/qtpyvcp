#!/usr/bin/env python

"""Testing """

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtProperty

from QtPyVCP.actions import bindWidget

print QPushButton

class ActionButton(QPushButton):
    """General purpose button for triggering QtPyVCP actions.

    Args:
        parent (QWidget) : The parent widget of the button, or None.
    """
    def __init__(self, parent=None):
        super(ActionButton, self).__init__(parent)

        self._action_name = ''

    @pyqtProperty(str)
    def actionName(self):
        """The actionName property defines the name of the action the
        button should trigger.  When the actionName property is set it
        calls :meth:`QtPyVCP.actions.bindWidget` to bind the widget to
        the action.

        Args:
            action_name (str) : A fully qualified action name.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        self._action_name = action_name
        bindWidget(self, action_name)
