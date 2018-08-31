#!/usr/bin/env python

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.utilities import status, action
STATUS = status.Status()

class Action(object):
    EmergencyStop = action.EmergencyStop.action_id
    MachinePower = action.MachinePower.action_id
    Mist = action.Mist.action_id
    Flood = action.Flood.action_id
    BlockDelete = action.BlockDelete.action_id
    OptionalStop = action.OptionalStop.action_id
    JogMode = action.JogMode.action_id
    StepMode = action.StepMode.action_id

class ActionType(object):
    Toggle = -1
    Off = 0
    On = 1

    @classmethod
    def toString(cls, action_type):
        return ['OFF', 'ON', 'TOGGLE'][action_type]

class ActionButton(QPushButton, Action, ActionType):

    Q_ENUMS(Action)
    Q_ENUMS(ActionType)

    def __init__(self, parent=None):
        super(ActionButton, self).__init__(parent)

        self._action_id = 1
        self._action_type = -1
        self._action_inst = None
        self._custom_text = u'\u200b'
        self._setDefaultText()

        STATUS.init_ui.connect(self._setUpAction)

    def _setUpAction(self):
        act_obj = action.action_by_id.get(self._action_id)
        type_str = ActionType.toString(self._action_type)
        self._action_inst = act_obj(self, action_type=type_str)

    def showEvent(self, event=None):
        if self._custom_text != u'\u200b':
            self.setText(self._custom_text)

    def _setDefaultText(self):
        if self._custom_text != u'\u200b':
            return
        act_text = action.action_by_id.get(self._action_id).action_text
        type_str = ' ' + ActionType.toString(self._action_type)
        if self._action_type == ActionType.Toggle:
            type_str = ''
        self.setText("{}{}".format(act_text, type_str))

    @pyqtProperty(Action)
    def actionID(self):
        """
        The ID of the action the button should perform.

        Returns
        -------
        int
        """
        return self._action_id

    @actionID.setter
    def actionID(self, action_id):
        """
        The ID of the action the button should perform.

        Parameters
        ----------
        action_id : int
        """
        self._action_id = action_id
        self._setDefaultText()

    @pyqtProperty(ActionType)
    def actionType(self):
        """
        The type of action the button should perform.
            Toggle = -1
            Off    =  0
            On     =  1

        Returns
        -------
        int
        """
        return self._action_type

    @actionType.setter
    def actionType(self, action_type):
        """
        The type of action the button should perform.
            Toggle = -1
            Off    =  0
            On     =  1

        Parameters
        ----------
        action_type : int
        """
        self._action_type = action_type
        self._setDefaultText()

    @pyqtProperty(str)
    def customText(self):
        """
        Custom button text property.

        Returns
        -------
        str
        """
        return self._custom_text

    @customText.setter
    def customText(self, custom_text):
        """
        Sets the custom button text property to `custom_text`.

        Parameters
        ----------
        custom_text : str
        """
        if custom_text == u'\u200b':
            self._setDefaultText()
        else:
            self._custom_text = custom_text
            self.setText(custom_text)

    @customText.reset
    def customText(self):
        """
        Resets the custom button text property.
        """
        self._custom_text = u'\u200b'
