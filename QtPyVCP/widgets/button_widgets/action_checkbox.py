#!/usr/bin/env python

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP import actions

class ActionCheckBox(QCheckBox):
    """docstring for ActionCheckBox."""
    def __init__(self, parent=None):
        super(ActionCheckBox, self).__init__(parent)

        self._action_id = ''

    @pyqtProperty(str)
    def actionID(self):
        """Action identifier property.

        Returns:
            str : The action ID.
        """
        return self._action_id

    @actionID.setter
    def actionID(self, action_id):
        """
        Sets the action identifier.

        Args:
            action_id (str) :
        """
        self._action_id = action_id

        data = action_id.split('.')
        print data
        module = getattr(actions, data[0])
        print module
        module.bindWidget(self, action=data[1])
