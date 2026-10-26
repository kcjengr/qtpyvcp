"""Tool geometry for the Qt Quick 3D backplot.

Renderer-independent: turns the active LinuxCNC/QtPyVCP tool table entry into a
:class:`ToolShape` (a cylinder sized by the tool diameter and Z offset, or a
cone marker when no tool is loaded), and derives lathe insert silhouettes and
per-tool model paths from the tool database.
"""

import math
import os
import re
from dataclasses import dataclass

from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

# Default tool height: 2 inches, or 50.8 mm on a metric machine.
DEFAULT_HEIGHT_INCH = 2.0


def _get(entry, name, default=None):
    if entry is None:
        return default
    if isinstance(entry, dict):
        return entry.get(name, default)
    return getattr(entry, name, default)


def _as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default=-1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _entry_tool_number(entry):
    """Return an entry's tool number from LinuxCNC or QtPyVCP field names."""
    for name in ('tool', 'toolno', 'tool_no', 'number', 'id'):
        number = _as_int(_get(entry, name, None), None)
        if number is not None:
            return number
    return None


def _entry_axis_offset(entry, axis):
    """Read a tool offset from LinuxCNC or QtPyVCP field names.

    QtPyVCP's DB rows use ``xoffset``/``zoffset``; LinuxCNC's
    ``stat.tool_table`` stores them in the entry's ``offset`` (an
    ``EmcPose`` with ``x``/``y``/``z`` attributes or a 9-tuple).
    """
    if entry is None:
        return 0.0

    explicit = _get(entry, axis + 'offset', None)
    if explicit is not None:
        return _as_float(explicit, 0.0)

    offset = _get(entry, 'offset', None)
    if offset is None:
        return 0.0

    value = _get(offset, axis, None)
    if value is not None:
        return _as_float(value, 0.0)

    try:
        return _as_float(offset['xyz'.index(axis)], 0.0)
    except (TypeError, KeyError, IndexError, ValueError):
        return 0.0


def resolve_tool_entry(tool_table, tool_number):
    """Find the tool-table entry for *tool_number*.

    Handles the pocket-indexed ``stat.tool_table`` list (LinuxCNC exposes the
    tool number as ``toolno``) and the tool-number-keyed dict returned by the
    DB tool table plugin.
    """
    if not tool_table:
        return None

    if isinstance(tool_table, dict):
        if tool_number in tool_table:
            return tool_table[tool_number]
        if str(tool_number) in tool_table:
            return tool_table[str(tool_number)]
        if 0 in tool_table:
            return tool_table[0]
        values = list(tool_table.values())
        return values[0] if values else None

    for entry in tool_table:
        if _entry_tool_number(entry) == tool_number:
            return entry

    # Legacy lists without a tool-number field are pocket indexed.
    if 0 <= tool_number < len(tool_table):
        entry = tool_table[tool_number]
        if _entry_tool_number(entry) is None:
            return entry
    return None


@dataclass
class ToolShape:
    """A renderable primitive for the active tool.

    ``kind`` is ``"cylinder"``, ``"cone"``, ``"insert"``, ``"mesh"`` or
    ``"none"``. ``length`` is the body length along +Z (toward the spindle)
    from the tool tip, ``radius`` its radius, and ``x_offset`` a lateral offset
    (lathe radial offset). Insert/mesh shapes are authored in tip coordinates,
    so they have no body-centre offset.
    """

    kind: str = "none"
    radius: float = 0.0
    length: float = 0.0
    x_offset: float = 0.0
    tool_number: int = -1

    @property
    def visible(self):
        return self.kind != "none" and self.length > 0.0 and self.radius > 0.0


def tool_shape(tool_table, tool_number, *, metric, lathe=False,
               robot=False, foam=False, jet=False) -> ToolShape:
    """Return the :class:`ToolShape` for the active tool."""
    if robot or foam or jet:
        # These machines draw their own tool representation; no generic body.
        return ToolShape(kind="none", tool_number=_as_int(tool_number, -1))

    default_height = DEFAULT_HEIGHT_INCH * (25.4 if metric else 1.0)
    unit_scale = 25.4 if metric else 1.0

    entry = resolve_tool_entry(tool_table, _as_int(tool_number, -1))
    tool_id = _entry_tool_number(entry) or 0
    diameter = _as_float(_get(entry, 'diameter', 0.0), 0.0)
    z_offset = abs(_entry_axis_offset(entry, 'z'))
    x_offset = _entry_axis_offset(entry, 'x')

    if lathe:
        radius = (diameter / 2.0) if diameter > 0.05 else (0.035 * unit_scale)
        length = z_offset if z_offset > 0.0 else default_height
        return ToolShape(kind="cylinder", radius=radius, length=length,
                         x_offset=x_offset, tool_number=tool_id)

    if tool_id <= 0 or diameter < 0.05:
        # No tool loaded: a pointed cone marker.
        return ToolShape(kind="cone", radius=default_height / 4.0,
                         length=default_height / 2.0, tool_number=tool_id)

    length = z_offset if z_offset > 0.0 else default_height
    return ToolShape(kind="cylinder", radius=diameter / 2.0, length=length,
                     x_offset=x_offset, tool_number=tool_id)


