import linuxcnc
import os

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger
from qtpy.QtCore import Slot, Signal
from qtpyvcp.utilities.info import Info

INFO = Info()
LOG = logger.getLogger(__name__)

class LinuxCncWrapper:
    #programLoaded = Signal(object)

    def __init__(self):
        self._info = Info()
        self._status = getPlugin('status')
        self._tooltable = getPlugin('tooltable')
        self._offsettable = getPlugin('offsettable')
        self._inifile = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        self._is_lathe = bool(self._inifile.find("DISPLAY", "LATHE"))

        #self._status.file.notify(self.__handleProgramLoaded)

    #def __handleProgramLoaded(self, fname):
     #   self.programLoaded.emit(fname)

    def getAxis(self):
        return self._status.stat.axis

    def getAxisMask(self):
        return self._status.stat.axis_mask

    def getToolTable(self):
        return self._status.stat.tool_table

    def getToolOffset(self):
        return self._status.tool_offset

    def isMetric(self):
        return self._info.getIsMachineMetric()

    def getProgramUnits(self):
        return str(self._status.program_units)

    def isLathe(self):
        return self._is_lathe

    def isModeMdi(self):
        return str(self._status.task_mode) == "MDI"

    def isModeAuto(self):
        return str(self._status.task_mode) == "Auto"

    def getG5x_index(self):
        return self._status.stat.g5x_index

    def getG5x_offset(self):
        return self._status.stat.g5x_offset

    def getG92_offset(self):
        return self._status.stat.g92_offset

    def getRotationXY(self):
        return self._status.stat.rotation_xy

    def getOffsetTable(self):
        return self._offsettable.getOffsetTable()