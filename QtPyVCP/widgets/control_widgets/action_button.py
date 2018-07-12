#!/usr/bin/env python

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.utilities import action

class DummyAction(object):
    action_id = -1
    action_text = "NoAction"
    def __init__(self, widget=None, action_type="TOGGLE"):
        pass

class Action(object):
    NoAction = DummyAction.action_id
    EmergencyStop = action.EmergencyStop.action_id
    MachinePower = action.MachinePower.action_id
    Mist = action.Mist.action_id
    Flood = action.Flood.action_id
    BlockDelete = action.BlockDelete.action_id
    OptionalStop = action.OptionalStop.action_id

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

        self._action_id = -1
        self._action_type = -1
        self.setText("NoAction")

    def _setUpAction(self):
        try:
            # Disconnect any existing signals
            self.clicked.disconnect()
        except:
            pass
        act_obj = action.action_by_id.get(self._action_id, DummyAction)
        type_str = ActionType.toString(self._action_type)
        act_inst = act_obj(self, action_type=type_str)
        if self._action_type == ActionType.Toggle:
            type_str = ''
        self.setText("{} {}".format(act_inst.action_text, type_str))


    def getAction(self):
        return self._action_id
    @pyqtSlot(Action)
    def setAction(self, action_id):
        self._action_id = action_id
        self._setUpAction()
    action_id = pyqtProperty(Action, getAction, setAction)

    def getActionType(self):
        return self._action_type
    @pyqtSlot(ActionType)
    def setActionType(self, action_type):
        self._action_type = action_type
        self._setUpAction()
    action_type = pyqtProperty(ActionType, getActionType, setActionType)
