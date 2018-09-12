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

import linuxcnc
from PyQt5.QtWidgets import QAction

# Set up logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.utilities.status import Status
STATUS = Status()
STAT = STATUS.stat

CMD = linuxcnc.command()

#==============================================================================
# Coolent actions
#==============================================================================

def bindWidget(widget, action):
    """Binds a widget to a coolant action.

    Args:
        widget (QtWidget) : The widget to bind the action too. Typically `widget`
            would be a QPushButton, QCheckBox or a QAction.

        action (string) : The string name of the coolant action method to bind
            the widget too.

    Example:
        This will create a checkbox for toggling the Flood coolant state. If the
        flood state is changed via another means (e.g. halui) the checkbox state
        will update accordingly.

            btn = QCheckBox("Flood Coolant")
            bindWidget(btn, action="floodToggle")
    """

    if isinstance(widget, QAction):
        sig = widget.triggered
    else:
        sig = widget.clicked
    sig.connect(globals()[action])

    widget.setEnabled(coolantOk(widget))
    STATUS.task_state.connect(lambda: coolantOk(widget))

    if action == "floodToggle":
        widget.setChecked(STAT.flood == linuxcnc.FLOOD_ON)
        STATUS.flood.connect(lambda s: widget.setChecked(s == linuxcnc.FLOOD_ON))
    elif action == "mistToggle":
        widget.setChecked(STAT.mist == linuxcnc.MIST_ON)
        STATUS.mist.connect(lambda s: widget.setChecked(s == linuxcnc.MIST_ON))

def bindKey(key, action):
    # TODO: Add method for binding keypress events to coolant actions.
    raise NotImplemented

def floodOn():
    """Turns Flood coolant ON"""
    LOG.debug("Turning Flood coolant green<ON>")
    CMD.flood(linuxcnc.FLOOD_ON)

def floodOff():
    """Turns Flood coolant OFF"""
    LOG.debug("Turning Flood coolant red<OFF>")
    CMD.flood(linuxcnc.FLOOD_OFF)

def floodToggle():
    """Toggles Flood coolant ON/OFF"""
    if STAT.flood == linuxcnc.FLOOD_ON:
        floodOff()
    else:
        floodOn()

def mistOn():
    """Turns Mist coolant ON"""
    LOG.debug("Turning Mist coolant green<ON>")
    CMD.mist(linuxcnc.MIST_ON)

def mistOff():
    """Turns Mist coolant OFF"""
    LOG.debug("Turning Mist coolant red<OFF>")
    CMD.mist(linuxcnc.MIST_OFF)

def mistToggle():
    """Toggles Mist coolant ON/OFF"""
    if STAT.flood == linuxcnc.MIST_ON:
        mistOff()
    else:
        mistOn()

def coolantOk(widget=None):
    """Checks if it is OK to turn coolant ON.

    Args:
        widget (QWidget, optional) : Widget to enable/disable according to result.

    Atributes:
        msg (string) : The reason the action is not permitted, or empty if permitted.

    Retuns:
        bool : True if OK, else False.

    Example:
        if coolantOk():
            floodOn()
        else:
            print "Can't turn coolant on: ", coolantOk.msg
    """
    if STAT.task_state == linuxcnc.STATE_ON:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Can't turn on coolant when machine is not ON"

    coolantOk.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok
