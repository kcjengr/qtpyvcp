import linuxcnc
import os

from PySide6.QtCore import Signal, QObject
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.load_perf_summary import PROGRAM_LOAD_PERF_SUMMARY

LOG = logger.getLogger('qtpyvcp.' + __name__)
INFO = Info()
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
    rotationXYChanged = Signal(float)
    g92OffsetChanged = Signal(tuple)
    g5xIndexChanged = Signal(int)
    # Use a generic object signal so PySide6 can marshal the Python dict reliably.
    offsetTableChanged = Signal(object)
    activeOffsetChanged = Signal(int)
    toolTableChanged = Signal(tuple)
    toolOffsetChanged = Signal(tuple)
    toolInSpindleChanged = Signal(int)

    def __init__(self):
        super(LinuxCncDataSource, self).__init__(None)

        self._info = Info()
        self._status = getPlugin('status')
        self._tooltable = getPlugin('tooltable')
        self._offsettable = getPlugin('offsettable')
        self._inifile = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        self._keyboard_jog = self._inifile.find("DISPLAY", "KEYBOARD_JOG") or "false"
        self._keyboard_jog_ctrl_off = self._inifile.find("DISPLAY", "KEYBOARD_JOG_SAFETY_OFF") or "false"
        self._is_lathe = (
            bool(self._inifile.find("DISPLAY", "LATHE")) or
            bool(self._inifile.find("DISPLAY", "BACK_TOOL_LATHE"))
        )
        self._is_foam = bool(self._inifile.find("DISPLAY", "FOAM"))
        self._is_jet = bool(self._inifile.find("DISPLAY", "JET"))
        self._machine_bounds = str(self._inifile.find("DISPLAY", "BOUNDARIES"))
        self._nav_helper = bool(self._inifile.find("DISPLAY", "NAV")) or False
        self._antialias = bool(self._inifile.find("DISPLAY", "ANTIALIAS")) or False
        self._fps = int(self._inifile.find("DISPLAY", "FPS") or 0)
        if self._fps == 0:
            self._fps = int(self._inifile.find("VTK", "FPS") or 30)

        self._vtk_kinematics_type = str(self._inifile.find("VTK", "KINEMATICS_TYPE") or "gantry_xyz")
        self._vtk_axis_motion_owner = {
            'X': 'tool',
            'Y': 'tool',
            'Z': 'tool',
            'A': 'tool',
            'B': 'tool',
            'C': 'tool',
        }

        explicit_axis_owner = False
        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
            raw_owner = self._inifile.find("VTK", axis)
            if raw_owner is None:
                continue

            owner = str(raw_owner).strip().lower()
            if owner in ['tool', 'table']:
                self._vtk_axis_motion_owner[axis] = owner
                explicit_axis_owner = True

        # Backward compatibility for old single-value kinematics selector.
        # Per-axis entries take precedence when present.
        if not explicit_axis_owner:
            legacy_mode = self._vtk_kinematics_type.strip().lower()
            if legacy_mode in ['vmc_table_xy', '3_axis_vmc', 'vmc']:
                self._vtk_axis_motion_owner['X'] = 'table'
                self._vtk_axis_motion_owner['Y'] = 'table'
                self._vtk_axis_motion_owner['Z'] = 'tool'
            elif legacy_mode in ['gantry_fixed_y', '3_axis_gantry_fixed_y']:
                self._vtk_axis_motion_owner['X'] = 'tool'
                self._vtk_axis_motion_owner['Y'] = 'table'
                self._vtk_axis_motion_owner['Z'] = 'tool'
        
        self._status.file.notify(self.__handleProgramLoaded)
        self._status.position.notify(self.__handlePositionChanged)
        self._status.motion_type.notify(self.__handleMotionTypeChanged)
        self._status.g5x_offset.notify(self.__handleG5xOffsetChange)
        self._status.g92_offset.notify(self.__handleG92OffsetChange)

        self._status.g5x_index.notify(self.__handleG5xIndexChange)
        # self._status.rotation_xy.notify(self.__handleRotationChangeXY)

        self._offsettable.offset_table_changed.connect(self.__handleOffsetTableChanged)
        # self._offsettable.active_offset_changed.connect(self.__handleActiveOffsetChanged)

        self._status.tool_offset.notify(self.__handleToolOffsetChanged)
        self._status.tool_table.notify(self.__handleToolTableChanged)
        self._status.tool_in_spindle.notify(self.__handleToolInSpindleChanged)

    def __handleProgramLoaded(self, fname):
        PROGRAM_LOAD_PERF_SUMMARY.mark_phase(fname, phase='datasource-program-loaded', percent=45)
        self.programLoaded.emit(fname)

    def __handlePositionChanged(self, position):
        self.positionChanged.emit(position)

    def __handleMotionTypeChanged(self, motion_type):
        self.motionTypeChanged.emit(motion_type)

    def __handleG5xOffsetChange(self, offset):
        # the received parameter, its missing the rotation of the current wcs
        LOG.debug("__handleG5xOffsetChange --- Start")
        emitted_offset = list(offset)
        active_wcs = self.getWcsOffsets()[self.getActiveWcsIndex()]
        #
        LOG.debug("--------initial offset emitted: {} {}".format(type(offset),offset))
        LOG.debug("--------active wcs: {} {}".format(type(active_wcs), active_wcs))
        #
        # # emitted_offset.append(self.__getRotationOfActiveWcs())
        # LOG.debug("--------correct_offset: {}".format(emitted_offset))
        result = tuple(emitted_offset)
        LOG.debug("--------result: {} {}".format(type(result), result))
        self.g5xOffsetChanged.emit(offset)
        LOG.debug("__handleG5xOffsetChange --- End")

    def __handleG92OffsetChange(self, offset):
        self.g92OffsetChanged.emit(offset)

    def __handleG5xIndexChange(self, value):
        self.g5xIndexChanged.emit(value - 1)

    def __handleRotationChangeXY(self, value):
        self.rotationXYChanged.emit(value)

    def __handleOffsetTableChanged(self, offset_table):
        #LOG.debug("__handleOffsetTableChanged: {}".format(type(offset_table)))
        if not offset_table:
            # Offset table should not be empty; force a reread and propagate the fresh table.
            offset_table = self.getWcsOffsets()
            if not offset_table:
                return

        # Ensure a plain dict for PySide6 signal marshalling.
        if isinstance(offset_table, dict):
            offset_table = dict(offset_table)
        
        self.offsetTableChanged.emit(offset_table)
        
        # offset = offset_table[self.getActiveWcsIndex()]
        #
        # self.g5xOffsetChanged.emit(tuple(offset))

    def __handleActiveOffsetChanged(self, active_offset_index):
        # the first one is g53 - machine coordinates, we're not interested in that one
        current_wcs_index = active_offset_index - 1
        self.activeOffsetChanged.emit(current_wcs_index)

    def __handleToolOffsetChanged(self, tool_offset):
        self.toolOffsetChanged.emit(tool_offset)

    def __handleToolTableChanged(self, tool_table):
        self.toolTableChanged.emit(tool_table)

    def __handleToolInSpindleChanged(self, tool_number):
        try:
            self.toolInSpindleChanged.emit(int(tool_number))
        except Exception:
            self.toolInSpindleChanged.emit(0)

    def getFPS(self):
        return self._fps

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
        # Return True if either LATHE or BACK_TOOL_LATHE is set
        return self._is_lathe

    def isMachineFoam(self):
        return self._is_foam
    
    def isMachineJet(self):
        return self._is_jet

    def isModeMdi(self):
        return str(self._status.task_mode) == "MDI"

    def isModeAuto(self):
        return str(self._status.task_mode) == "Auto"

    def isHomed(self):
        return bool(self._status.homed)
    
    def getKeyboardJog(self):
        return self._keyboard_jog
    
    def getKeyboardJogLock(self):
        return self._keyboard_jog_ctrl_off

    def getMachineBounds(self):
        return self._machine_bounds
    
    def getNavHelper(self):
        return self._nav_helper
    
    def getAntialias(self):
        return self._antialias

    def getActiveWcsIndex(self):
        # in the stat, the first one the list is G53 (Machine Coordinates)
        # therefore to get the correct index of the G54 we need to do a -1
        return self._status.stat.g5x_index -1

    def getActiveWcsOffsets(self):
        # g5x_offset does not contain the rotation information
        return self._status.stat.g5x_offset

    def getRotationOfActiveWcs(self):
        return self._status.stat.rotation_xy

    def getG92_offset(self):
        return self._status.stat.g92_offset

    def getWcsOffsets(self):
        # returns a dictionary with the coordinate systems from 0 to 8 (g54 up to g59.3)
        return self._offsettable.getOffsetTable()
    
    def getOffsetColumns(self):
        return self._offsettable.column_labels

    def getKinematicsType(self):
        return self._vtk_kinematics_type

    def getAxisMotionOwners(self):
        return dict(self._vtk_axis_motion_owner)

