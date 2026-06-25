# -*- coding: utf-8 -*-

import os
import json
import re

from math import cos, sin, radians

import vtk.qt

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper

from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import getSetting

from qtpyvcp.plugins import iterPlugins, getPlugin
from qtpyvcp.plugins.db_tool_table import DBToolTable

from qtpyvcp.lib.db_tool.base import Session, Base, engine
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool, ToolModel
from qtpyvcp.lib.lathe_insert_geometry import compute_live_insert_profile


LOG = logger.getLogger(__name__)


WIDTH_REMARK_PATTERN = re.compile(r'\bwidth\s*:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', re.IGNORECASE)
NUMBER_PATTERN = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')

_FUSION_TOOL_CACHE_PATH = ''
_FUSION_TOOL_CACHE_MTIME_NS = 0
_FUSION_TOOL_CACHE_BY_NUMBER = {}

# ISO holder style letter -> entering angle (kappa_r) in degrees.
# LinuxCNC conversion:
#   I = 180 - kappa_r
#   J = abs(kappa_r - 90)
_ISO_THSC_LETTER_KAPPA_DEG = {
    'a': 90.0,
    'b': 75.0,
    'c': 90.0,
    'd': 45.0,
    'e': 60.0,
    'f': 90.0,
    'g': 90.0,
    'h': 107.5,
    'j': 93.0,
    'k': 75.0,
    'l': 95.0,
    'm': 86.0,
    'n': 62.5,
    'p': 117.5,
    'q': 107.5,
    'r': 45.0,
    's': 45.0,
    'v': 72.5,
}


def _coerce_int(value, default=0):
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


def _parse_number(value, default=None):
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value or '').strip()
    if not text:
        return default

    match = NUMBER_PATTERN.search(text)
    if match is None:
        return default

    return float(match.group(0))


def _dict_get(mapping, *keys):
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _read_setting_value(setting_name):
    setting_obj = getSetting(setting_name)
    if setting_obj is None:
        return None

    getter = getattr(setting_obj, 'getValue', None)
    if not callable(getter):
        return None

    return getter()


def _normalize_tool_source(raw_value):
    normalized = str(raw_value or '').strip().lower()
    if normalized in ('fusion-json', 'fusion', 'json'):
        return 'fusion-json'
    if normalized in ('linuxcnc', 'tooltable', 'tool-table'):
        return 'linuxcnc'
    return ''


def _resolve_fusion_tool_library_path():
    source_value = _normalize_tool_source(_read_setting_value('lathe-conv.tool-data-source'))
    if source_value != 'fusion-json':
        return ''

    raw_path = str(_read_setting_value('lathe-conv.tool-library-json-path') or '').strip()
    if not raw_path:
        return ''

    normalized_path = os.path.abspath(os.path.expanduser(raw_path))
    if not os.path.isfile(normalized_path):
        return ''

    return normalized_path


def _extract_fusion_tool_number(tool_entry):
    post_number = _parse_number(_dict_get(tool_entry, 'post-process', 'number'), None)
    if post_number is not None and int(post_number) > 0:
        return int(post_number)

    expr_number = _parse_number(_dict_get(tool_entry, 'expressions', 'tool_number'), None)
    if expr_number is not None and int(expr_number) > 0:
        return int(expr_number)

    return 0


def _load_fusion_tools_by_number(json_path):
    global _FUSION_TOOL_CACHE_PATH
    global _FUSION_TOOL_CACHE_MTIME_NS
    global _FUSION_TOOL_CACHE_BY_NUMBER

    path_stat = os.stat(json_path)
    mtime_ns = int(path_stat.st_mtime_ns)

    if _FUSION_TOOL_CACHE_PATH == json_path and _FUSION_TOOL_CACHE_MTIME_NS == mtime_ns:
        return _FUSION_TOOL_CACHE_BY_NUMBER

    with open(json_path, 'r', encoding='utf-8') as handle:
        parsed_doc = json.load(handle)

    raw_tools = parsed_doc.get('data')
    if not isinstance(raw_tools, list):
        _FUSION_TOOL_CACHE_PATH = json_path
        _FUSION_TOOL_CACHE_MTIME_NS = mtime_ns
        _FUSION_TOOL_CACHE_BY_NUMBER = {}
        return _FUSION_TOOL_CACHE_BY_NUMBER

    tools_by_number = {}
    for entry in raw_tools:
        if not isinstance(entry, dict):
            continue

        tool_number = _extract_fusion_tool_number(entry)
        if tool_number <= 0:
            continue

        if tool_number not in tools_by_number:
            tools_by_number[tool_number] = entry

    _FUSION_TOOL_CACHE_PATH = json_path
    _FUSION_TOOL_CACHE_MTIME_NS = mtime_ns
    _FUSION_TOOL_CACHE_BY_NUMBER = tools_by_number
    return _FUSION_TOOL_CACHE_BY_NUMBER


def _resolve_active_tool_number(tool, datasource):
    if tool is not None:
        for attr in ('tool', 'toolno', 'tool_no', 'number', 'id'):
            raw_value = tool.get(attr) if isinstance(tool, dict) else getattr(tool, attr, None)
            parsed = _coerce_int(raw_value, None)
            if parsed is not None and parsed > 0:
                return parsed

    status = getattr(datasource, '_status', None)
    stat = getattr(status, 'stat', None)
    return max(0, _coerce_int(getattr(stat, 'tool_in_spindle', 0), 0))


