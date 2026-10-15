"""Tool geometry for the Qt3D backplot, driven by the LinuxCNC tool table.

Mirrors the VTK ``ToolActor``/``ToolBitActor`` sizing so the drawn tool matches
the tool table: a cylinder sized by the tool diameter and Z offset for a loaded
mill tool, or a cone when no tool / a negligible diameter is active.  The VTK
version can additionally show an STL model from the tool database; this module
deliberately stays renderer-light and uses primitives.
"""

from dataclasses import dataclass

from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.QtGui import QColor, QQuaternion, QVector3D

from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

# VTK's default tool height: 2 inches, or 50.8 mm on a metric machine.
DEFAULT_HEIGHT_INCH = 2.0

TOOL_COLOR = QColor(210, 210, 215)
HOLDER_COLOR = QColor(120, 120, 130)


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


def resolve_tool_entry(tool_table, tool_number):
    """Find the tool-table entry for *tool_number*.

    Handles both the pocket-indexed ``stat.tool_table`` list and the
    tool-number-keyed dict returned by the DB tool table plugin.
    """
    if not tool_table:
        return None

    if isinstance(tool_table, dict):
        if tool_number in tool_table:
            return tool_table[tool_number]
        if 0 in tool_table:
            return tool_table[0]
        values = list(tool_table.values())
        return values[0] if values else None

    # Prefer matching by the entry's own tool number.
    for entry in tool_table:
        if _as_int(_get(entry, 'id', _get(entry, 'tool', None)), -1) == tool_number:
            return entry

    if 0 <= tool_number < len(tool_table):
        return tool_table[tool_number]
    return tool_table[0] if tool_table else None


@dataclass
class ToolShape:
    """A renderable primitive for the active tool.

    ``kind`` is ``"cylinder"``, ``"cone"`` or ``"none"``.  ``length`` is the
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
        # These machines draw their own tool representation (robot cylinder,
        # foam/jet nozzle); no generic body is drawn here.
        return ToolShape(kind="none", tool_number=_as_int(tool_number, -1))

    default_height = DEFAULT_HEIGHT_INCH * (25.4 if metric else 1.0)
    unit_scale = 25.4 if metric else 1.0

    entry = resolve_tool_entry(tool_table, _as_int(tool_number, -1))
    tool_id = _as_int(_get(entry, 'id', _get(entry, 'tool', None)), 0)
    diameter = _as_float(_get(entry, 'diameter', 0.0), 0.0)
    z_offset = abs(_as_float(_get(entry, 'zoffset', 0.0), 0.0))
    x_offset = _as_float(_get(entry, 'xoffset', 0.0), 0.0)

    if lathe:
        # Lathe: a stick from the tip along the tool length. Unknown tools get
        # a small default marker radius (matching VTK's 0.035 in polygon).
        radius = (diameter / 2.0) if diameter > 0.05 else (0.035 * unit_scale)
        length = z_offset if z_offset > 0.0 else default_height
        return ToolShape(kind="cylinder", radius=radius, length=length,
                         x_offset=x_offset, tool_number=tool_id)

    # Mill / router.
    if tool_id <= 0 or diameter < 0.05:
        # No tool loaded: a pointed cone, sized like the VTK default.
        return ToolShape(kind="cone", radius=default_height / 4.0,
                         length=default_height / 2.0, tool_number=tool_id)

    length = z_offset if z_offset > 0.0 else default_height
    return ToolShape(kind="cylinder", radius=diameter / 2.0, length=length,
                     x_offset=x_offset, tool_number=tool_id)


def build_tool_entity(parent, shape: ToolShape, name="tool"):
    """Create (or return ``None`` for) a tool body entity for *shape*.

    The mesh is centred on its own origin; the caller positions the entity so
    the tool tip sits at the machine position.  Meshes are aligned to +Z.
    """
    if not shape.visible:
        return None

    if shape.kind == "cone":
        mesh = Qt3DExtras.QConeMesh()
        mesh.setTopRadius(shape.radius)
        mesh.setBottomRadius(0.0)
        mesh.setLength(shape.length)
        mesh.setRings(2)
        mesh.setSlices(48)
    else:
        mesh = Qt3DExtras.QCylinderMesh()
        mesh.setRadius(shape.radius)
        mesh.setLength(shape.length)
        mesh.setRings(2)
        mesh.setSlices(48)

    material = Qt3DExtras.QPhongMaterial()
    material.setDiffuse(TOOL_COLOR)
    material.setSpecular(QColor(255, 255, 255))
    material.setShininess(60.0)

    entity = Qt3DCore.QEntity(parent)
    entity.setObjectName(name)
    transform = Qt3DCore.QTransform()
    # Mesh axis is +Y; rotate to +Z so the body runs toward the spindle.
    transform.setRotation(QQuaternion.fromAxisAndAngle(
        QVector3D(1.0, 0.0, 0.0), 90.0))
    entity.addComponent(mesh)
    entity.addComponent(material)
    entity.addComponent(transform)
    entity._qt3d_refs = (mesh, material, transform)

    entity._tool_transform = transform
    entity._tool_shape = shape
    return entity


def tool_body_offset(shape: ToolShape):
    """Translation from the tool tip to the mesh centre (tip at the origin)."""
    return (shape.x_offset, 0.0, shape.length / 2.0)
