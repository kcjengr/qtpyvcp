import linuxcnc
import os

from qtpy.QtCore import Signal
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.info import Info

INFO = Info()
LOG = logger.getLogger(__name__)
from PyQt5.QtCore import QObject

IN_DESIGNER = os.getenv('DESIGNER', False)
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
        # the received parameter, its missing the rotation of the current wcs
        emitted_offset = list(offset)
        active_wcs = self.getWcsOffsets()[self.getActiveWcsIndex()]

        LOG.debug("--------initial offset emitted: {} {}".format(type(offset),offset))
        LOG.debug("--------active wcs: {} {}".format(type(active_wcs), active_wcs))

        emitted_offset.append(self.__getRotationOfActiveWcs())
        LOG.debug("--------correct_offset: {}".format(emitted_offset))
        result = tuple(emitted_offset)
        LOG.debug("--------result: {} {}".format(type(result), result))
        self.g5xOffsetChanged.emit(result)

    def __handleG92OffsetChange(self, offset):
        #LOG.debug("__handleG92OffsetChange: {}".format(type(offset)))
        self.g92OffsetChanged.emit(offset)

    def __handleG5xIndexChange(self, value):
        LOG.debug("__handleG5xIndexChange: {}".format(value - 1))
        self.g5xIndexChanged.emit(value - 1)

    def __handleRotationChangeXY(self, value):
        LOG.debug("__handleRotationChangeXY: {}".format(value))
        active_wcs = self.getWcsOffsets()[self.getActiveWcsIndex()]
        LOG.debug("--------active wcs: {} {}".format(type(active_wcs), active_wcs))
        active_wcs[9] = value
        LOG.debug("--------active new wcs: {} {}".format(type(active_wcs), active_wcs))
        self.g5xOffsetChanged.emit(tuple(active_wcs))

    def __handleOffsetTableChanged(self, offset_table):
        #LOG.debug("__handleOffsetTableChanged: {}".format(type(offset_table)))
        self.offsetTableChanged.emit(offset_table)
        #self.g5xOffsetChanged.emit(self.getActiveWcsOffsets())

    def __handleActiveOffsetChanged(self, active_offset_index):
        # the first one is g53 - machine coordinates, we're not interested in that one
        current_wcs_index = active_offset_index - 1
        LOG.debug("__handleActiveOffsetChanged index: {}".format(current_wcs_index))
        self.activeOffsetChanged.emit(current_wcs_index)

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

    def getActiveWcsIndex(self):
        # in the stat, the first one the list is G53 (Machine Coordinates)
        # therefore to get the correct index of the G54 we need to do a -1
        return self._status.stat.g5x_index - 1

    def getActiveWcsOffsets(self):
        # g5x_offset does not contain the rotation information
        xx = self._status.stat.g5x_offset
        LOG.debug("self._status.stat.g5x_offset: {}".format(type(xx)))
        xy = list(xx)
        xy.append(self.__getRotationOfActiveWcs())
        return tuple(xy)

    def __getRotationOfActiveWcs(self):
        if not IN_DESIGNER:
            current_wcs = self.getWcsOffsets()[self.getActiveWcsIndex()]
            LOG.debug("-----current_wcs index: {}".format(current_wcs))
            return current_wcs[9]
        else:
            return 0

    def getG92_offset(self):
        return self._status.stat.g92_offset

    def getWcsOffsets(self):
        # returns a dictionary with the coordinate systems from 0 to 8 (g54 up to g59.3)
        return self._offsettable.getOffsetTable()