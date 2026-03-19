import linuxcnc
import os
import hal
import re
import yaml

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

    @staticmethod
    def _normalize_axis_owner(raw_owner, default='head'):
        text = str(raw_owner).strip().lower() if raw_owner is not None else ''
        if text in ('head', 'table'):
            return text
        return default

    @staticmethod
    def _coerce_int(value, default=None):
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value) if value.is_integer() else default

        text = str(value or '').strip()
        if not text:
            return default
        signless = text[1:] if text[0] in ('+', '-') else text
        if signless.isdigit():
            return int(text)
        return default

    @staticmethod
    def _coerce_float(value, default=None):
        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value or '').strip()
        if not text:
            return default
        float_pattern = r'^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?$'
        if re.fullmatch(float_pattern, text):
            return float(text)
        return default

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
        self._arc_division = 64
        raw_arc_division = self._inifile.find("VTK", "ARC_DIVISION")
        if raw_arc_division is not None:
            parsed_arc_division = self._coerce_int(raw_arc_division)
            if parsed_arc_division is not None:
                self._arc_division = max(8, min(1024, parsed_arc_division))
            else:
                LOG.warning("Invalid [VTK] ARC_DIVISION=%r, using default=64", raw_arc_division)

        self._vtk_axis_motion_owner = {
            'X': 'head',
            'Y': 'head',
            'Z': 'head',
            'A': 'head',
            'B': 'head',
            'C': 'head',
        }
        self._vtk_rotary_axis_origin = {
            'A': None,
            'B': None,
            'C': None,
        }
        self._vtk_machine_parts_file = None
        self._vtk_machine_parts_loaded = False
        self._vtk_machine_parts_axes = {}
        self._vtk_active_machine_axes = self._get_active_machine_axes()
        self._vtk_axis_config_report = {
            'strict_mode': False,
            'warnings': [],
            'missing_axes': [],
            'extra_axes': [],
            'invalid_axes': {},
            'missing_machine_parts_axes': [],
            'missing_rotary_origins': [],
        }
        self._last_switchkins_type = 0
        self._last_logged_motion_switchkins_raw = None
        self._last_logged_motion_switchkins_parsed = None
        self._last_logged_kinstype_bits_raw = None
        self._hal_pin_read_error_logged = set()

        self._configure_vtk_machine_axes()
        
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
        tool_number_int = self._coerce_int(tool_number, 0)
        self.toolInSpindleChanged.emit(tool_number_int)

    def getFPS(self):
        return self._fps

    def getArcDivision(self):
        return self._arc_division

    def getAxis(self):
        return self._status.stat.axis

    def getAxisMask(self):
        return self._status.stat.axis_mask

    def getToolTable(self):
        return self._status.stat.tool_table

    def getToolOffset(self):
        return self._status.tool_offset

    def isMachineMetric(self):
        # Prefer explicit INI units so backplot scaling follows the currently
        # loaded machine configuration even if Info() reports stale data.
        ini_units = str(self._inifile.find("TRAJ", "LINEAR_UNITS") or "").strip().lower()
        if ini_units:
            if ini_units in ("mm", "metric", "millimeter", "millimeters", "cm", "centimeter", "centimeters"):
                return True
            if ini_units in ("inch", "in", "imperial", "inches"):
                return False

        return self._info.getIsMachineMetric()

    def getProgramUnits(self):
        return str(self._status.program_units)

    def _hal_get_float(self, pin_name):
        if not pin_name:
            return None
        try:
            raw_value = hal.get_value(pin_name)
        except Exception as exc:
            if pin_name not in self._hal_pin_read_error_logged:
                LOG.warning(
                    "VTK switchkins pin read failed for %s: %s",
                    pin_name,
                    exc,
                )
                self._hal_pin_read_error_logged.add(pin_name)
            return None
        return LinuxCncDataSource._coerce_float(raw_value, None)

    def _switchkins_type_from_status_bits(self):
        b0 = self._hal_get_float('kinstype.is-0')
        b1 = self._hal_get_float('kinstype.is-1')
        b2 = self._hal_get_float('kinstype.is-2')

        if b0 is None and b1 is None and b2 is None:
            return None, (b0, b1, b2)

        v0 = bool((b0 or 0.0) >= 0.5)
        v1 = bool((b1 or 0.0) >= 0.5)
        v2 = bool((b2 or 0.0) >= 0.5)

        if v1 and not v0 and not v2:
            return 1, (b0, b1, b2)
        if v2 and not v0 and not v1:
            return 2, (b0, b1, b2)
        if v0 and not v1 and not v2:
            return 0, (b0, b1, b2)

        return None, (b0, b1, b2)

    def getSwitchkinsType(self):
        # Authoritative runtime source: motion.switchkins-type.
        # Fallback to kinstype.is-* bits when the motion pin is unavailable.
        raw = self._hal_get_float('motion.switchkins-type')
        if raw is not None:
            parsed_switchkins = self._coerce_int(raw)
            if raw != self._last_logged_motion_switchkins_raw or parsed_switchkins != self._last_logged_motion_switchkins_parsed:
                LOG.info(
                    "VTK switchkins pin: motion.switchkins-type raw=%s parsed=%s",
                    raw,
                    parsed_switchkins,
                )
                self._last_logged_motion_switchkins_raw = raw
                self._last_logged_motion_switchkins_parsed = parsed_switchkins
            if parsed_switchkins is not None:
                self._last_switchkins_type = parsed_switchkins
            return self._last_switchkins_type

        bits_value, bits_raw = self._switchkins_type_from_status_bits()
        if bits_raw != self._last_logged_kinstype_bits_raw:
            LOG.info(
                "VTK switchkins pins: kinstype.is-0=%s kinstype.is-1=%s kinstype.is-2=%s resolved=%s",
                bits_raw[0],
                bits_raw[1],
                bits_raw[2],
                bits_value,
            )
            self._last_logged_kinstype_bits_raw = bits_raw
        if bits_value is not None:
            self._last_switchkins_type = int(bits_value)
            return self._last_switchkins_type

        return self._last_switchkins_type

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

    def getAxisMotionOwners(self):
        return dict(self._vtk_axis_motion_owner)

    def getAxisConfigurationDataset(self):
        return {
            'active_machine_axes': list(self._vtk_active_machine_axes),
            'axis_motion_owner': dict(self._vtk_axis_motion_owner),
            'rotary_axis_origin': dict(self._vtk_rotary_axis_origin),
            'machine_parts_file': self._vtk_machine_parts_file,
            'machine_parts_loaded': bool(self._vtk_machine_parts_loaded),
            'machine_parts_axes': dict(self._vtk_machine_parts_axes),
            'validation': {
                'strict_mode': bool(self._vtk_axis_config_report.get('strict_mode')),
                'warnings': list(self._vtk_axis_config_report.get('warnings', [])),
                'missing_axes': list(self._vtk_axis_config_report.get('missing_axes', [])),
                'extra_axes': list(self._vtk_axis_config_report.get('extra_axes', [])),
                'invalid_axes': dict(self._vtk_axis_config_report.get('invalid_axes', {})),
                'missing_machine_parts_axes': list(self._vtk_axis_config_report.get('missing_machine_parts_axes', [])),
                'missing_rotary_origins': list(self._vtk_axis_config_report.get('missing_rotary_origins', [])),
            },
        }

    @staticmethod
    def _parse_vector3(raw_value):
        if raw_value is None:
            return None

        text = str(raw_value).strip()
        if not text:
            return None

        text = text.replace(',', ' ')
        parts = [p for p in text.split() if p]
        if len(parts) < 3:
            return None

        x = LinuxCncDataSource._coerce_float(parts[0], None)
        y = LinuxCncDataSource._coerce_float(parts[1], None)
        z = LinuxCncDataSource._coerce_float(parts[2], None)
        if x is None or y is None or z is None:
            return None
        return (x, y, z)

    @staticmethod
    def _point3_or_none(value):
        if not isinstance(value, (list, tuple)) or len(value) < 3:
            return None
        x = LinuxCncDataSource._coerce_float(value[0], None)
        y = LinuxCncDataSource._coerce_float(value[1], None)
        z = LinuxCncDataSource._coerce_float(value[2], None)
        if x is None or y is None or z is None:
            return None
        return (float(x), float(y), float(z))

    @staticmethod
    def _parse_traj_coordinates(raw_value):
        allowed = {'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W'}
        text = str(raw_value or '').strip().upper()
        if not text:
            return ['X', 'Y', 'Z']

        parsed = []
        for token in text.replace(',', ' ').split():
            if not token:
                continue
            axis = token[0]
            if axis in allowed and axis not in parsed:
                parsed.append(axis)
        return parsed or ['X', 'Y', 'Z']

    def _get_active_machine_axes(self):
        return self._parse_traj_coordinates(self._inifile.find("TRAJ", "COORDINATES"))

    def _resolve_machine_parts_path(self):
        raw = self._inifile.find("VTK", "MACHINE_PARTS")
        text = str(raw or '').strip()
        if not text:
            return None

        if os.path.isabs(text):
            return text

        ini_file = os.getenv("INI_FILE_NAME") or ''
        config_dir = os.path.dirname(ini_file)
        if not config_dir:
            return text
        return os.path.normpath(os.path.join(config_dir, text))

    def _extract_machine_parts_axes(self, machine_parts_data):
        axes = {}

        def walk(node):
            if not isinstance(node, dict):
                return

            axis_raw = node.get('axis')
            if isinstance(axis_raw, str) and axis_raw.strip():
                axis = axis_raw.strip().upper()
                if axis not in axes:
                    axes[axis] = {
                        'axis': axis,
                        'type': str(node.get('type', '')).lower(),
                        'origin': self._point3_or_none(node.get('origin')),
                        'joint': node.get('joint'),
                        'id': node.get('id'),
                    }

            for value in node.values():
                if isinstance(value, dict):
                    walk(value)

        walk(machine_parts_data)
        return axes

    def _warn_vtk(self, message):
        self._vtk_axis_config_report['warnings'].append(message)
        LOG.warning("VTK configuration: %s", message)

    def _configure_vtk_machine_axes(self):
        allowed_axes = ('X', 'Y', 'Z', 'A', 'B', 'C')
        active_axes = [axis for axis in self._vtk_active_machine_axes if axis in allowed_axes]

        configured_axes = []
        invalid_axes = {}
        for axis in allowed_axes:
            raw_owner = self._inifile.find("VTK", axis)
            if raw_owner is None:
                continue

            configured_axes.append(axis)
            owner = self._normalize_axis_owner(raw_owner, default=None)
            if owner in ('head', 'table'):
                self._vtk_axis_motion_owner[axis] = owner
            else:
                invalid_axes[axis] = str(raw_owner)

        strict_mode = bool(configured_axes)
        self._vtk_axis_config_report['strict_mode'] = strict_mode

        if not strict_mode:
            return

        missing_axes = [axis for axis in active_axes if axis not in configured_axes]
        extra_axes = [axis for axis in configured_axes if axis not in active_axes]

        self._vtk_axis_config_report['missing_axes'] = list(missing_axes)
        self._vtk_axis_config_report['extra_axes'] = list(extra_axes)
        self._vtk_axis_config_report['invalid_axes'] = dict(invalid_axes)

        if missing_axes or invalid_axes or extra_axes:
            details = [
                f"machine axes={active_axes}",
                f"vtk axes={configured_axes}",
            ]
            if missing_axes:
                details.append(f"missing={missing_axes}")
            if extra_axes:
                details.append(f"extra={extra_axes}")
            if invalid_axes:
                details.append(f"invalid={invalid_axes}")
            self._warn_vtk("axis ownership map does not match machine axes; " + "; ".join(details))

        machine_parts_path = self._resolve_machine_parts_path()
        self._vtk_machine_parts_file = machine_parts_path

        if machine_parts_path is None:
            self._warn_vtk(
                "MACHINE_PARTS is not set in [VTK]; add MACHINE_PARTS=<yaml> to complete machine-axis simulation metadata"
            )
            return

        if not os.path.isfile(machine_parts_path):
            self._warn_vtk(
                f"MACHINE_PARTS file not found: {machine_parts_path}"
            )
            return

        try:
            with open(machine_parts_path, 'r', encoding='utf-8') as stream:
                machine_parts_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            self._warn_vtk(
                f"MACHINE_PARTS YAML parse failed for {machine_parts_path}: {exc}"
            )
            return
        except OSError as exc:
            self._warn_vtk(
                f"MACHINE_PARTS file read failed for {machine_parts_path}: {exc}"
            )
            return

        if not isinstance(machine_parts_data, dict):
            self._warn_vtk(
                f"MACHINE_PARTS did not parse to a mapping: {machine_parts_path}"
            )
            return

        self._vtk_machine_parts_loaded = True
        self._vtk_machine_parts_axes = self._extract_machine_parts_axes(machine_parts_data)

        yaml_axes = set(self._vtk_machine_parts_axes.keys())
        missing_from_yaml = [axis for axis in active_axes if axis not in yaml_axes]
        if missing_from_yaml:
            self._vtk_axis_config_report['missing_machine_parts_axes'] = list(missing_from_yaml)
            self._warn_vtk(
                f"MACHINE_PARTS is missing active machine axes: {missing_from_yaml}"
            )

        for axis in ('A', 'B', 'C'):
            meta = self._vtk_machine_parts_axes.get(axis)
            if meta is not None:
                self._vtk_rotary_axis_origin[axis] = meta.get('origin')

        missing_rotary_origins = []
        for axis in ('A', 'B', 'C'):
            if axis not in active_axes:
                continue
            if self._vtk_axis_motion_owner.get(axis, 'head') != 'table':
                continue

            meta = self._vtk_machine_parts_axes.get(axis)
            if meta is None:
                continue
            axis_type = str(meta.get('type') or '').lower()
            if axis_type != 'angular':
                self._warn_vtk(
                    f"MACHINE_PARTS axis {axis} should be type=angular for table rotary ownership (got type={axis_type or 'unset'})"
                )
            if meta.get('origin') is None:
                missing_rotary_origins.append(axis)

        self._vtk_axis_config_report['missing_rotary_origins'] = list(missing_rotary_origins)
        if missing_rotary_origins:
            self._warn_vtk(
                f"table rotary axes missing MACHINE_PARTS origin definitions: {missing_rotary_origins}"
            )

        legacy_pivot_keys = []
        for axis in ('A', 'B', 'C'):
            for key_suffix in ('PIVOT', 'ORIGIN', 'ROT_CENTER', 'PIVOT_X', 'PIVOT_Y', 'PIVOT_Z'):
                key = f"{axis}_{key_suffix}"
                if self._inifile.find("VTK", key) is not None:
                    legacy_pivot_keys.append(key)

        if legacy_pivot_keys:
            self._warn_vtk(
                f"legacy VTK pivot keys are ignored; use MACHINE_PARTS origins instead (keys={legacy_pivot_keys})"
            )

    def getRotaryAxisOrigins(self):
        return dict(self._vtk_rotary_axis_origin)