def tool_body_offset(shape: ToolShape):
    """Translation from the tool tip to the model origin.

    ``#Cone`` is authored with its origin at the base and is rotated 180° in
    QML, so its tip sits ``length`` below the model origin.  Moving the origin
    up by the full length puts the tip at the tool position instead of
    centring the cone on it.  ``#Cylinder`` is centred and only needs half its
    length; insert/mesh shapes are already authored in tip coordinates.
    """
    if shape.kind in ("insert", "mesh"):
        return (0.0, 0.0, 0.0)
    if shape.kind == "cone":
        return (shape.x_offset, 0.0, shape.length)
    return (shape.x_offset, 0.0, shape.length / 2.0)


# -- lathe insert silhouette ------------------------------------------------
#
# The tool bit on a lathe is an insert, not a cylinder.  The tool database is
# the single source of truth for its shape, so the backplot derives a 2D
# polygon in the machine XZ plane from the same ``compute_insert_profile()``
# document the tool-table editor uses.  The polygon is flat (the old VTK
# renderer drew a flat, double-sided silhouette as well); Quick 3D extrudes
# nothing and simply lights both faces.

_ISO_THSC_LETTER_KAPPA_DEG = {
    'a': 90.0, 'b': 75.0, 'c': 90.0, 'd': 45.0, 'e': 60.0, 'f': 90.0,
    'g': 90.0, 'h': 107.5, 'j': 93.0, 'k': 75.0, 'l': 95.0, 'm': 86.0,
    'n': 62.5, 'p': 117.5, 'q': 107.5, 'r': 45.0, 's': 45.0, 'v': 72.5,
}


def _first_positive(*values):
    for value in values:
        parsed = _as_float(value, 0.0)
        if parsed > 0.0:
            return parsed
    return 0.0


def _tool_field(entry, *names, default=None):
    for name in names:
        value = _get(entry, name, None)
        if value is not None:
            return value
    return default


def resolve_insert_record(datasource, tool_number, tool_entry=None):
    """Return a DB insert record for *tool_number*, or ``None``.

    Uses the running ``tooltable`` plugin when available (the same source the
    old VTK renderer used) and falls back to insert columns carried by the
    tool-table entry itself, which keeps the widget usable in tests and with
    classic ``.tbl`` files.
    """
    tool_number = _as_int(tool_number, -1)
    if tool_number <= 0:
        return None
    try:
        from qtpyvcp.lib.db_tool.insert_profile import insert_record
    except ImportError:  # pragma: no cover - optional GUI/database dependency
        return None

    plugin = getattr(datasource, "_tooltable", None)
    core = None
    extras = None
    if (plugin is not None and hasattr(plugin, "getToolTable")
            and hasattr(plugin, "getToolExtras")):
        try:
            table = plugin.getToolTable() or {}
            core = table.get(tool_number) if isinstance(table, dict) else None
            if core is not None:
                extras = plugin.getToolExtras(tool_number)
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
            LOG.debug("tool DB insert lookup failed for T%s", tool_number,
                      exc_info=True)
            core = extras = None

    has_entry_insert_fields = tool_entry is not None and any(
        _get(tool_entry, key, None) not in (None, "")
        for key in ('type', 'tool_type', 'insert_shape', 'shape',
                    'insert_size', 'holder_style'))
    if core is None and has_entry_insert_fields:
        # Fall back to a flattened record from the entry.  Entries that do not
        # carry insert columns are classic .tbl rows: leave them to the generic
        # cylinder rather than inventing a C-shaped insert.
        core = {
            'T': tool_number,
            'D': _get(tool_entry, 'diameter', 0.0),
        }
        extras = {
            key: _get(tool_entry, key, None)
            for key in (
                'type', 'insert_shape', 'insert_size_mode', 'insert_size',
                'insert_thickness', 'groove_width', 'max_depth_of_cut',
                'drill_point_angle', 'flute_length', 'overall_length',
                'shaft_diameter', 'chamfer_threads', 'thread_pitch_max',
                'thread_pitch_min', 'thread_angle', 'thread_tip_type',
                'holder_style', 'holder_hand', 'holder_shank_width',
                'holder_cut_width', 'holder_oal',
            )
            if _get(tool_entry, key, None) is not None
        }
        extras['type'] = _tool_field(tool_entry, 'type', 'tool_type',
                                     default='')
        extras['insert_shape'] = _tool_field(
            tool_entry, 'insert_shape', 'shape', default='')
    if core is None:
        return None
    try:
        record = insert_record(core, extras)
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
        LOG.debug("could not build insert record for T%s", tool_number,
                  exc_info=True)
        return None
    if record.get('tool_no') != tool_number:
        # The plugin may have returned a different row; keep the record only
        # when it belongs to the requested tool.
        return None if record.get('tool_no', tool_number) != tool_number else record
    return record


def resolve_tool_model_path(datasource, tool_entry, tool_number=None):
    """Return an STL/glTF path for a per-tool model, or ``None``.

    Per-tool models are optional: a tool-table row (or its DB extras) may
    carry ``model``/``stl``/``mesh``/``file``.  The legacy ``tool_model`` table
    is a dead stub in the DB schema, so entries are the supported source.
    """
    raw = _tool_field(tool_entry, 'model', 'stl', 'mesh', 'file', 'model_path')
    plugin = getattr(datasource, "_tooltable", None)
    if raw is None and plugin is not None and hasattr(plugin, "getToolExtras"):
        try:
            extras = plugin.getToolExtras(_as_int(tool_number, -1)) or {}
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
            extras = {}
        if isinstance(extras, dict):
            raw = _tool_field(extras, 'model', 'stl', 'mesh', 'file',
                              'model_path')
    if not raw:
        return None
    path = str(raw)
    if not os.path.isabs(path):
        base = getattr(datasource, "config_dir", None)
        if not base:
            return None
        path = os.path.normpath(os.path.join(base, path))
    return path if os.path.isfile(path) else None


def _resolve_profile_orientation(raw_orientation, record, profile_doc):
    orientation = _as_int(raw_orientation, 0)
    if not isinstance(profile_doc, dict):
        profile_doc = {}
    try:
        from qtpyvcp.lib.db_tool.insert_profile import holder_style_code
    except ImportError:  # pragma: no cover
        holder_style_code = lambda rec: str(rec.get('holder_style') or '').lower()

    remark = str(record.get('remark') or '').lower()
    style_code = holder_style_code(record)
    is_thread = (record.get('type') == 'threading'
                 or str(profile_doc.get('family') or '').strip().lower()
                 == 'thread')
    is_internal = 'internal' in remark
    is_external = 'external' in remark

    hand = ''
    if ' lh' in remark or '-lh' in remark:
        hand = 'L'
    elif ' rh' in remark or '-rh' in remark:
        hand = 'R'
    if not hand and record.get('holder_hand') in ('L', 'R'):
        hand = record['holder_hand']

    if record.get('type') == 'boring' or 'boring bar' in style_code:
        return 3
    if orientation in (1, 2, 3, 4):
        return orientation
    if is_thread:
        side = None
        if is_internal and not is_external:
            side = 'internal'
        elif is_external and not is_internal:
            side = 'external'
        q_map = {('external', 'R'): 2, ('external', 'L'): 1,
                 ('internal', 'R'): 3, ('internal', 'L'): 4}
        if side is not None and hand in ('L', 'R'):
            return q_map[(side, hand)]
        if side == 'external':
            return 2
        if side == 'internal':
            return 3
    return {5: 1, 6: 2, 7: 3, 8: 4}.get(orientation, 1)


def _resolve_insert_rotation_deg(record, tool_entry):
    try:
        from qtpyvcp.lib.db_tool.insert_profile import holder_style_code
    except ImportError:  # pragma: no cover
        holder_style_code = lambda rec: str(rec.get('holder_style') or '').lower()

    style = holder_style_code(record)
    if record.get('is_round_tool'):
        return 0.0
    if (record.get('type') in ('grooving', 'parting', 'threading')
            or style.startswith(('groove', 'thread'))):
        return 0.0
    letter = ''
    if len(style) == 1 and style.isalpha():
        letter = style
    else:
        match = re.match(r'^boring\s+bar\s+([a-z])$', style)
        if match is not None:
            letter = match.group(1)
    kappa = _ISO_THSC_LETTER_KAPPA_DEG.get(letter)
    if kappa is not None:
        return float(kappa) - 90.0
    front = _as_float(_tool_field(tool_entry, 'frontangle', 'i_offset',
                                  'ioffset', 'i', 'I', default=None), None)
    if front is not None and 0.0 <= front <= 180.0:
        return front - 90.0
    return 0.0


