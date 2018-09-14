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
#   LinuxCNC coolant actions

import sys
import linuxcnc
from PyQt5.QtWidgets import QAction

# Set up logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.utilities.status import Status
STATUS = Status()
STAT = STATUS.stat

CMD = linuxcnc.command()



def bindWidget(widget, action):
    """Binds a widget to a program action.

    Args:
        widget (QtWidget) : The widget to bind the action too. Typically `widget`
            would be a QPushButton, QCheckBox or a QAction.

        action (string) : The string identifier of the machine action to bind
            the widget to.
    """
    action = action.replace('-', '_')
    method = reduce(getattr, action.split('.'), sys.modules[__name__])
    if method is None:
        return

    if isinstance(widget, QAction):
        sig = widget.triggered
    else:
        sig = widget.clicked

    sig.connect(method)

    if action.endswith('toggle'):
        widget.setCheckable(True)

    if action.startswith('estop'):
        STATUS.estop.connect(lambda v: widget.setChecked(not v))

    elif action.startswith('power'):
        powerOk(widget)
        STATUS.estop.connect(lambda: powerOk(widget))


class estop:
    """E-Stop action group"""
    @staticmethod
    def activate():
        """Set E-Stop active"""
        LOG.debug("Setting state red<ESTOP>")
        CMD.state(linuxcnc.STATE_ESTOP)

    @staticmethod
    def reset():
        """Resets E-Stop"""
        LOG.debug("Setting state green<ESTOP_RESET>")
        CMD.state(linuxcnc.STATE_ESTOP_RESET)

    @staticmethod
    def toggle():
        """Toggles E-Stop state"""
        if estop.is_activated():
            estop.reset()
        else:
            estop.activate()

    @staticmethod
    def is_activated():
        """Checks if E_Stop is activated.

        Returns:
            bool : True if E-Stop is active, else False.
        """
        return bool(STAT.estop)

def estopOk():
    estopOk.msg = "Estop Machine"
    return True


class power:
    """Power action group"""
    @staticmethod
    def on():
        """Turns machine power On"""
        LOG.debug("Setting state green<ON>")
        CMD.state(linuxcnc.STATE_ON)

    @staticmethod
    def off():
        """Turns machine power Off"""
        LOG.debug("Setting state red<OFF>")
        CMD.state(linuxcnc.STATE_OFF)

    @staticmethod
    def toggle():
        """Toggles machine power On/Off"""
        if power.is_on():
            power.off()
        else:
            power.on()

    @staticmethod
    def is_on():
        """Checks if power is on.

        Returns:
            bool : True if power is on, else False.
        """
        return STAT.task_state == linuxcnc.STATE_ON

def powerOk(widget=None):
    if STAT.task_state == linuxcnc.STATE_ESTOP_RESET:
        ok = True
        msg = "Turn machine on"
    else:
        ok = False
        msg = "Can't turn machine ON until out of E-Stop"

    powerOk.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok




class home:
    def all():
        pass

    def axis(axis):
        pass

    def joint(joint):
        pass


class unhome:
    def all():
        pass

    def axis(axis):
        pass

    def joint(joint):
        pass
