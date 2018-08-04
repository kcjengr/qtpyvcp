#!/usr/bin/env python

import os

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.core import Status, Action, Info
STATUS = Status()
ACTION = Action()
INFO = Info()

from QtPyVCP.enums import Axis, ReferenceType, Units

SIG_NAMES = {
    0: "motion_type",
    1: "task_state",
    2: "motion_mode",
    3: "interp_state",
    4: "g5x_index",
    5: "program_units",
    6: "gcodes",
    7: "mcodes",
    8: "interpreter_errcode",
}

class LabelType(object):
    motion_type = 0
    task_state = 1
    motion_mode = 2
    interp_state = 3
    g5x_index = 4
    program_units = 5
    gcodes = 6
    mcodes = 7
    interpreter_errcode = 8

class StatusLabel(QLabel, LabelType):

    Q_ENUMS(LabelType)

    def __init__(self, parent=None):
        super(StatusLabel, self).__init__(parent)

        self._label_type = 1
        self.setText(SIG_NAMES[self._label_type])

        STATUS.init_ui.connect(self.initUI)

    def initUI(self):
        sig_name = SIG_NAMES[self._label_type]
        value = getattr(STATUS.stat, sig_name)
        value_str = STATUS.STATE_STRING_LOOKUP.get(sig_name)[value]
        getattr(STATUS, sig_name)[str].connect(self.update)
        self.setText(value_str)

    def update(self, status_str):
        self.setText(status_str)

    def getLabelType(self):
        return self._label_type
    @pyqtSlot(LabelType)
    def setLabelType(self, label_type):
        sig_name = SIG_NAMES[label_type]
        self.setText(sig_name)
        self.setToolTip(sig_name)
        self._label_type = label_type
    label_type = pyqtProperty(LabelType, getLabelType, setLabelType)
