#!/usr/bin/env python

import os
import linuxcnc
from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.core import Status, Action, Prefs, Info
STATUS = Status()
ACTION = Action()
PREFS = Prefs()
INFO = Info()

MAPPING = {
    0: {"cmd_name": "feedrate",
        "stat_name": "feedrate",
        "tooltip": "Feed Override",
        "min": 0,
        "max": INFO.getMaxFeedOverride() * 100,
        },
    1: {"cmd_name": "spindleoverride",
        "stat_name": "spindlerate",
        "tooltip": "Spindle Override",
        "min": INFO.getMinSpindleOverride() * 100,
        "max": INFO.getMaxSpindleOverride() * 100,
        },
    2: {"cmd_name": "rapidrate",
        "stat_name": "rapidrate",
        "tooltip": "Rapid Override",
        "min": 0,
        "max": 100,
        },
    }

class OverrideType(object):
    feed_override = 0
    speed_override = 1
    rapid_override = 2

class OverrideSlider(QSlider, OverrideType):

    Q_ENUMS(OverrideType)
    cmd = linuxcnc.command()

    def __init__(self, parent=None):
        super(OverrideSlider, self).__init__(parent)

        self._override_type = -1
        self._or_method = lambda v:None

        self.valueChanged.connect(self.onValueChanged)

        STATUS.init_ui.connect(self.initUI)

    def initUI(self):
        cmd_name = MAPPING[self._override_type]['cmd_name']
        stat_name = MAPPING[self._override_type]['stat_name']
        tooltip = MAPPING[self._override_type]['tooltip']
        min_val = MAPPING[self._override_type]['min']
        max_val = MAPPING[self._override_type]['max']

        self._or_method = getattr(self.cmd, cmd_name)
        self.setToolTip(self.property("toolTip") or tooltip)
        self.setMinimum(min_val)
        self.setMaximum(max_val)

        # connect to STATUS signal so slider will update when the OR value is
        # changed externally. e.g. thru halui or another GUI
        getattr(STATUS, stat_name).connect(self.updatePos)

        # set initial position of slider
        self.updatePos(getattr(STATUS.stat, stat_name))

    def onValueChanged(self, value):
        self._or_method(float(value) / 100)

    def updatePos(self, pos):
        self.setSliderPosition(pos * 100)

    @pyqtSlot()
    def reset(self):
        self.setValue(100)

    def getOverrideType(self):
        return self._override_type
    @pyqtSlot(OverrideType)
    def setOverrideType(self, override_type):
        self._override_type = override_type
    override_type = pyqtProperty(OverrideType, getOverrideType, setOverrideType)
