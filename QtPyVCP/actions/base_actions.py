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
#   LinuxCNC basic actions

import linuxcnc
from QtPyVCP.utilities import logger
from QtPyVCP.utilities.info import Info
from QtPyVCP.utilities.status import Status

INFO = Info()
STATUS = Status()
STAT = STATUS.stat
CMD = linuxcnc.command()

# Set up logging
LOG = logger.getLogger(__name__)

def setTaskMode(new_mode):
    """Sets task mode, if possible

    Args:
        new_mode (int) : linuxcnc.MODE_MANUAL, linuxcnc.MODE_MDI or linuxcnc.MODE_AUTO

    Returns:
        bool : True if successful
    """
    if isRunning():
        LOG.error("Can't set mode while machine is running")
        return False
    else:
        CMD.mode(new_mode)
        return True

def isRunning():
    """Returns TRUE if machine is moving due to MDI, program execution, etc."""
    if STAT.state == linuxcnc.RCS_EXEC:
        return True
    else:
        return STAT.task_mode == linuxcnc.MODE_AUTO \
            and STAT.interp_state != linuxcnc.INTERP_IDLE
