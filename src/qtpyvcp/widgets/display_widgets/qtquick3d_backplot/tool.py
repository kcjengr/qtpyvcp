"""Tool geometry sizing for the Qt Quick 3D backplot.

Renderer-independent: turns the active LinuxCNC/QtPyVCP tool table entry into a
:class:`ToolShape` (a cylinder sized by the tool diameter and Z offset, or a
cone marker when no tool is loaded).
"""

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

    ``kind`` is ``"cylinder"``, ``"cone"`` or ``"none"``. ``length`` is the
    body length along +Z (toward the spindle) from the tool tip, ``radius`` its
    radius, and ``x_offset`` a lateral offset (lathe radial offset).
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
    """Translation from the tool tip to the mesh centre (tip at the origin)."""
    return (shape.x_offset, 0.0, shape.length / 2.0)
