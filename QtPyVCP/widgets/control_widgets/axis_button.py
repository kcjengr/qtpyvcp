#!/usr/bin/env python

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.utilities import action, info, status
from QtPyVCP.enums import Axis

STATUS = status.Status()

class DummyAction(object):
    action_id = -1
    action_text = "NoAction"
    def __init__(self, widget=None, action_type="TOGGLE"):
        pass

class Action(object):
    NoAction = DummyAction.action_id
    Home = action.Home.action_id
    Jog = action.Jog.action_id

class ActionType(object):
    Toggle = -1
    Off = 0
    On = 1

    @classmethod
    def toString(cls, action_type):
        return ['OFF', 'ON', 'TOGGLE'][action_type]

class AxisActionButton(QPushButton, Action, ActionType, Axis):

    Q_ENUMS(Action)
    Q_ENUMS(ActionType)
    Q_ENUMS(Axis)

    def __init__(self, parent=None):
        super(AxisActionButton, self).__init__(parent)

        self._action_id = -1
        self._action_type = ActionType.Toggle
        self._action_cls = DummyAction

        self._axis = Axis.X
        self._axis_letter = 'X'

        self.setText("NoAction")

        self.action = None

        STATUS.init_ui.connect(self.init_ui)

    def init_ui(self):
        self.action = self._action_cls(widget=self, axis=self._axis)

    def getAction(self):
        return self._action_id
    @pyqtSlot(Action)
    def setAction(self, action_id):
        self._action_id = action_id
        self._action_cls = action.action_by_id.get(self._action_id, DummyAction)
        self.setText("{} {}".format(self._action_cls.action_text, self._axis_letter))
    action_id = pyqtProperty(Action, getAction, setAction)

    def getAxis(self):
        return self._axis
    @pyqtSlot(Axis)
    def setAxis(self, axis):
        self._axis = axis
        self._axis_letter = ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w', 'all'][self._axis].capitalize()
        self.setText("{} {}".format(self._action_cls.action_text, self._axis_letter))
    axis = pyqtProperty(Axis, getAxis, setAxis)

    # def getJoint(self):
    #     return self._joint_number
    # @pyqtSlot(ActionType)
    # def setJoint(self, jnum):
    #     self._joint_number = jnum
    #     self._setUpAction()
    # joint_number = pyqtProperty(ActionType, getJoint, setJoint)

    def getActionType(self):
        return self._action_type
    @pyqtSlot(ActionType)
    def setActionType(self, action_type):
        self._action_type = action_type
        self._setUpAction()
    action_type = pyqtProperty(ActionType, getActionType, setActionType)
