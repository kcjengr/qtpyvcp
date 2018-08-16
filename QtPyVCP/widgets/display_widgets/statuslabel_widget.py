#!/usr/bin/env python

import os

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.core import Status, Action, Info
STATUS = Status()
ACTION = Action()
INFO = Info()

from QtPyVCP.enums import Axis, ReferenceType, Units

MAPPING = {
    0: {'name': 'motion_type',
        'format': '',
        'tooltip': 'Motion Type',
        },
    1: {'name': 'task_state',
        'format': '',
        'tooltip': 'Task State',
        },
    2: {'name': 'motion_mode',
        'format': '',
        'tooltip': 'Motion Mode',
        },
    3: {'name': 'interp_state',
        'format': '',
        'tooltip': 'Interp State',
        },
    4: {'name': 'g5x_index',
        'format': '',
        'tooltip': 'Active Work System',
        },
    5: {'name': 'program_units',
        'format': '',
        'tooltip': 'Active Unit System',
        },
    6: {'name': 'gcodes',
        'format': '',
        'tooltip': 'Active G-codes',
        },
    7: {'name': 'mcodes',
        'format': '',
        'tooltip': 'Active M-codes',
        },
    8: {'name': 'interpreter_errcode',
        'format': '',
        'tooltip': 'Interp Error',
        },
    9: {'name': 'file',
        'format': '',
        'tooltip': 'Loaded NGC File',
        },
    10: {'name': 'feedrate',
        'format': '{:.0%}',
        'tooltip': 'Feed Override',
        },
    11: {'name': 'spindlerate',
        'format': '{:.0%}',
        'tooltip': 'Speed Override',
        },
    12: {'name': 'rapidrate',
        'format': '{:.0%}',
        'tooltip': 'Rapid Override',
        },
    13: {'name': 'max_velocity',
        'format': '{:.2f}',
        'tooltip': 'Max Velocity',
        },
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
    file = 9
    feed_override = 10
    speed_override = 11
    rapid_override = 12
    max_velocity = 13

class StatusLabel(QLabel, LabelType):

    Q_ENUMS(LabelType)

    def __init__(self, parent=None):
        super(StatusLabel, self).__init__(parent)

        self._label_type = 1
        self.setText(MAPPING[self._label_type]['name'])

        STATUS.init_ui.connect(self.initUI)

    def initUI(self):
        sig_name = MAPPING[self._label_type]['name']
        format_spec = MAPPING[self._label_type]['format']
        tooltip_text = MAPPING[self._label_type]['tooltip']

        value = getattr(STATUS.stat, sig_name)
        try:
            value = STATUS.STATE_STRING_LOOKUP[sig_name][value]
            getattr(STATUS, sig_name)[str].connect(self.update)
        except KeyError:
            if isinstance(value, str) and format_spec == '':
                getattr(STATUS, sig_name).connect(self.update)
            else:
                getattr(STATUS, sig_name).connect(lambda v: self.update(format_spec.format(v)))
                value = format_spec.format(value)
        self.setText(value)

    def update(self, status_str):
        self.setText(status_str)

    def getLabelType(self):
        return self._label_type
    @pyqtSlot(LabelType)
    def setLabelType(self, label_type):
        tooltip = MAPPING[label_type]['tooltip']
        self.setText(tooltip)
        self.setToolTip(tooltip)
        self._label_type = label_type
    label_type = pyqtProperty(LabelType, getLabelType, setLabelType)
