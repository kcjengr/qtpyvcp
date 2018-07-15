#!/usr/bin/env python
# coding: utf-8

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

class Direction(object):
    Negative = -1
    Null = 0
    Positive = 1

class AxisActionButton(QPushButton, Action, ActionType, Axis, Direction):

    Q_ENUMS(Action)
    Q_ENUMS(ActionType)
    Q_ENUMS(Axis)
    Q_ENUMS(Direction)


    def __init__(self, parent=None):
        super(AxisActionButton, self).__init__(parent)

        self._action_id = -1
        self._action_type = ActionType.Toggle
        self._action_cls = DummyAction

        self._direction = Direction.Null
        self._axis = Axis.X

        self.setText("NoAction")

        STATUS.init_ui.connect(self.init_ui)

    def init_ui(self):
        self._action_cls(widget=self, axis=self._axis, direction=self._direction)

    def setLabel(self):
        self.setText("{} {}{}".format(self._action_cls.action_text,
                                      ['', '+', '−'][self._direction],
                                      ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w', 'all'][self._axis].capitalize()))

    def getActionID(self):
        return self._action_id
    @pyqtSlot(Action)
    def setActionID(self, action_id):
        self._action_id = action_id
        self._action_cls = action.action_by_id.get(self._action_id, DummyAction)
        self.setLabel()
    action_id = pyqtProperty(Action, getActionID, setActionID)

    def getActionType(self):
        return self._action_type
    @pyqtSlot(ActionType)
    def setActionType(self, action_type):
        self._action_type = action_type
        self.setLabel()
    action_type = pyqtProperty(ActionType, getActionType, setActionType)

    def getAxis(self):
        return self._axis
    @pyqtSlot(Axis)
    def setAxis(self, axis):
        self._axis = axis
        self.setLabel()
    axis = pyqtProperty(Axis, getAxis, setAxis)

    def getDirection(self):
        return self._direction
    @pyqtSlot(Direction)
    def setDirection(self, direction):
        print 'Direction: ', 
        self._direction = direction
        self.setLabel()
    direction = pyqtProperty(Direction, getDirection, setDirection)
