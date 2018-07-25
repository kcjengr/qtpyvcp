#!/usr/bin/env python

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.utilities import action, info
from QtPyVCP.enums import Axis

class JogButton(QPushButton, Axis):

    Q_ENUMS(Axis)

    def __init__(self, parent=None):
        super(JogButton, self).__init__(parent)

        self._axis = Axis.X
        self._direction = 1
        self.setText("Jog +X")

        self.pressed.connect(self.jog)
        self.released.connect(self.stop)


    def _setUpAction(self):
        axis = ['X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'ALL'][self._axis]
        self.setText("Jog {}".format(axis))


    def jog(self):
        print 'JOG'
        self._jog_joint = STAT.motion_mode == linuxcnc.TRAJ_MODE_FREE

        if self.axis in (3,4,5):
            rate = STATUS.angular_jog_velocity / 60
        else:
            rate = STATUS.linear_jog_velocity / 60

        distance = STATUS.jog_increment

        if distance == 0:
            CMD.jog(linuxcnc.JOG_CONTINUOUS,
                    self._jog_joint,
                    self._axis,
                    self._direction * rate)
        else:
            CMD.jog(linuxcnc.JOG_INCREMENT,
                    self._jog_joint,
                    self._axis,
                    self._direction * rate,
                    distance)

    def stop(self):
        CMD.jog(linuxcnc.JOG_STOP,
                self._jog_joint,
                self._axis)


    # def getAction(self):
    #     return self._action_id
    # @pyqtSlot(Action)
    # def setAction(self, action_id):
    #     self._action_id = action_id
    #     self._setUpAction()
    # action_id = pyqtProperty(Action, getAction, setAction)

    def getAxis(self):
        return self._axis
    @pyqtSlot(Axis)
    def setAxis(self, axis):
        self._axis = axis
        self._setUpAction()
    axis = pyqtProperty(Axis, getAxis, setAxis)

    # def getJoint(self):
    #     return self._joint_number
    # @pyqtSlot(ActionType)
    # def setJoint(self, jnum):
    #     self._joint_number = jnum
    #     self._setUpAction()
    # joint_number = pyqtProperty(ActionType, getJoint, setJoint)

    # def getActionType(self):
    #     return self._action_type
    # @pyqtSlot(ActionType)
    # def setActionType(self, action_type):
    #     self._action_type = action_type
    #     self._setUpAction()
    # action_type = pyqtProperty(ActionType, getActionType, setActionType)
