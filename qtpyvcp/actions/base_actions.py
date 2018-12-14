#!/usr/bin/env python
# coding: utf-8

import linuxcnc
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')
STAT = STATUS.stat

INFO = Info()
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
