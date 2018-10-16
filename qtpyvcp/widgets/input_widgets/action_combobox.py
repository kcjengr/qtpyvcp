#!/usr/bin/env python

from qtpy.QtWidgets import QComboBox
from qtpy.QtCore import Property

from qtpyvcp.actions import bindWidget

class ActionComboBox(QComboBox):
    """General purpose combobox for triggering QtPyVCP actions.

    Args:
        parent (QWidget) : The parent widget of the combobox, or None.

    Attributes:
        _action_name (str) : The fully qualified name of the action the
            combobox triggers when the selection is changed.
    """
    def __init__(self, parent=None):
        super(ActionComboBox, self).__init__(parent)

        self._action_name = ''

    @Property(str)
    def actionName(self):
        """The `actionName` property for setting the action the combobox
            should trigger from within QtDesigner.

        Returns:
            str : The action name.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        """Sets the name of the action the button should trigger and
            binds the widget to that action.

        Args:
            action_name (str) : A fully qualified action name.
        """
        self._action_name = action_name
        bindWidget(self, action_name)
