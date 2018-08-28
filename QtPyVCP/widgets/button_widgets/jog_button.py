#!/usr/bin/env python

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.utilities import info, status
from QtPyVCP.utilities.action import Jogging
from QtPyVCP.enums import Axis

STATUS = status.Status()

class Direction(object):
    Negative = -1
    Null = 0
    Positive = 1

class JogButton(QPushButton, Axis, Direction):

    Q_ENUMS(Axis)
    Q_ENUMS(Direction)

    def __init__(self, parent=None):
        super(JogButton, self).__init__(parent)

        self._axis = Axis.X
        self._direction = Direction.Positive
        self.setText("+X")
        STATUS.init_ui.connect(self._setUpAction)

    def _setUpAction(self):
        self.inst = Jogging(widget=self, method='jog', axis=self._axis, direction=self._direction)
        print self.inst

    def _setText(self):
        axis = ['X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'ALL'][self._axis]
        direction = ['', '+', '-'][self._direction]
        print self.property('text')
        if self.property('text') is None:
            print "is none"
            self.setText("{}{}".format(axis, direction))

    def getDirection(self):
        return self._direction
    @pyqtSlot(Direction)
    def setDirection(self, direction):
        self._direction = direction
        self._setText()
    direction = pyqtProperty(Direction, getDirection, setDirection)

    def getAxis(self):
        return self._axis
    @pyqtSlot(Axis)
    def setAxis(self, axis):
        self._axis = axis
        self._setText()
    axis = pyqtProperty(Axis, getAxis, setAxis)