def _resolve_anchor_xz(points, orientation, nose_radius,
                       rotation_deg=0.0, force_global_tangent_z=False):
    if not points:
        return (0.0, 0.0)
    rotation = math.radians(float(rotation_deg or 0.0))
    cos_rot, sin_rot = math.cos(rotation), math.sin(rotation)
    rotated = [(x * cos_rot - z * sin_rot, x * sin_rot + z * cos_rot)
               for x, z in points]
    if orientation in (1, 2):
        tangent_x = min(point[0] for point in rotated)
    else:
        tangent_x = max(point[0] for point in rotated)
    span = (max(point[0] for point in rotated)
            - min(point[0] for point in rotated))
    tolerance = max(1e-6, span * 1e-3)
    front = [point for point in rotated
             if abs(point[0] - tangent_x) <= tolerance] or rotated
    if force_global_tangent_z:
        tangent_z = max(point[1] for point in rotated)
    elif orientation in (1, 4):
        tangent_z = max(point[1] for point in front)
    else:
        tangent_z = min(point[1] for point in front)
    # Convert the rotated tangent intersection back to the profile frame; the
    # profile is rotated again when it is placed in world space.
    anchor_x = tangent_x * cos_rot + tangent_z * sin_rot
    anchor_z = -tangent_x * sin_rot + tangent_z * cos_rot
    # Nose radius is already baked into the profile by the shape builder.
    return (anchor_x, anchor_z)


def _profile_to_world(points, orientation, local_rotation_deg, anchor_x,
                      anchor_z):
    if orientation in (1, 2):
        x_sign = 1.0
    else:
        x_sign = -1.0
    z_sign = -1.0 if orientation in (1, 4) else 1.0

    rotation = math.radians(float(local_rotation_deg or 0.0))
    cos_rot, sin_rot = math.cos(rotation), math.sin(rotation)
    rotate = abs(rotation) > 1e-12

    world = []
    for x_val, z_val in points:
        local_x = float(x_val) - float(anchor_x)
        local_z = float(z_val) - float(anchor_z)
        if rotate:
            local_x, local_z = (
                local_x * cos_rot - local_z * sin_rot,
                local_x * sin_rot + local_z * cos_rot,
            )
        world.append((x_sign * local_x, z_sign * local_z))
    return world


def _enforce_tangency(points, orientation, enforce_x, enforce_z):
    if not points:
        return points
    adjusted = list(points)
    if enforce_x:
        if orientation in (1, 4):
            shift = -max(point[1] for point in adjusted)
        else:
            shift = -min(point[1] for point in adjusted)
        if abs(shift) > 1e-12:
            adjusted = [(x, z + shift) for x, z in adjusted]
    if enforce_z:
        if orientation in (1, 2):
            shift = -min(point[0] for point in adjusted)
        else:
            shift = -max(point[0] for point in adjusted)
        if abs(shift) > 1e-12:
            adjusted = [(x + shift, z) for x, z in adjusted]
    return adjusted


def _ensure_ccw(points):
    area2 = 0.0
    for index, (x1, z1) in enumerate(points):
        x2, z2 = points[(index + 1) % len(points)]
        area2 += x1 * z2 - x2 * z1
    return list(points) if area2 >= 0.0 else list(reversed(points))


