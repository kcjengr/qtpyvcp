import linuxcnc
import os

from qtpy.QtCore import Signal
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.info import Info

INFO = Info()
LOG = logger.getLogger(__name__)
from PyQt5.QtCore import QObject

"""
This class acts as a datasource for the VTK components.
It abstracts all the linuxcnc specific logic and exposes simple methods that could be eventually 
mocked for testing the VTK outside of a linuxcnc context.
"""
class LinuxCncDataSource(QObject):
    programLoaded = Signal(str)
    positionChanged = Signal(tuple)
    motionTypeChanged = Signal(int)
    g5xOffsetChanged = Signal(tuple)
    g92OffsetChanged = Signal(tuple)
    g5xIndexChanged = Signal(int)
    rotationChanged = Signal(float)
    offsetTableChanged = Signal(dict)
    activeOffsetChanged = Signal(int)
    toolTableChanged = Signal(tuple)
    toolOffsetChanged = Signal(tuple)

    def __init__(self):
        super(LinuxCncDataSource, self).__init__(None)

        self._info = Info()
        self._status = getPlugin('status')
        self._tooltable = getPlugin('tooltable')
        self._offsettable = getPlugin('offsettable')
        self._inifile = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        self._is_lathe = bool(self._inifile.find("DISPLAY", "LATHE"))

        self._status.file.notify(self.__handleProgramLoaded)
        self._status.position.notify(self.__handlePositionChanged)
        self._status.motion_type.notify(self.__handleMotionTypeChanged)
        self._status.g5x_offset.notify(self.__handleG5xOffsetChange)
        self._status.g92_offset.notify(self.__handleG92OffsetChange)

        self._status.g5x_index.notify(self.__handleG5xIndexChange)
        self._status.rotation_xy.notify(self.__handleRotationChangeXY)

        self._offsettable.offset_table_changed.connect(self.__handleOffsetTableChanged)
        self._offsettable.active_offset_changed.connect(self.__handleActiveOffsetChanged)

        self._status.tool_offset.notify(self.__handleToolOffsetChanged)
        self._status.tool_table.notify(self.__handleToolTableChanged)

    def __handleProgramLoaded(self, fname):
        #LOG.debug("__handleProgramLoaded: {}".format(fname))
        self.programLoaded.emit(fname)

    def __handlePositionChanged(self, position):
        #LOG.debug("__handlePositionChanged: {}".format(type(position)))
        self.positionChanged.emit(position)

    def __handleMotionTypeChanged(self, motion_type):
        #LOG.debug("__handleMotionTypeChanged: {}".format(motion_type))
        self.motionTypeChanged.emit(motion_type)

    def __handleG5xOffsetChange(self, offset):
        #LOG.debug("__handleG5xOffsetChange: {}".format(type(offset)))
        self.g5xOffsetChanged.emit(offset)

    def __handleG92OffsetChange(self, offset):
        #LOG.debug("__handleG92OffsetChange: {}".format(type(offset)))
        self.g5xOffsetChanged.emit(offset)

    def __handleG5xIndexChange(self, value):
        LOG.debug("__handleG5xIndexChange: {}".format(type(value)))
        self.g5xIndexChanged.emit(value)

    def __handleRotationChangeXY(self, value):
        LOG.debug("__handleRotationChangeXY: {}".format(type(value)))
        self.rotationChanged.emit(value)

    def __handleOffsetTableChanged(self, offset_table):
        #LOG.debug("__handleOffsetTableChanged: {}".format(type(offset_table)))
        self.offsetTableChanged.emit(offset_table)

    def __handleActiveOffsetChanged(self, active_offset):
        LOG.debug("__handleActiveOffsetChanged: {}".format(type(active_offset)))
        self.activeOffsetChanged.emit(active_offset)

    def __handleToolOffsetChanged(self, tool_offset):
        #LOG.debug("__handleToolOffsetChanged: {}".format(type(tool_offset)))
        self.toolOffsetChanged.emit(tool_offset)

    def __handleToolTableChanged(self, tool_table):
        #LOG.debug("__handleToolTableChanged: {}".format(type(tool_table)))
        self.toolTableChanged.emit(tool_table)

    def getAxis(self):
        return self._status.stat.axis

    def getAxisMask(self):
        return self._status.stat.axis_mask

    def getToolTable(self):
        return self._status.stat.tool_table

    def getToolOffset(self):
        return self._status.tool_offset

    def isMachineMetric(self):
        return self._info.getIsMachineMetric()

    def getProgramUnits(self):
        return str(self._status.program_units)

    def isMachineLathe(self):
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

    def getWcsOffsets(self):
        return self._offsettable.getOffsetTable()