def _resolve_active_fusion_tool(tool, datasource):
    json_path = _resolve_fusion_tool_library_path()
    if not json_path:
        return None

    tool_number = _resolve_active_tool_number(tool, datasource)
    if tool_number <= 0:
        return None

    try:
        tools_by_number = _load_fusion_tools_by_number(json_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return None

    return tools_by_number.get(tool_number)


def _has_active_fusion_tool_data(fusion_tool, active_tool_number):
    if not isinstance(fusion_tool, dict):
        return False

    if int(active_tool_number or 0) <= 0:
        return False

    fusion_tool_number = _extract_fusion_tool_number(fusion_tool)
    if fusion_tool_number <= 0:
        return False

    return int(fusion_tool_number) == int(active_tool_number)


def _resolve_tool_number_field(tool_entry):
    for attr in ('tool', 'toolno', 'tool_no', 'number', 'id'):
        raw_value = tool_entry.get(attr) if isinstance(tool_entry, dict) else getattr(tool_entry, attr, None)
        parsed = _coerce_int(raw_value, None)
        if parsed is not None:
            return parsed
    return None


def _resolve_tool_orientation_field(tool_entry):
    for attr in ('orientation', 'q_offset', 'qoffset', 'q', 'Q'):
        raw_value = tool_entry.get(attr) if isinstance(tool_entry, dict) else getattr(tool_entry, attr, None)
        parsed = _parse_number(raw_value, None)
        if parsed is not None:
            return int(parsed)
    return 0


def _resolve_tool_angle_field(tool_entry, axis_name):
    if axis_name == 'front':
        attrs = ('frontangle', 'i_offset', 'ioffset', 'i', 'I')
    else:
        attrs = ('backangle', 'j_offset', 'joffset', 'j', 'J')

    for attr in attrs:
        raw_value = tool_entry.get(attr) if isinstance(tool_entry, dict) else getattr(tool_entry, attr, None)
        parsed = _parse_number(raw_value, None)
        if parsed is not None:
            return float(parsed)
    return None


def _resolve_tool_axis_offset(tool_entry, axis_name):
    if axis_name == 'x':
        attrs = ('xoffset', 'x_offset', 'x', 'X')
    else:
        attrs = ('zoffset', 'z_offset', 'z', 'Z')

    for attr in attrs:
        raw_value = tool_entry.get(attr) if isinstance(tool_entry, dict) else getattr(tool_entry, attr, None)
        parsed = _parse_number(raw_value, None)
        if parsed is not None:
            return float(parsed)
    return 0.0


def _resolve_active_tool(tool_table, datasource):
    status = getattr(datasource, '_status', None)
    stat = getattr(status, 'stat', None)
    active_tool = getattr(stat, 'tool_in_spindle', 0)
    active_tool = _coerce_int(active_tool, 0)

    def _entry_tool_number(entry):
        return _resolve_tool_number_field(entry)

    if isinstance(tool_table, dict):
        if active_tool in tool_table:
            return tool_table[active_tool]
        if 0 in tool_table:
            return tool_table[0]
        values = list(tool_table.values())
        return values[0] if values else None

    # LinuxCNC stat.tool_table is often pocket-indexed, not tool-number-indexed.
    # Match by tool number first to avoid selecting wrong geometry/diameter.
    if isinstance(tool_table, (list, tuple)):
        for entry in tool_table:
            if _entry_tool_number(entry) == active_tool:
                return entry

        if 0 <= active_tool < len(tool_table):
            return tool_table[active_tool]

        return tool_table[0] if tool_table else None

    return None


def _extract_width_from_tool_remark(tool, default_width, datasource=None):
    """Return tool edge width parsed from remark text, else default_width.

    Supported remark format examples:
      - "width: 0.1181"
      - "WIDTH: .090"
    """
    def _remark_from_entry(entry):
        if entry is None:
            return ''

        for attr in ('remark', 'comment', 'R'):
            value = getattr(entry, attr, None)
            if value:
                return str(value)

        if isinstance(entry, dict):
            for key in ('R', 'remark', 'comment'):
                value = entry.get(key)
                if value:
                    return str(value)

        return ''

    try:
        remark_text = _remark_from_entry(tool)

        # LinuxCNC status tool entries often do not include remark/comment text.
        # Fallback to the tooltable plugin's canonical per-tool dict ('R').
        if not remark_text and datasource is not None:
            status = getattr(datasource, '_status', None)
            stat = getattr(status, 'stat', None)
            active_tool = _coerce_int(getattr(stat, 'tool_in_spindle', 0), 0)

            tooltable_plugin = getPlugin('tooltable')
            table = tooltable_plugin.getToolTable() if tooltable_plugin else None
            if isinstance(table, dict):
                remark_text = _remark_from_entry(table.get(active_tool))

        match = WIDTH_REMARK_PATTERN.search(remark_text)
        if not match:
            return default_width

        parsed_width = float(match.group(1))
        if parsed_width > 0.0:
            return parsed_width
    except Exception:
        pass

    return default_width

class ToolActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource):
        super(ToolActor, self).__init__()
        self._datasource = linuxcncDataSource
        self._tool_table = self._datasource.getToolTable()
        self.tool = _resolve_active_tool(self._tool_table, self._datasource)

        back_tool_val = (self._datasource._inifile.find("DISPLAY", "BACK_TOOL_LATHE") or "0").strip()
        self._back_tool_lathe = back_tool_val not in ["0", "false", "no", "n", ""]

        self.session = Session()

        colors = vtkNamedColors()

        if self._datasource.isMachineMetric():
            self.height = 25.4 * 2.0
        else:
            self.height = 2.0



        if self._datasource.isMachineFoam():

            transform = vtk.vtkTransform()

            source = vtk.vtkConeSource()
            source.SetHeight(self.height / 2)
            #source.SetCenter(-self.height / 4 - tool.zoffset, -tool.yoffset, -tool.xoffset)
            source.SetCenter(-self.height / 4, 0, 0)
            source.SetRadius(self.height / 4)
            source.SetResolution(64)
            transform.RotateWXYZ(-90, 0, 1, 0)
            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetTransform(transform)
            transform_filter.SetInputConnection(source.GetOutputPort())
            transform_filter.Update()

            # Create a mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(transform_filter.GetOutputPort())

            self.GetProperty().SetColor(colors.GetColor3d('Red'))

        elif self._datasource.isMachineLathe():
            mapper = vtk.vtkPolyDataMapper()
        elif self._datasource.isMachineJet():
            mapper = vtk.vtkPolyDataMapper()
        else:
            tool_id = getattr(self.tool, 'id', 0)
            tool_diameter = getattr(self.tool, 'diameter', 0.0)

            if tool_id == 0 or tool_diameter < .05:
                transform = vtk.vtkTransform()

                source = vtk.vtkConeSource()
                source.SetHeight(self.height / 2)
                #source.SetCenter(-self.height / 4 - tool.zoffset, -tool.yoffset, -tool.xoffset)
                source.SetCenter(-self.height / 4, 0, 0)
                source.SetRadius(self.height / 4)
                source.SetResolution(64)
                transform.RotateWXYZ(90, 0, 1, 0)
                transform_filter = vtk.vtkTransformPolyDataFilter()
                transform_filter.SetTransform(transform)
                transform_filter.SetInputConnection(source.GetOutputPort())
                transform_filter.Update()

                # Create a mapper
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(transform_filter.GetOutputPort())
            else:
                plugins = dict(iterPlugins())
                tool_table_plugin = plugins["tooltable"]

                transform = vtk.vtkTransform()
                # Create a mapper
                mapper = vtk.vtkPolyDataMapper()

                if isinstance(tool_table_plugin, DBToolTable):
                    tool_data = self.session.query(ToolModel).filter(ToolModel.tool_no == tool_id).first()

                    if tool_data:

                        filename = tool_data.model

                        source = vtk.vtkSTLReader()
                        source.SetFileName(filename)

                        # source = vtk.vtkCylinderSource()
                        # source.SetHeight(self.height / 2)
                        # #source.SetCenter(-tool.xoffset, self.height / 4 - tool.zoffset, tool.yoffset)
                        # source.SetCenter(0, self.height / 4, 0)
                        # source.SetRadius(tool.diameter / 2)
                        # source.SetResolution(64)

                        # transform.RotateWXYZ(180, 1, 0, 0)

                        transform_filter = vtk.vtkTransformPolyDataFilter()
                        transform_filter.SetTransform(transform)
                        transform_filter.SetInputConnection(source.GetOutputPort())
                        transform_filter.Update()

                        mapper.SetInputConnection(transform_filter.GetOutputPort())

        self.SetMapper(mapper)

        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(0)


class ToolBitActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource):
        super(ToolBitActor, self).__init__()

        self._datasource = linuxcncDataSource
        self._tool_table = self._datasource.getToolTable()

        back_tool_val = (self._datasource._inifile.find("DISPLAY", "BACK_TOOL_LATHE") or "0").strip()
        self._back_tool_lathe = back_tool_val not in ["0", "false", "no", "n", ""]

        self.tool_position = []
        self.foam_z = 0.0
        self.foam_w = 0.0
        self._smoothed_cnc_rotation = None

        # Visual-only damping to reduce rotational jitter in backplot updates.
        # Position remains exact to avoid drifting from breadcrumb path.
        motion_alpha = _parse_number(_read_setting_value('backplot.tool-bit-motion-alpha'), None)
        if motion_alpha is None:
            motion_alpha = 0.35
        self._cnc_motion_alpha = max(0.0, min(1.0, float(motion_alpha)))

        self.tool = _resolve_active_tool(self._tool_table, self._datasource)
        if self.tool is None:
            self.tool = self._tool_table[0]

        if self._datasource.isMachineMetric():
            self.unit_scale = 25.4
            self.height = 25.4 * 2.0
        else:
            self.unit_scale = 1.0
            self.height = 2.0

        tip_edge = 0.05 * self.unit_scale
        tip_length = 0.5 * self.unit_scale
        stick_length = 1.0 * self.unit_scale
        profile_length = 0.35 * self.unit_scale

        # Allow per-tool lathe edge width override via tool remark, e.g. "width: 0.1181".
        tip_edge = _extract_width_from_tool_remark(self.tool, tip_edge, self._datasource)

        # FOAM TOOL

        if self._datasource.isMachineLathe():

            active_tool_number = _resolve_active_tool_number(self.tool, self._datasource)
            fusion_tool = _resolve_active_fusion_tool(self.tool, self._datasource)
            fusion_mapper = None
            if self.tool.id not in (0, -1) and _has_active_fusion_tool_data(fusion_tool, active_tool_number):
                fusion_mapper = self._make_fusion_lathe_silhouette_mapper(
                    fusion_tool=fusion_tool,
                    default_tip_edge=tip_edge,
                    default_tip_length=tip_length,
                    default_profile_length=profile_length,
                )

            if fusion_mapper is not None:
                mapper = fusion_mapper
            elif self.tool.id == 0 or self.tool.id == -1:
                source = vtk.vtkRegularPolygonSource()
                source.SetNumberOfSides(64)
                source.SetRadius(0.035 * self.unit_scale)
                source.SetCenter(0.0, 0.0, 0.0)

                transform = vtk.vtkTransform()
                transform.RotateWXYZ(90, 1, 0, 0)

                transform_filter = vtk.vtkTransformPolyDataFilter()
                transform_filter.SetTransform(transform)
                transform_filter.SetInputConnection(source.GetOutputPort())
                transform_filter.Update()

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(transform_filter.GetOutputPort())
            else:
                if self.tool.orientation == 1 and self.tool.frontangle == 90 and self.tool.backangle == 90:
                    mapper = self._make_double_sided_quad_mapper([
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset - tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset + tip_length), 0.0, -self.tool.zoffset - tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset + tip_length), 0.0, -self.tool.zoffset),
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset),
                    ])

                elif self.tool.orientation == 2 and self.tool.frontangle == 90 and self.tool.backangle == 90:
                    mapper = self._make_double_sided_quad_mapper([
                        (self._lathe_special_x(-self.tool.xoffset + tip_length), 0.0, -self.tool.zoffset),
                        (self._lathe_special_x(-self.tool.xoffset + tip_length), 0.0, -self.tool.zoffset + tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset + tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset),
                    ])

                elif self.tool.orientation == 3 and self.tool.frontangle == 90 and self.tool.backangle == 90:
                    mapper = self._make_double_sided_quad_mapper([
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset),
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset + tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset - tip_length), 0.0, -self.tool.zoffset + tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset - tip_length), 0.0, -self.tool.zoffset),
                    ])

                elif self.tool.orientation == 4 and self.tool.frontangle == 90 and self.tool.backangle == 90:
                    mapper = self._make_double_sided_quad_mapper([
                        (self._lathe_special_x(-self.tool.xoffset - tip_length), 0.0, -self.tool.zoffset),
                        (self._lathe_special_x(-self.tool.xoffset - tip_length), 0.0, -self.tool.zoffset - tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset - tip_edge),
                        (self._lathe_special_x(-self.tool.xoffset), 0.0, -self.tool.zoffset),
                    ])

                elif self.tool.orientation == 9:

                    radius = self.tool.diameter / 2

                    mapper = self._make_double_sided_quad_mapper([
                        (self._lathe_special_x(-self.tool.xoffset + radius), 0.0, -self.tool.zoffset),
                        (self._lathe_special_x(-self.tool.xoffset + radius), 0.0, -self.tool.zoffset + stick_length),
                        (self._lathe_special_x(-self.tool.xoffset - radius), 0.0, -self.tool.zoffset + stick_length),
                        (self._lathe_special_x(-self.tool.xoffset - radius), 0.0, -self.tool.zoffset),
                    ])
                else:
                    positive = 1
                    negative = -1
                    flip = False

                    if self.tool.orientation == 1:
                        fa_x_pol = negative
                        fa_z_pol = negative

                        ba_x_pol = negative
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 2:
                        fa_x_pol = negative
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = positive

                    elif self.tool.orientation == 3:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = positive
                        ba_z_pol = positive
                        flip = True

                    elif self.tool.orientation == 4:
                        fa_x_pol = positive
                        fa_z_pol = negative

                        ba_x_pol = positive
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 5:
                        fa_x_pol = negative
                        fa_z_pol = negative

                        ba_x_pol = positive
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 6:
                        fa_x_pol = negative
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 7:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = positive

                    elif self.tool.orientation == 8:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = positive
                        ba_z_pol = negative
                    else:
                        fa_x_pol = 0.0
                        fa_z_pol = 0.0

                        ba_x_pol = 0.0
                        ba_z_pol = 0.0

                    A = radians(float(self.tool.frontangle))
                    B = radians(float(self.tool.backangle))
                    C = profile_length

                    p1_x = abs(C * sin(A))
                    p1_z = abs(C * cos(A))

                    p2_x = abs(C * sin(B))
                    p2_z = abs(C * cos(B))

                    p1_x_pos = p1_x * fa_x_pol
                    p1_z_pos = p1_z * fa_z_pol

                    p2_x_pos = p2_x * ba_x_pol
                    p2_z_pos = p2_z * ba_z_pol

                    # Setup three points
                    points = vtk.vtkPoints()

                    if flip:
                        points.InsertNextPoint((self.tool.xoffset + p2_x_pos, 0.0, p2_z_pos - self.tool.zoffset))
                        points.InsertNextPoint((self.tool.xoffset + p1_x_pos, 0.0, p1_z_pos - self.tool.zoffset))
                        points.InsertNextPoint((self.tool.xoffset, 0.0, -self.tool.zoffset))  # Fixed here
                    else:
                        points.InsertNextPoint((self.tool.xoffset, 0.0, -self.tool.zoffset))  # Fixed here
                        points.InsertNextPoint((self.tool.xoffset + p1_x_pos, 0.0, p1_z_pos - self.tool.zoffset))
                        points.InsertNextPoint((self.tool.xoffset + p2_x_pos, 0.0, p2_z_pos - self.tool.zoffset))

                    # Create the polygon
                    polygon = vtk.vtkPolygon()
                    polygon.GetPointIds().SetNumberOfIds(6)  # make a quad
                    polygon.GetPointIds().SetId(0, 0)
                    polygon.GetPointIds().SetId(1, 1)
                    polygon.GetPointIds().SetId(2, 2)

                    polygon.GetPointIds().SetId(3, 2)
                    polygon.GetPointIds().SetId(4, 1)
                    polygon.GetPointIds().SetId(5, 0)

                    # Add the polygon to a list of polygons
                    polygons = vtk.vtkCellArray()
                    polygons.InsertNextCell(polygon)

                    # Create a PolyData
                    polygon_poly_data = vtk.vtkPolyData()
                    polygon_poly_data.SetPoints(points)
                    polygon_poly_data.SetPolys(polygons)

                    transform = vtk.vtkTransform()
                    transform.RotateWXYZ(180, 0, 0, 1)

                    transform_filter = vtk.vtkTransformPolyDataFilter()
                    transform_filter.SetTransform(transform)
                    transform_filter.SetInputData(polygon_poly_data)
                    transform_filter.Update()

                    # Create a mapper
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputConnection(transform_filter.GetOutputPort())

        # LATHE TOOL

        elif self._datasource.isMachineFoam():

            # if self._datasource.isMachineMetric:
            #       self.foam_z *= 254
            #       self.foam_w *= 254
            #


            self.start_point = [self.tool.xoffset, self.tool.yoffset, self.tool.zoffset+self.foam_z]
            self.end_point = [self.tool.uoffset, self.tool.voffset, self.tool.woffset+self.foam_z]

            self.source = vtkLineSource()
            self.source.SetPoint1(self.start_point)
            self.source.SetPoint2(self.end_point)

            transform = vtk.vtkTransform()

            # # source.SetHeight(self.tool.zoffset)
            # source.SetHeight(10)
            # source.SetCenter(self.tool.xoffset, self.tool.zoffset - 5, self.tool.yoffset,)
            # source.SetRadius(self.tool.diameter / 2)
            # source.SetResolution(64)

            transform.RotateWXYZ(0, 1, 0, 0)

            transform.RotateX(self.tool.aoffset)
            transform.RotateY(self.tool.boffset)
            transform.RotateZ(self.tool.coffset)

            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetTransform(transform)
            transform_filter.SetInputConnection(self.source.GetOutputPort())
            transform_filter.Update()
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(transform_filter.GetOutputPort())

        # CNC TOOL

        else:

            self.source = vtkCylinderSource()
            transform = vtk.vtkTransform()


            self.source.SetHeight(self.tool.zoffset)
            self.source.SetCenter(self.tool.xoffset, self.tool.yoffset, -self.tool.zoffset/2)
            self.source.SetRadius(self.tool.diameter / 2)
            self.source.SetResolution(64)

            transform.RotateWXYZ(90, 1, 0, 0)
            
            transform.Translate(self.tool.xoffset, -self.tool.zoffset/2, self.tool.zoffset/2)

            transform.RotateX(self.tool.aoffset)
            transform.RotateY(self.tool.boffset)
            transform.RotateZ(self.tool.coffset)

            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetTransform(transform)
            transform_filter.SetInputConnection(self.source.GetOutputPort())
            transform_filter.Update()
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(transform_filter.GetOutputPort())

        # colors = vtkNamedColors()

        # Create a mapper and actor for the arrow
        # mapper = vtkPolyDataMapper()
        # mapper.SetInputConnection(transform_filter.GetOutputPort())
        #
        #
        self.SetMapper(mapper)

        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(1)

        if self._datasource.isMachineLathe():
            # Match insert visuals for lathe by using a gold silhouette color.
            self.GetProperty().SetColor(0.83, 0.68, 0.22)

    def set_foam_offsets(self, zo, wo):

        self.foam_z = zo
        self.foam_w = wo

    def _lathe_special_x(self, x_value):
        return x_value

    def _make_double_sided_quad_mapper(self, point_list):
        points = vtk.vtkPoints()
        for point in point_list:
            points.InsertNextPoint(point)

        quad_front = vtk.vtkQuad()
        quad_front.GetPointIds().SetId(0, 0)
        quad_front.GetPointIds().SetId(1, 1)
        quad_front.GetPointIds().SetId(2, 2)
        quad_front.GetPointIds().SetId(3, 3)

        quad_back = vtk.vtkQuad()
        quad_back.GetPointIds().SetId(0, 3)
        quad_back.GetPointIds().SetId(1, 2)
        quad_back.GetPointIds().SetId(2, 1)
        quad_back.GetPointIds().SetId(3, 0)

        polygons = vtk.vtkCellArray()
        polygons.InsertNextCell(quad_front)
        polygons.InsertNextCell(quad_back)

        polygon_poly_data = vtk.vtkPolyData()
        polygon_poly_data.SetPoints(points)
        polygon_poly_data.SetPolys(polygons)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polygon_poly_data)
        return mapper

    def _make_double_sided_quads_mapper(self, quad_lists):
        points = vtk.vtkPoints()
        polygons = vtk.vtkCellArray()
        point_index = 0

        for quad_points in quad_lists:
            if len(quad_points) != 4:
                return None

            for point in quad_points:
                points.InsertNextPoint(point)

            quad_front = vtk.vtkQuad()
            quad_front.GetPointIds().SetId(0, point_index + 0)
            quad_front.GetPointIds().SetId(1, point_index + 1)
            quad_front.GetPointIds().SetId(2, point_index + 2)
            quad_front.GetPointIds().SetId(3, point_index + 3)

            quad_back = vtk.vtkQuad()
            quad_back.GetPointIds().SetId(0, point_index + 3)
            quad_back.GetPointIds().SetId(1, point_index + 2)
            quad_back.GetPointIds().SetId(2, point_index + 1)
            quad_back.GetPointIds().SetId(3, point_index + 0)

            polygons.InsertNextCell(quad_front)
            polygons.InsertNextCell(quad_back)
            point_index += 4

        polygon_poly_data = vtk.vtkPolyData()
        polygon_poly_data.SetPoints(points)
        polygon_poly_data.SetPolys(polygons)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polygon_poly_data)
        return mapper

    def _make_double_sided_polygon_mapper(self, point_list):
        if not isinstance(point_list, list) or len(point_list) < 3:
            return None

        points = vtk.vtkPoints()
        for point in point_list:
            points.InsertNextPoint(point)

        num_points = len(point_list)

        poly_front = vtk.vtkPolygon()
        poly_front.GetPointIds().SetNumberOfIds(num_points)
        for idx in range(num_points):
            poly_front.GetPointIds().SetId(idx, idx)

        front_polys = vtk.vtkCellArray()
        front_polys.InsertNextCell(poly_front)

        front_poly_data = vtk.vtkPolyData()
        front_poly_data.SetPoints(points)
        front_poly_data.SetPolys(front_polys)

        triangle_filter = vtk.vtkTriangleFilter()
        triangle_filter.SetInputData(front_poly_data)
        triangle_filter.PassLinesOff()
        triangle_filter.PassVertsOff()
        triangle_filter.Update()

        triangulated = triangle_filter.GetOutput()
        tri_points = triangulated.GetPoints()
        tri_cells = triangulated.GetPolys()

        if tri_points is None or tri_cells is None:
            return None

        polygons = vtk.vtkCellArray()
        ids = vtk.vtkIdList()
        tri_cells.InitTraversal()
        while tri_cells.GetNextCell(ids):
            if ids.GetNumberOfIds() != 3:
                continue

            i0 = ids.GetId(0)
            i1 = ids.GetId(1)
            i2 = ids.GetId(2)

            tri_front = vtk.vtkTriangle()
            tri_front.GetPointIds().SetId(0, i0)
            tri_front.GetPointIds().SetId(1, i1)
            tri_front.GetPointIds().SetId(2, i2)

            tri_back = vtk.vtkTriangle()
            tri_back.GetPointIds().SetId(0, i2)
            tri_back.GetPointIds().SetId(1, i1)
            tri_back.GetPointIds().SetId(2, i0)

            polygons.InsertNextCell(tri_front)
            polygons.InsertNextCell(tri_back)

        if polygons.GetNumberOfCells() <= 0:
            return None

        polygon_poly_data = vtk.vtkPolyData()
        polygon_poly_data.SetPoints(tri_points)
        polygon_poly_data.SetPolys(polygons)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polygon_poly_data)
        return mapper

    def _ensure_ccw_xz_world_points(self, point_list):
        if not isinstance(point_list, list) or len(point_list) < 3:
            return point_list

        area2 = 0.0
        point_count = len(point_list)
        for idx in range(point_count):
            x1, _, z1 = point_list[idx]
            x2, _, z2 = point_list[(idx + 1) % point_count]
            area2 += (x1 * z2) - (x2 * z1)

        if area2 < 0.0:
            return list(reversed(point_list))

        return point_list

    def _resolve_profile_anchor_xz(
        self,
        profile_points_xz,
        orientation,
        local_rotation_deg=0.0,
        nose_radius=0.0,
        force_global_tangent_z=False,
    ):
        if not isinstance(profile_points_xz, list) or not profile_points_xz:
            return (0.0, 0.0)

        parsed_points = []
        for point in profile_points_xz:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            point_x = _parse_number(point[0], None)
            point_z = _parse_number(point[1], None)
            if point_x is None or point_z is None:
                continue
            parsed_points.append((float(point_x), float(point_z)))

        if not parsed_points:
            return (0.0, 0.0)

        rotation_rad = radians(float(local_rotation_deg or 0.0))
        cos_rot = cos(rotation_rad)
        sin_rot = sin(rotation_rad)

        rotated_points = []
        for point_x, point_z in parsed_points:
            rotated_x = (point_x * cos_rot) - (point_z * sin_rot)
            rotated_z = (point_x * sin_rot) + (point_z * cos_rot)
            rotated_points.append((rotated_x, rotated_z))

        if orientation in (1, 2):
            tangent_x = min(point[0] for point in rotated_points)
        else:
            tangent_x = max(point[0] for point in rotated_points)

        x_span = max(point[0] for point in rotated_points) - min(point[0] for point in rotated_points)
        x_tolerance = max(1e-6, x_span * 1e-3)
        front_cluster = [point for point in rotated_points if abs(point[0] - tangent_x) <= x_tolerance]
        if not front_cluster:
            front_cluster = rotated_points

        if bool(force_global_tangent_z):
            tangent_z = max(point[1] for point in rotated_points)
        elif orientation in (1, 4):
            tangent_z = max(point[1] for point in front_cluster)
        else:
            tangent_z = min(point[1] for point in front_cluster)

        radius = max(0.0, float(nose_radius or 0.0))
        if radius > 1e-9:
            x_offset = -radius if orientation in (1, 2) else radius
            z_offset = radius if orientation in (1, 4) else -radius

            # Dynamic control point: recover nose-center in rotated space and keep
            # tangent intersection exactly radius away on both X and Z axes.
            center_rot_x = tangent_x - x_offset
            center_rot_z = tangent_z - z_offset
            tangent_x = center_rot_x + x_offset
            tangent_z = center_rot_z + z_offset

        # Anchor at the orientation-selected tangent intersection in rotated space,
        # then convert back to unrotated local coordinates.
        anchor_local_x = (tangent_x * cos_rot) + (tangent_z * sin_rot)
        anchor_local_z = (-tangent_x * sin_rot) + (tangent_z * cos_rot)
        return (float(anchor_local_x), float(anchor_local_z))

    def _resolve_profile_control_point_xz(self, profile_doc):
        if not isinstance(profile_doc, dict):
            return None

        explicit_control = profile_doc.get('control_point_xz')
        if isinstance(explicit_control, (list, tuple)) and len(explicit_control) >= 2:
            point_x = _parse_number(explicit_control[0], None)
            point_z = _parse_number(explicit_control[1], None)
            if point_x is not None and point_z is not None:
                return (float(point_x), float(point_z))

        profile_dims = profile_doc.get('dimensions')
        if isinstance(profile_dims, dict):
            point_x = _parse_number(profile_dims.get('control_point_x'), None)
            point_z = _parse_number(profile_dims.get('control_point_z'), None)
            if point_x is not None and point_z is not None:
                return (float(point_x), float(point_z))

        return None

    def _profile_points_to_world(
        self,
        profile_points_xz,
        base_x,
        base_z,
        orientation,
        local_rotation_deg=0.0,
        anchor_x=0.0,
        anchor_z=0.0,
    ):
        if orientation in (1, 2):
            x_sign = 1.0
        else:
            x_sign = -1.0

        if orientation in (1, 4):
            z_sign = -1.0
        else:
            z_sign = 1.0

        rotation_rad = radians(float(local_rotation_deg or 0.0))
        cos_rot = cos(rotation_rad)
        sin_rot = sin(rotation_rad)
        rotate_local = abs(rotation_rad) > 1e-12

        world_points = []
        for point in profile_points_xz:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue

            local_x = _parse_number(point[0], None)
            local_z = _parse_number(point[1], None)
            if local_x is None or local_z is None:
                continue

            local_x = float(local_x) - float(anchor_x)
            local_z = float(local_z) - float(anchor_z)

            if rotate_local:
                rotated_x = (local_x * cos_rot) - (local_z * sin_rot)
                rotated_z = (local_x * sin_rot) + (local_z * cos_rot)
            else:
                rotated_x = local_x
                rotated_z = local_z

            world_x = self._lathe_special_x(base_x + (x_sign * rotated_x))
            world_z = base_z + (z_sign * rotated_z)
            world_points.append((world_x, 0.0, world_z))

        return world_points

    def _enforce_world_axis_tangency(self, world_points, orientation, base_x, base_z, enforce_x_axis, enforce_z_axis):
        if not isinstance(world_points, list) or not world_points:
            return []

        adjusted = [
            (float(point[0]), float(point[1]), float(point[2]))
            for point in world_points
            if isinstance(point, (list, tuple)) and len(point) >= 3
        ]
        if not adjusted:
            return []

        if enforce_x_axis:
            if orientation in (1, 4):
                z_shift = float(base_z) - max(point[2] for point in adjusted)
            else:
                z_shift = float(base_z) - min(point[2] for point in adjusted)
            if abs(z_shift) > 1e-12:
                adjusted = [(point_x, point_y, point_z + z_shift) for point_x, point_y, point_z in adjusted]

        if enforce_z_axis:
            if orientation in (1, 2):
                x_shift = float(base_x) - min(point[0] for point in adjusted)
            else:
                x_shift = float(base_x) - max(point[0] for point in adjusted)
            if abs(x_shift) > 1e-12:
                adjusted = [(point_x + x_shift, point_y, point_z) for point_x, point_y, point_z in adjusted]

        return adjusted

    def _build_insert_polygon_from_profile(
        self,
        profile_doc,
        base_x,
        base_z,
        orientation,
        local_rotation_deg=0.0,
        enforce_x_axis_tangency=False,
        enforce_z_axis_tangency=False,
    ):
        profile_points = profile_doc.get('insert_polygon_xz')
        if not isinstance(profile_points, list):
            return None

        control_point = self._resolve_profile_control_point_xz(profile_doc)
        profile_family = str(profile_doc.get('family') or '').strip().lower()
        if control_point is not None:
            anchor_x, anchor_z = control_point
        elif profile_family in ('drill', 'tap'):
            # Drill/tap profiles are generated centered on the spindle
            # centerline (X=0) with the cutting tip at Z=0, so the tip-edge
            # tangent anchor used for turning inserts (which picks the
            # min/max X point - the OD edge, not the centerline) does not
            # apply here; anchoring at the origin keeps the bore on-center.
            anchor_x, anchor_z = 0.0, 0.0
        else:
            profile_dims = profile_doc.get('dimensions')
            if not isinstance(profile_dims, dict):
                profile_dims = {}

            nose_radius = _parse_number(profile_dims.get('nose_radius'), 0.0)
            if nose_radius is None or nose_radius <= 0.0:
                nose_radius = _parse_number(profile_dims.get('tip_radius'), 0.0)
            if nose_radius is None:
                nose_radius = 0.0

            # Q3 boring-bar C inserts should anchor from the global top tangent
            # corner so the control-surface tangent sits at the axis origin.
            orientation_int = _coerce_int(orientation, None)
            use_global_tangent_z = (profile_family == 'c' and orientation_int == 3)

            anchor_x, anchor_z = self._resolve_profile_anchor_xz(
                profile_points,
                orientation,
                local_rotation_deg=0.0,
                nose_radius=float(nose_radius),
                force_global_tangent_z=use_global_tangent_z,
            )

        world_points = self._profile_points_to_world(
            profile_points,
            base_x,
            base_z,
            orientation,
            local_rotation_deg=local_rotation_deg,
            anchor_x=anchor_x,
            anchor_z=anchor_z,
        )

        world_points = self._enforce_world_axis_tangency(
            world_points,
            orientation,
            base_x,
            base_z,
            enforce_x_axis_tangency,
            enforce_z_axis_tangency,
        )

        if len(world_points) < 3:
            return None

        world_points = self._ensure_ccw_xz_world_points(world_points)

        return self._make_double_sided_polygon_mapper(world_points)

    def _resolve_insert_rotation_deg(self, fusion_tool, holder, expressions):
        def _extract_thsc_letter(raw_style):
            style_text = str(raw_style or '').strip().lower()
            if not style_text:
                return ''
            if style_text == 'custom':
                return ''
            if len(style_text) == 1 and style_text.isalpha():
                return style_text

            boring_match = re.match(r'^boring\s+bar\s+([a-z])$', style_text)
            if boring_match is not None:
                return boring_match.group(1)

            return ''

        tool_type = str(fusion_tool.get('type') if isinstance(fusion_tool, dict) else '').strip().lower()
        style_type = str(_dict_get(fusion_tool, 'geometry', 'SCTY') or '').strip().lower()
        holder_style = str(_dict_get(fusion_tool, 'holder', 'THSC') or '').strip().lower()

        if 'drill' in tool_type or 'tap' in tool_type:
            return 0.0

        if (
            'groov' in tool_type
            or 'thread' in tool_type
            or style_type == 'g'
            or holder_style.startswith('groove')
            or holder_style.startswith('thread')
        ):
            return 0.0

        style_letter = _extract_thsc_letter(holder_style)

        kappa_deg = _ISO_THSC_LETTER_KAPPA_DEG.get(style_letter)
        if kappa_deg is not None:
            return float(kappa_deg) - 90.0

        lead_angle = _parse_number(holder.get('tool_leadingAngle'), None)
        if lead_angle is None:
            lead_angle = _parse_number(expressions.get('tool_leadingAngle'), None)
        if lead_angle is not None:
            return -float(lead_angle)

        tool_front_angle = _resolve_tool_angle_field(self.tool, 'front')
        if tool_front_angle is not None and 0.0 <= float(tool_front_angle) <= 180.0:
            return float(tool_front_angle) - 90.0

        fusion_front_angle = _parse_number(
            fusion_tool.get('linuxcnc_i') if isinstance(fusion_tool, dict) else None,
            None,
        )
        if fusion_front_angle is None:
            fusion_front_angle = _parse_number(_dict_get(fusion_tool, 'post-process', 'linuxcnc_i'), None)
        if fusion_front_angle is None:
            fusion_front_angle = _parse_number(_dict_get(fusion_tool, 'post-process', 'linuxcnc-i'), None)
        if fusion_front_angle is None:
            fusion_front_angle = _parse_number(_dict_get(fusion_tool, 'expressions', 'linuxcnc_i'), None)
        if fusion_front_angle is not None and 0.0 <= float(fusion_front_angle) <= 180.0:
            return float(fusion_front_angle) - 90.0

        return 0.0

    def _resolve_profile_orientation(self, raw_orientation, fusion_tool, profile_doc):
        orientation = _coerce_int(raw_orientation, 0)

        if not isinstance(fusion_tool, dict):
            fusion_tool = {}
        if not isinstance(profile_doc, dict):
            profile_doc = {}

        tool_type = str(fusion_tool.get('type') or profile_doc.get('type') or '').strip().lower()
        description = str(fusion_tool.get('description') or profile_doc.get('description') or '').strip().lower()
        holder_style = str(_dict_get(fusion_tool, 'holder', 'THSC') or '').strip().lower()
        is_thread = ('thread' in tool_type) or (str(profile_doc.get('family') or '').strip().lower() == 'thread')
        is_internal = 'internal' in description
        is_external = 'external' in description

        hand = ''
        if ' lh' in description or '-lh' in description:
            hand = 'L'
        elif ' rh' in description or '-rh' in description:
            hand = 'R'

        if not hand:
            setup_hand_raw = _dict_get(fusion_tool, 'setup', 'HAND')
            setup_hand_text = str(setup_hand_raw or '').strip().lower()
            if setup_hand_raw is True or setup_hand_text in ('true', '1', 'yes', 'on'):
                hand = 'R'
            elif setup_hand_raw is False or setup_hand_text in ('false', '0', 'no', 'off'):
                hand = 'L'

        if not hand:
            holder_hand = str(_dict_get(fusion_tool, 'holder', 'HAND') or '').strip().upper()
            if holder_hand in ('L', 'R'):
                hand = holder_hand

        is_boring_style = 'boring bar' in holder_style
        if is_boring_style:
            return 3

        if orientation in (1, 2, 3, 4):
            return orientation

        # Thread tools in extended LinuxCNC Q modes need semantic orientation.
        # Use the same side/hand convention as LinuxCNC Q mapping.
        if is_thread:
            side_key = None
            if is_internal and not is_external:
                side_key = 'internal'
            elif is_external and not is_internal:
                side_key = 'external'

            q_from_semantics = {
                ('external', 'R'): 2,
                ('external', 'L'): 1,
                ('internal', 'R'): 3,
                ('internal', 'L'): 4,
            }
            if side_key is not None and hand in ('L', 'R'):
                return q_from_semantics[(side_key, hand)]

            if side_key == 'external':
                return 2
            if side_key == 'internal':
                return 3

        extended_orientation_map = {
            5: 1,
            6: 2,
            7: 3,
            8: 4,
        }
        if orientation in extended_orientation_map:
            return extended_orientation_map[orientation]

        return 1

    def _first_positive_number(self, *raw_values):
        for raw_value in raw_values:
            parsed = _parse_number(raw_value, None)
            if parsed is not None and parsed > 0.0:
                return float(parsed)
        return 0.0

    def _make_fusion_lathe_silhouette_mapper(self, fusion_tool, default_tip_edge, default_tip_length, default_profile_length):
        orientation = _coerce_int(_resolve_tool_orientation_field(self.tool), 0)

        # Keep active tool-table orientation authoritative when present.
        # This preserves user table edits (e.g. Q2/Q3 thread orientation)
        # and avoids stale Fusion metadata overriding runtime behavior.
        if orientation < 1 or orientation > 9:
            fusion_orientation_candidates = [
                fusion_tool.get('linuxcnc_q') if isinstance(fusion_tool, dict) else None,
                _dict_get(fusion_tool, 'post-process', 'linuxcnc_q'),
                _dict_get(fusion_tool, 'post-process', 'linuxcnc-q'),
                _dict_get(fusion_tool, 'expressions', 'linuxcnc_q'),
                _dict_get(fusion_tool, 'expressions', 'tool_q'),
                _dict_get(fusion_tool, 'expressions', 'tool_orientation_q'),
            ]
            for candidate in fusion_orientation_candidates:
                candidate_num = _parse_number(candidate, None)
                if candidate_num is None:
                    continue
                candidate_q = int(candidate_num)
                if 1 <= candidate_q <= 9:
                    orientation = candidate_q
                    break

        tool_number = _resolve_active_tool_number(self.tool, self._datasource)
        if tool_number > 0:
            profile_doc = compute_live_insert_profile(fusion_tool)
        else:
            profile_doc = None

        if profile_doc is not None:
            orientation = self._resolve_profile_orientation(orientation, fusion_tool, profile_doc)

        if orientation not in (1, 2, 3, 4):
            return None

        geometry = _dict_get(fusion_tool, 'geometry')
        holder = _dict_get(fusion_tool, 'holder')
        expressions = _dict_get(fusion_tool, 'expressions')

        if not isinstance(geometry, dict):
            geometry = {}
        if not isinstance(holder, dict):
            holder = {}
        if not isinstance(expressions, dict):
            expressions = {}

        tool_type = str(fusion_tool.get('type') or '').strip().lower()
        style_type = str(geometry.get('SCTY') or '').strip().lower()

        insert_size = self._first_positive_number(
            geometry.get('tool_insertSize'),
            expressions.get('tool_insertSize'),
            geometry.get('INSD'),
            expressions.get('tool_cuttingWidth'),
            holder.get('CW'),
            default_profile_length,
        )

        is_groove = ('groove' in tool_type) or (style_type == 'g')
        is_thread = 'thread' in tool_type
        is_drill = ('drill' in tool_type) or ('tap' in tool_type)

        if is_groove:
            holder_style = str(holder.get('THSC') or '').strip().lower()
            description = str(fusion_tool.get('description') or '').strip().lower()
            is_internal_groove = (
                ('internal' in holder_style)
                or ('internal' in description and 'external' not in description)
            )

            internal_groove_max_depth = None
            if is_internal_groove:
                holder_cw = _parse_number(holder.get('CW'), None)
                holder_w = _parse_number(holder.get('W'), None)
                if holder_cw is not None and holder_w is not None:
                    internal_groove_max_depth = float(holder_cw) - (0.5 * float(holder_w))

            insert_width = self._first_positive_number(
                geometry.get('tool_grooveWidth'),
                expressions.get('tool_grooveWidth'),
                geometry.get('tool_insertWidth'),
                expressions.get('tool_insertWidth'),
                insert_size,
                default_tip_edge,
            )

            insert_length = self._first_positive_number(
                internal_groove_max_depth,
                geometry.get('H'),
                holder.get('H'),
                expressions.get('tool_maxDOC'),
                expressions.get('tool_maxDepthOfCut'),
                geometry.get('S'),
                geometry.get('INSD'),
                geometry.get('tool_insertSize'),
                expressions.get('tool_insertSize'),
                expressions.get('tool_cuttingWidth'),
                holder.get('CW'),
                holder.get('LH'),
                default_profile_length,
                default_tip_length,
            )
        elif is_thread:
            insert_length = self._first_positive_number(
                geometry.get('OAL'),
                expressions.get('tool_overallLength'),
                geometry.get('INSD'),
                geometry.get('tool_insertSize'),
                expressions.get('tool_insertSize'),
                geometry.get('S'),
                expressions.get('tool_thickness'),
                default_profile_length,
                default_tip_length,
            )

            thread_thickness = self._first_positive_number(
                geometry.get('S'),
                expressions.get('tool_thickness'),
                0.0,
            )

            template_width = max(
                0.56 * float(insert_length),
                2.00 * float(thread_thickness),
                0.0,
            )

            insert_width = self._first_positive_number(
                geometry.get('thread-body-width'),
                expressions.get('thread-body-width'),
                template_width,
                geometry.get('S'),
                expressions.get('tool_thickness'),
                geometry.get('tool_insertWidth'),
                expressions.get('tool_insertWidth'),
                geometry.get('INSD'),
                geometry.get('tool_insertSize'),
                expressions.get('tool_insertSize'),
                default_tip_edge,
            )
        else:
            insert_width = self._first_positive_number(
                geometry.get('tool_insertWidth'),
                expressions.get('tool_insertWidth'),
                geometry.get('tool_insertSize'),
                expressions.get('tool_insertSize'),
                geometry.get('INSD'),
                expressions.get('tool_cuttingWidth'),
                insert_size,
                default_tip_edge,
            )

        nose_radius = self._first_positive_number(
            geometry.get('RE'),
            geometry.get('thread-tip-radius'),
            expressions.get('tool_cornerRadius'),
            0.0,
        )
        if nose_radius > 0.0:
            insert_width = max(insert_width, 2.0 * nose_radius)

        if not is_groove and not is_thread:
            insert_length = self._first_positive_number(
                geometry.get('INSD'),
                geometry.get('tool_insertSize'),
                expressions.get('tool_insertSize'),
                expressions.get('tool_cuttingWidth'),
                holder.get('CW'),
                holder.get('LH'),
                default_profile_length,
                default_tip_length,
            )

        insert_rotation_deg = self._resolve_insert_rotation_deg(
            fusion_tool,
            holder,
            expressions,
        )

        base_x = float(-_resolve_tool_axis_offset(self.tool, 'x'))
        base_z = float(-_resolve_tool_axis_offset(self.tool, 'z'))

        if orientation in (1, 2):
            x_sign = 1.0
        else:
            x_sign = -1.0

        if orientation in (1, 4):
            z_sign = -1.0
        else:
            z_sign = 1.0

        if is_drill:
            half_width = 0.5 * float(insert_width)
            insert_quad_local = [
                (-half_width, 0.0),
                (-half_width, -float(insert_length)),
                (half_width, -float(insert_length)),
                (half_width, 0.0),
            ]
        else:
            insert_quad_local = [
                (0.0, 0.0),
                (insert_length, 0.0),
                (insert_length, insert_width),
                (0.0, insert_width),
            ]

        if profile_doc is not None:
            profile_local_rotation_deg = float(insert_rotation_deg)
            profile_format = _coerce_int(profile_doc.get('profile_format'), 0)
            profile_family = str(profile_doc.get('family') or '').strip().lower()
            holder_hand = str(_dict_get(fusion_tool, 'holder', 'HAND') or '').strip().upper()
            neutral_hand_tool = bool(is_drill) or holder_hand == 'N'

            enforce_x_axis_tangency = False
            enforce_z_axis_tangency = False

            if profile_format >= 1:
                if profile_family == 'thread':
                    enforce_x_axis_tangency = True
                    enforce_z_axis_tangency = True
                elif profile_family not in ('drill', 'tap'):
                    enforce_z_axis_tangency = True
                    if not neutral_hand_tool:
                        enforce_x_axis_tangency = True

            # Canonical generated thread/drill/tap profiles are already oriented
            # in the same local frame as the preview SVG. Avoid extra runtime
            # rotation so backplot matches preview geometry directly.
            if profile_format >= 1 and profile_family in ('thread', 'drill', 'tap'):
                profile_local_rotation_deg = 0.0

            insert_mapper = self._build_insert_polygon_from_profile(
                profile_doc,
                base_x,
                base_z,
                orientation,
                local_rotation_deg=profile_local_rotation_deg,
                enforce_x_axis_tangency=enforce_x_axis_tangency,
                enforce_z_axis_tangency=enforce_z_axis_tangency,
            )
            if insert_mapper is not None:
                return insert_mapper

        fallback_points = self._profile_points_to_world(
            insert_quad_local,
            base_x,
            base_z,
            orientation,
            local_rotation_deg=insert_rotation_deg,
        )
        if len(fallback_points) < 3:
            return None
        return self._make_double_sided_polygon_mapper(fallback_points)

    def set_position_cnc(self, position):
        
        
        # self.source.SetCenter(self.tool.xoffset, self.tool.yoffset, -self.tool.zoffset/2)

        
        target_position = (
            float(position[0]),
            float(position[1]),
            float(position[2]),
        )
        target_rotation = (
            float(position[3]),
            float(position[4]),
            float(position[5]),
        )

        if self._smoothed_cnc_rotation is None or self._cnc_motion_alpha >= 1.0:
            self._smoothed_cnc_rotation = target_rotation
        else:
            alpha = self._cnc_motion_alpha
            prev_rot = self._smoothed_cnc_rotation

            def smooth_angle(prev_deg, target_deg):
                delta = ((target_deg - prev_deg + 180.0) % 360.0) - 180.0
                return prev_deg + (alpha * delta)

            self._smoothed_cnc_rotation = (
                smooth_angle(prev_rot[0], target_rotation[0]),
                smooth_angle(prev_rot[1], target_rotation[1]),
                smooth_angle(prev_rot[2], target_rotation[2]),
            )

        smoothed_rot = self._smoothed_cnc_rotation

        transform = vtk.vtkTransform()

        transform.Translate(target_position[0], target_position[1], (target_position[2] - self.tool.zoffset))

        transform.RotateX(smoothed_rot[0])
        transform.RotateY(smoothed_rot[2])
        transform.RotateZ(smoothed_rot[1])

        transform.Translate(-target_position[0], -target_position[1], -(target_position[2] - self.tool.zoffset))

        self.SetUserTransform(transform)
        
        self.SetPosition(target_position[0], target_position[1], target_position[2])
        
        
    def set_position(self, position):
        self.tool_position = position

        x, y, z = position[:3]
        u, v, w = position[6:9]

        self.source.SetPoint1(x, y ,z+self.foam_z)
        self.source.SetPoint2(u, v, w+self.foam_w)




