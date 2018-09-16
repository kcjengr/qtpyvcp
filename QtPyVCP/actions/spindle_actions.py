#!/usr/bin/env python
# coding: utf-8

#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   LinuxCNC spindle related actions

import sys
import linuxcnc
from PyQt5.QtWidgets import QAction

# Set up logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.utilities.info import Info
from QtPyVCP.utilities.status import Status
INFO = Info()
STATUS = Status()
STAT = STATUS.stat

CMD = linuxcnc.command()

from QtPyVCP.actions.base_actions import setTaskMode

def bindWidget(widget, action):
    """Binds a widget to an action.

    Args:
        widget (QtWidget) : The widget to bind the action too. Typically `widget`
            would be a QPushButton, QCheckBox or a QAction instance.

        action (string) : The string identifier of the action to bind the widget
            to in the format `action_class.action_name:arg1, arg2 ...`.
    """
    action, sep, args = action.partition(':')
    action = action.replace('-', '_')
    method = reduce(getattr, action.split('.'), sys.modules[__name__])
    if method is None:
        return

    if isinstance(widget, QAction):
        sig = widget.triggered
    else:
        sig = widget.clicked

    if args == '':
        sig.connect(lambda: method())

    else:
        # make a list out of comma separated args
        args = args.replace(' ', '').split(',')
        # convert numbers to int and unicode to str
        args = [int(arg) if arg.isdigit() else str(arg) for arg in args]

        sig.connect(lambda: method(*args))

    # if it is a toggle action make the widget checkable
    if action.endswith('toggle'):
        widget.setCheckable(True)

    if action in ['forward', 'reverse', 'off']:
        _spindleOk(widget)
        STATUS.on.connect(lambda: _spindleOk(widget))
        STATUS.task_mode.connect(lambda: _spindleOk(widget))

def forward(speed=223.23):
    CMD.spindle(linuxcnc.SPINDLE_FORWARD, speed)

def reverse(speed=224.23):
    CMD.spindle(linuxcnc.SPINDLE_REVERSE, speed)

def off():
    CMD.spindle(linuxcnc.SPINDLE_OFF)

def faster():
    """Increase spindle speed by 100rpm"""
    CMD.spindle(linuxcnc.SPINDLE_INCREASE)

def slower():
    """Decreases spindle speed by 100rpm"""
    CMD.spindle(linuxcnc.SPINDLE_DECREASE)

def constant():
    """Unclear"""
    CMD.spindle(linuxcnc.SPINDLE_CONSTANT)

def _spindleOk(widget=None):
    print "###################"
    if STAT.task_state != linuxcnc.STATE_ON:
        ok = False
        msg = "Can't run spindle until machine it ON"
    elif STAT.task_mode == linuxcnc.MODE_AUTO:
        ok = False
        msg = "Machine must be in Manuel mode"
    else:
        ok = True
        msg = ""

    _spindleOk.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

forward.ok = _spindleOk
reverse.ok = _spindleOk
off.ok = _spindleOk
faster.ok = _spindleOk
slower.ok = _spindleOk


class override:
    def enable():
        CMD.set_spindle_override(1)

    def disable():
        CMD.set_spindle_override(0)

    def set(value):
        CMD.spindleoverride(value)

    def reset():
        CMD.spindleoverride(1.0)


class brake:
    @staticmethod
    def on():
        CMD.brake(linuxcnc.BRAKE_ENGAGE)

    @staticmethod
    def off():
        CMD.brake(linuxcnc.BRAKE_RELEASE)

    @staticmethod
    def toggle():
        if brake.it_on():
            brake.off()
        else:
            brake.on()

    @staticmethod
    def is_on():
        return STAT.spindle_brake == linuxcnc.BRAKE_ENGAGE