def insert_polygon(record, tool_entry=None):
    """Return the insert silhouette as CCW ``(x, z)`` points relative to the
    tool tip, or ``None`` when the record cannot produce a polygon."""
    if not isinstance(record, dict):
        return None
    try:
        from qtpyvcp.lib.db_tool.insert_profile import (
            compute_insert_profile,
        )
    except ImportError:  # pragma: no cover - optional GUI/database dependency
        return None
    profile_doc = compute_insert_profile(record)
    if not profile_doc:
        return None
    points = profile_doc.get('insert_polygon_xz')
    if not isinstance(points, list) or len(points) < 3:
        return None
    points = [(float(point[0]), float(point[1])) for point in points]

    orientation = _resolve_profile_orientation(
        _tool_field(tool_entry, 'orientation', 'q_offset', 'qoffset', 'q',
                    'Q', default=0)
        if tool_entry is not None else 0,
        record, profile_doc)
    if orientation not in (1, 2, 3, 4):
        return None

    family = str(profile_doc.get('family') or '').strip().lower()
    dims = profile_doc.get('dimensions') or {}
    nose_radius = _first_positive(dims.get('nose_radius'),
                                  dims.get('tip_radius'))
    rotation = (0.0 if family in ('thread', 'drill', 'tap')
                else _resolve_insert_rotation_deg(record, tool_entry))

    control = profile_doc.get('control_point_xz')
    if isinstance(control, (list, tuple)) and len(control) >= 2:
        anchor_x, anchor_z = float(control[0]), float(control[1])
    elif family in ('drill', 'tap'):
        anchor_x = anchor_z = 0.0
    else:
        anchor_x, anchor_z = _resolve_anchor_xz(
            points, orientation, nose_radius, rotation_deg=rotation,
            force_global_tangent_z=(family == 'c' and orientation == 3))

    world = _profile_to_world(points, orientation, rotation, anchor_x,
                              anchor_z)
    is_round_tool = bool(record.get('is_round_tool'))
    neutral_hand = is_round_tool or record.get('holder_hand') == 'N'
    if family == 'thread':
        enforce_x = enforce_z = True
    elif not is_round_tool and family not in ('drill', 'tap'):
        enforce_x = not neutral_hand
        enforce_z = True
    else:
        enforce_x = enforce_z = False
    world = _enforce_tangency(world, orientation, enforce_x, enforce_z)
    if len(world) < 3:
        return None
    return tuple(_ensure_ccw(world))


def triangulate_polygon(points):
    """Ear-clip a simple 2D polygon into a list of triangle index triples."""
    count = len(points)
    if count < 3:
        return []
    if count == 3:
        return [(0, 1, 2)]

    def cross(ax, az, bx, bz, cx, cz):
        return (bx - ax) * (cz - az) - (bz - az) * (cx - ax)

    def inside(point, a, b, c):
        px, pz = point
        d1 = cross(a[0], a[1], b[0], b[1], px, pz)
        d2 = cross(b[0], b[1], c[0], c[1], px, pz)
        d3 = cross(c[0], c[1], a[0], a[1], px, pz)
        return d1 >= -1e-12 and d2 >= -1e-12 and d3 >= -1e-12

    indices = list(range(count))
    triangles = []
    guard = 0
    while len(indices) > 3 and guard < count * count:
        guard += 1
        ear_found = False
        for position in range(len(indices)):
            previous = indices[position - 1]
            current = indices[position]
            following = indices[(position + 1) % len(indices)]
            a, b, c = points[previous], points[current], points[following]
            if cross(a[0], a[1], b[0], b[1], c[0], c[1]) <= 1e-12:
                continue
            if any(inside(points[index], a, b, c)
                   for index in indices
                   if index not in (previous, current, following)):
                continue
            triangles.append((previous, current, following))
            indices.pop(position)
            ear_found = True
            break
        if not ear_found:
            break

    if len(indices) == 3:
        triangles.append(tuple(indices))
    if not triangles:
        # Degenerate/self-intersecting profile: fan from the centroid.
        center = (sum(p[0] for p in points) / count,
                  sum(p[1] for p in points) / count)
        points = list(points) + [center]
        center_index = len(points) - 1
        triangles = [(index, (index + 1) % count, center_index)
                     for index in range(count)]
    return triangles


def insert_mesh(polygon):
    """Build a double-sided Quick 3D triangle mesh from a tip-relative
    ``(x, z)`` insert polygon.

    CNC ``(x, 0, z)`` maps to Quick 3D ``(x, z, 0)``: the silhouette lies in
    the scene XY plane with its normal along scene Z.  Front and back faces are
    emitted so the insert is visible from either side of the lathe.
    """
    import numpy as np

    points = list(polygon or ())
    if len(points) < 3:
        return None
    triangles = triangulate_polygon(points)
    if not triangles:
        return None

    scene_points = np.asarray(
        [(float(x), float(z), 0.0) for x, z in points], dtype=np.float64)
    front = np.asarray(triangles, dtype=np.int64)
    back = front[:, ::-1]
    faces = np.concatenate((front, back))
    vertices = scene_points[faces.reshape(-1)]
    normals = np.empty_like(vertices)
    normals[:len(front) * 3] = (0.0, 0.0, 1.0)
    normals[len(front) * 3:] = (0.0, 0.0, -1.0)
    return vertices.astype(np.float32), normals.astype(np.float32)
