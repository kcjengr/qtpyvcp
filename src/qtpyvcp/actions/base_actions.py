import os
import linuxcnc
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import getPlugin

IN_DESIGNER = os.getenv('DESIGNER', False)
if not IN_DESIGNER:
    _STATUS = getPlugin('status')
    
    def _get_stat():
        if _STATUS is not None:
            return _STATUS.stat
        return None
else:
    _STATUS = None
    
    def _get_stat():
        return None

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
        CMD.wait_complete()  # Wait for mode change to complete, like AXIS does
        _get_stat().poll()  # Update status after mode change
        return True

def isRunning():
    """Returns TRUE if machine is moving due to MDI, program execution, etc."""
    if _get_stat().state == linuxcnc.RCS_EXEC:
        return True
    else:
        return _get_stat().task_mode == linuxcnc.MODE_AUTO \
            and _get_stat().interp_state != linuxcnc.INTERP_IDLE
