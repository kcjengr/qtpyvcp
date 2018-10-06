#!/usr/bin/env python

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.core import Status, Info
STATUS = Status()
INFO = Info()

from QtPyVCP.enums import Units

MAPPING = {
    0: {'name': 'motion_type',
        'format': None,
        'tooltip': 'Motion Type',
        },
    1: {'name': 'task_state',
        'format': None,
        'tooltip': 'Task State',
        },
    2: {'name': 'motion_mode',
        'format': None,
        'tooltip': 'Motion Mode',
        },
    3: {'name': 'interp_state',
        'format': None,
        'tooltip': 'Interp State',
        },
    4: {'name': 'g5x_index',
        'format': None,
        'tooltip': 'Active Work System',
        },
    5: {'name': 'program_units',
        'format': None,
        'tooltip': 'Active Unit System',
        },
    6: {'name': 'gcodes',
        'format': None,
        'tooltip': 'Active G-codes',
        },
    7: {'name': 'mcodes',
        'format': None,
        'tooltip': 'Active M-codes',
        },
    8: {'name': 'interpreter_errcode',
        'format': None,
        'tooltip': 'Interp Error',
        },
    9: {'name': 'file',
        'format': None,
        'tooltip': 'Loaded NGC File',
        },
    10: {'name': 'feedrate',
        'format': '{:.0%}',
        'factor': 1,
        'tooltip': 'Feed Override',
        },
    # 11: {'name': 'spindlerate',
    #     'format': '{:.0%}',
    #     'factor': 1,
    #     'tooltip': 'Speed Override',
    #     },
    12: {'name': 'rapidrate',
        'format': '{:.0%}',
        'factor': 1,
        'tooltip': 'Rapid Override',
        },
    13: {'name': 'max_velocity',
        'format': '{:.2f}',
        'factor': 60,
        'tooltip': 'Max Velocity',
        },
    14: {'name': 'current_vel',
        'format': '{:.1f} {units}/min',
        'factor': 60,
        'tooltip': 'Current Velocity',
        },
    # 15: {'name': 'spindle_speed',
    #     'format': '{:.2f} rpm',
    #     'factor': 1,
    #     'tooltip': 'Current Spindle Speed'
    #     },
    16: {'name': 'linear_units',
        'format': None,
        'tooltip': 'Machine Unit System',
        },
    17: {'name': 'task_mode',
        'format': None,
        'tooltip': "Task Mode",
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
    # speed_override = 11
    rapid_override = 12
    max_velocity = 13
    current_vel = 14
    # spindle_speed = 15
    linear_units = 16
    taks_mode = 17

class StatusLabel(QLabel, LabelType):

    Q_ENUMS(LabelType)

    def __init__(self, parent=None):
        super(StatusLabel, self).__init__(parent)

        self._label_type = 1
        self._factor = 1
        self._format_spec = None
        self.setText(MAPPING[self._label_type]['name'])

        STATUS.init_ui.connect(self.initUI)

    def initUI(self):
        sig_name = MAPPING[self._label_type]['name']
        format_spec = self.property('format_spec') or '{}'
        factor = self.property('conv_factor') or 1
        tooltip_text = MAPPING[self._label_type]['tooltip']

        value = getattr(STATUS.stat, sig_name)
        try:
            value = STATUS.STATE_STRING_LOOKUP[sig_name][value]
            sig = getattr(STATUS, sig_name)[str]
        except KeyError:
            # print 'key error', sig_name, value
            sig = getattr(STATUS, sig_name)

        if isinstance(value, str):
            if format_spec is None:
                sig.connect(self.setText)
            else:
                sig.connect(lambda v: self.setText(format_spec.format(v)))
        else:
            sig.connect(lambda v: self.setText(format_spec.format(v * factor, units='in')))
            value = format_spec.format(value * factor, units='in')

        self.setText(value)

    def getLabelType(self):
        return self._label_type
    @pyqtSlot(LabelType)
    def setLabelType(self, label_type):
        tooltip = MAPPING[label_type]['tooltip']
        format_spec = MAPPING[label_type]['format']
        conv_factor = MAPPING[label_type].get('factor')
        self.setText(tooltip)
        self.setToolTip(tooltip)
        self.setProperty('format_spec', format_spec)
        self.setProperty('conv_factor', conv_factor)
        self._label_type = label_type
    label_type = pyqtProperty(LabelType, getLabelType, setLabelType)

    def getFormat(self):
        return self._format_spec
    @pyqtSlot(str)
    def setFormat(self, format_spec):
        self._format_spec = format_spec
    format_spec = pyqtProperty(str, getFormat, setFormat)

    def getFactor(self):
        return self._factor
    @pyqtSlot(float)
    def setFactor(self, factor):
        self._factor = factor
    conv_factor = pyqtProperty(float, getFactor, setFactor)
