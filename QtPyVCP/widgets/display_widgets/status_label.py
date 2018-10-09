#!/usr/bin/env python

import os

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtBoundSignal

# Set up logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.utilities.info import Info
from QtPyVCP.utilities.status import Status
INFO = Info()
STATUS = Status()
STAT = STATUS.stat

IN_DESIGNER = os.getenv('DESIGNER') == 'true'

FORMATS = {
    'motion_type': {
        'tooltip': 'Motion Type',
        },
    'task_state': {
        'tooltip': 'Task State',
        },
    'motion_mode': {
        'tooltip': 'Motion Mode',
        },
    'interp_state': {
        'tooltip': 'Interp State',
        },
    'g5x_index': {
        'tooltip': 'Active Work System',
        },
    'program_units': {
        'tooltip': 'Active Unit System',
        },
    'gcodes': {
        'tooltip': 'Active G-codes',
        },
    'mcodes': {
        'tooltip': 'Active M-codes',
        },
    'interpreter_errcode': {
        'tooltip': 'Interp Error',
        },
    'file': {
        'tooltip': 'Loaded NGC File',
        },
    'feedrate': {
        'format': '{:.0%}',
        'factor': 1,
        'tooltip': 'Feed Override',
        },
    'override': {
        'format': '{:.0%}',
        'factor': 1,
        'tooltip': 'Speed Override',
        },
    'rapidrate': {
        'format': '{:.0%}',
        'factor': 1,
        'tooltip': 'Rapid Override',
        },
    'max_velocity': {
        'format': '{:.2f}',
        'factor': 60,
        'tooltip': 'Max Velocity',
        },
    'current_vel': {
        'format': '{:.1f} {units}/min',
        'factor': 60,
        'tooltip': 'Current Velocity',
        },
    'spindle_speed': {
        'format': '{:.2f} rpm',
        'factor': 1,
        'tooltip': 'Current Spindle Speed'
        },
    'linear_units': {
        'tooltip': 'Machine Unit System',
        },
    'task_mode': {
        'tooltip': "Task Mode",
        },
    }

class StatusLabelNew(QLabel):
    """General purpose button for triggering QtPyVCP actions.

    Args:
        parent (QWidget) : The parent widget of the button, or None.

    Attributes:
        _action_name (str) : The fully qualified name of the action the
            button triggers:
    """
    def __init__(self, parent=None):
        super(StatusLabelNew, self).__init__(parent)

        self._factor = 1
        self._format = '{}'
        self._status_item = ''

    @pyqtProperty(float)
    def factor(self):
        """The `actionName` property for setting the action the button
            should trigger from within QtDesigner.

        Returns:
            str : The action name.
        """
        return self._factor

    @factor.setter
    def factor(self, factor):
        """Sets the name of the action the button should trigger and
            binds the widget to that action.

        Args:
            action_name (str) : A fully qualified action name.
        """
        self._factor = factor

        # force update of value when in designer
        if IN_DESIGNER:
            self.statusItem = self._status_item

    @pyqtProperty(str)
    def format(self):
        """The `actionName` property for setting the action the button
            should trigger from within QtDesigner.

        Returns:
            str : The action name.
        """
        return self._format

    @format.setter
    def format(self, format):
        """Sets the name of the action the button should trigger and
            binds the widget to that action.

        Args:
            action_name (str) : A fully qualified action name.
        """

        self._format = format

        # force update of value when in designer
        if IN_DESIGNER:
            self.statusItem = self._status_item

    @pyqtProperty(str)
    def statusItem(self):
        """The `actionName` property for setting the action the button
            should trigger from within QtDesigner.

        Returns:
            str : The action name.
        """
        return self._status_item

    @statusItem.setter
    def statusItem(self, status_item):
        """Sets the name of the action the button should trigger and
            binds the widget to that action.

        Args:
            action_name (str) : A fully qualified action name.
        """
        self._status_item = status_item

        items = status_item.split('.')
        item = items[0]
        index = None

        try:
            if len(items) == 1:
                value = getattr(STAT, item)
                sig = getattr(STATUS, item)
            elif len(items) == 2:
                index = int(items[1])
                value = getattr(STAT, item)
                sig = getattr(STATUS, item)
            elif len(items) == 3:
                ind = int(items[1])
                key = items[2]
                value = getattr(STAT, item)[ind][key]
                sig = getattr(getattr(STATUS, item)[ind], key)

            if type(sig) != pyqtBoundSignal:
                raise ValueError('Not a valid signal')

        except:
            LOG.exception("")
            self.setText('N/A')
            return

        try:
            value = STATUS.STATE_STRING_LOOKUP[item][value]
            sig[str].connect(lambda v: self.setText(self._format.format(v)))
            self.setText(self._format.format(value))

        except KeyError:

            if isinstance(value, (int, float)) and self._factor != 1:
                try:
                    if index is not None:
                        self.setText(self._format.format(value[index] * self._factor))
                        sig.connect(lambda v: self.setText(self._format.format(v[index] * self._factor)))
                    else:
                        self.setText(self._format.format(value * self._factor))
                        sig.connect(lambda v: self.setText(self._format.format(v * self._factor)))

                except:
                    LOG.warning("Invalid format '{}' for data of type '{}'" \
                        .format(format, value.__class__.__name__))
                    self.setText('FRMT error')

            else:
                try:
                    if index is not None:
                        self.setText(self._format.format(value[index]))
                        sig.connect(lambda v: self.setText(self._format.format(v[index])))
                    else:
                        self.setText(self._format.format(value))
                        sig.connect(lambda v: self.setText(self._format.format(v)))

                except:
                    LOG.warning("Invalid format '{}' for data of type '{}'" \
                        .format(format, value.__class__.__name__))
                    self.setText('FRMT error')

        except:
            LOG.exception('')
