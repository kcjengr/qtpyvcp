#!/usr/bin/env python

from qtpy.QtWidgets import QPushButton
from qtpy.QtCore import Property

from qtpyvcp.widgets import CMDWidget
from qtpyvcp.actions import bindWidget

class ActionButton(QPushButton, CMDWidget):
    """General purpose button for triggering QtPyVCP actions.

    Args:
        parent (QWidget, optional) : The parent widget of the button, or None.
        action (str, optional) : The name of the action the button should trigger.
    """

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = {
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
        'Opacity': ['setOpacity', float],
        'Text': ['setText', str],
        'Checked': ['setChecked', bool],
        'Style Class': ['setStyleClass', str],
        'None': ['None', None],
    }

    def __init__(self, parent=None, action=None):
        super(ActionButton, self).__init__(parent)

        self._action_name = ''
        if action is not None:
            self.actionName = action

    @Property(str)
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
