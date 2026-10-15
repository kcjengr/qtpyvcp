"""Qt3D scene primitives for the backplot.

Small factory helpers that build vertices, line/triangle geometry, and the
materials the backplot needs.  Keeping these here keeps the widget focused on
machine state and coordinate logic.
"""

import numpy as np
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QColor

PositionAttribute = Qt3DCore.QAttribute.defaultPositionAttributeName()
ColorAttribute = Qt3DCore.QAttribute.defaultColorAttributeName()
NormalAttribute = Qt3DCore.QAttribute.defaultNormalAttributeName()

def make_buffer(array):
    """Wrap a NumPy array in a Qt3D ``QBuffer`` with a copy of its bytes."""
    buf = Qt3DCore.QBuffer()
    data = np.ascontiguousarray(array)
    # QBuffer copies the QByteArray, so the temporary is safe to release.
    buf.setData(QByteArray(data.tobytes()))
    buf.setObjectName("vertex_buffer")
    return buf


def _add_attribute(geom, name, base_type, size, count, buffer, stride, offset=0):
    attr = Qt3DCore.QAttribute()
    attr.setName(name)
    attr.setVertexBaseType(base_type)
    attr.setVertexSize(size)
    attr.setCount(int(count))
    attr.setBuffer(buffer)
    attr.setByteStride(int(stride))
    attr.setByteOffset(int(offset))
    geom.addAttribute(attr)
    # Keep the Python wrappers alive as well as the C++ parent/child graph.
    # PySide can otherwise collect the QAttribute/QBuffer wrappers after this
    # helper returns; Qt3D then sees a geometry with zero vertex attributes.
    refs = getattr(geom, "_qt3d_refs", [])
    refs.extend((buffer, attr))
    geom._qt3d_refs = refs
    return attr


class DynamicLine:
    """A line entity whose vertex buffer is rewritten in place.

    Rebuilding a Qt3D entity on every position update (as the live trail used
    to) churns Qt3D nodes at 30+ Hz and can crash the render thread. A single
    preallocated buffer that is re-uploaded and re-counted is both safe and
    far cheaper.
    """

    def __init__(self, parent, capacity, color=(0.9, 0.95, 0.3, 1.0), width=2.0,
                 name="dynamic_line"):
        self.capacity = max(int(capacity), 2)
        self.entity = Qt3DCore.QEntity(parent)
        self.entity.setObjectName(name)
        self.entity.setEnabled(False)

        self._positions = np.zeros((self.capacity, 3), dtype=np.float32)
        self._colors = np.tile(np.asarray(color, dtype=np.float32),
                               (self.capacity, 1))

        geometry = Qt3DCore.QGeometry()
        position_buffer = make_buffer(self._positions)
        position_attribute = _add_attribute(
            geometry, PositionAttribute, Qt3DCore.QAttribute.Float, 3, 0,
            position_buffer, 3 * 4)
        color_buffer = make_buffer(self._colors)
        color_attribute = _add_attribute(
            geometry, ColorAttribute, Qt3DCore.QAttribute.Float, 4, 0,
            color_buffer, 4 * 4)

        renderer = Qt3DRender.QGeometryRenderer(self.entity)
        renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)
        renderer.setGeometry(geometry)

        material = per_vertex_material(self.entity)
        if width and width > 1.0:
            _attach_line_width(material, width)

        self.entity.addComponent(renderer)
        self.entity.addComponent(material)

        self.geometry = geometry
        self.position_buffer = position_buffer
        self.position_attribute = position_attribute
        self.color_buffer = color_buffer
        self.color_attribute = color_attribute
        self.entity._qt3d_refs = (geometry, position_buffer, position_attribute,
                                  color_buffer, color_attribute, renderer, material)

    def set_points(self, points):
        array = np.asarray(points, dtype=np.float32).reshape(-1, 3)
        count = min(array.shape[0], self.capacity)
        if count:
            self._positions[:count] = array[:count]
        self.position_buffer.setData(QByteArray(self._positions.tobytes()))
        self.position_attribute.setCount(count)
        self.color_attribute.setCount(count)
        self.entity.setEnabled(count >= 2)

    def clear(self):
        self.position_attribute.setCount(0)
        self.color_attribute.setCount(0)
        self.entity.setEnabled(False)


def build_line_geometry(points, colors=None):
    """Build a ``Lines`` geometry from an ``(N, 3)`` point array.

    Vertices are drawn pairwise (0-1, 2-3, ...), matching the shared backplot
    segment layout.  *colors* is an optional uint8 array, either per-vertex
    ``(N, 4)`` or per-segment ``(N / 2, 4)``; per-segment colours are expanded
    by repeating each entry for both endpoints.
    """
    points = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    count = points.shape[0]

    geom = Qt3DCore.QGeometry()
    _add_attribute(geom, PositionAttribute, Qt3DCore.QAttribute.Float, 3, count,
                   make_buffer(points), 3 * 4)

    if colors is None or len(colors) == 0:
        # The per-vertex material always reads vertexColor. Bounds, grid and trail
        # entities often have no per-motion colour buffer, so supply a visible
        # neutral colour rather than leaving the shader input undefined.
        rgba = np.tile(np.asarray((0.72, 0.76, 0.82, 1.0), dtype=np.float32),
                       (count, 1))
    else:
        rgba = np.asarray(colors, dtype=np.float32)
        if rgba.shape[0] * 2 == count:
            rgba = np.repeat(rgba, 2, axis=0)
        if rgba.shape[0] != count or rgba.ndim != 2 or rgba.shape[1] != 4:
            rgba = np.tile(np.asarray((0.72, 0.76, 0.82, 1.0), dtype=np.float32),
                           (count, 1))
        elif rgba.max() > 1.0:
            rgba = rgba / 255.0
    if count:
        _add_attribute(geom, ColorAttribute, Qt3DCore.QAttribute.Float, 4, count,
                       make_buffer(rgba), 4 * 4)

    return geom


def build_indexed_triangle_geometry(vertices, indices, normals=None):
    """Build a triangle geometry from vertex and index arrays."""
    vertices = np.asarray(vertices, dtype=np.float32).reshape(-1, 3)
    indices = np.asarray(indices, dtype=np.uint32).reshape(-1)
    vcount = vertices.shape[0]

    geom = Qt3DCore.QGeometry()
    _add_attribute(geom, PositionAttribute, Qt3DCore.QAttribute.Float, 3, vcount,
                   make_buffer(vertices), 3 * 4)

    if normals is not None and len(normals) == vcount:
        normals = np.asarray(normals, dtype=np.float32).reshape(-1, 3)
        _add_attribute(geom, NormalAttribute, Qt3DCore.QAttribute.Float, 3, vcount,
                       make_buffer(normals), 3 * 4)

    index_attr = Qt3DCore.QAttribute()
    index_attr.setName("index")
    index_attr.setVertexBaseType(Qt3DCore.QAttribute.UnsignedInt)
    index_attr.setVertexSize(1)
    index_attr.setCount(indices.shape[0])
    index_buffer = make_buffer(indices)
    index_attr.setBuffer(index_buffer)
    index_attr.setAttributeType(Qt3DCore.QAttribute.IndexAttribute)
    geom.addAttribute(index_attr)
    refs = getattr(geom, "_qt3d_refs", [])
    refs.extend((index_buffer, index_attr))
    geom._qt3d_refs = refs
    return geom


def per_vertex_material(parent=None):
    """Unlit material that draws the per-vertex colour attribute."""
    return Qt3DExtras.QPerVertexColorMaterial(parent)


def solid_material(color=(0.8, 0.8, 0.8, 1.0), parent=None):
    """Simple lambert material with a uniform diffuse colour."""
    material = Qt3DExtras.QPhongMaterial(parent)
    material.setDiffuse(QColor.fromRgbF(*[float(component) for component in color]))
    return material


def build_gradient_background(parent, bottom_color, top_color):
    """Create a camera-facing, vertex-coloured gradient quad.

    The returned entity has ``_gradient_transform`` and geometry references
    attached for the backplot to position it behind its scene contents.
    """
    def rgba(color):
        return tuple(float(c) for c in color.getRgbF())

    bottom = rgba(bottom_color)
    top = rgba(top_color)
    vertices = np.asarray((
        (-0.5, -0.5, 0.0), (0.5, -0.5, 0.0),
        (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0),
    ), dtype=np.float32)
    colors = np.asarray((bottom, bottom, top, top), dtype=np.float32)
    indices = np.asarray((0, 1, 2, 0, 2, 3), dtype=np.uint32)

    geometry = Qt3DCore.QGeometry()
    _add_attribute(geometry, PositionAttribute, Qt3DCore.QAttribute.Float, 3, 4,
                   make_buffer(vertices), 3 * 4)
    _add_attribute(geometry, ColorAttribute, Qt3DCore.QAttribute.Float, 4, 4,
                   make_buffer(colors), 4 * 4)
    index_buffer = make_buffer(indices)
    index_attribute = Qt3DCore.QAttribute()
    index_attribute.setName("index")
    index_attribute.setVertexBaseType(Qt3DCore.QAttribute.UnsignedInt)
    index_attribute.setVertexSize(1)
    index_attribute.setCount(indices.size)
    index_attribute.setBuffer(index_buffer)
    index_attribute.setAttributeType(Qt3DCore.QAttribute.IndexAttribute)
    geometry.addAttribute(index_attribute)
    geometry._qt3d_refs.extend((index_buffer, index_attribute))

    entity = Qt3DCore.QEntity(parent)
    entity.setObjectName("backplot_gradient_background")
    renderer = Qt3DRender.QGeometryRenderer(entity)
    renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Triangles)
    renderer.setGeometry(geometry)
    material = per_vertex_material(entity)
    transform = Qt3DCore.QTransform(entity)
    entity.addComponent(renderer)
    entity.addComponent(material)
    entity.addComponent(transform)
    entity._qt3d_refs = (geometry, renderer, material, transform)
    entity._gradient_transform = transform
    return entity


def build_line_entity(parent, points, colors=None, width=1.0, name="path"):
    """Create a ``QEntity`` drawing *points* as coloured line segments."""
    entity = Qt3DCore.QEntity(parent)
    entity.setObjectName(name)

    geometry = build_line_geometry(points, colors)
    renderer = Qt3DRender.QGeometryRenderer(entity)
    renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)
    renderer.setGeometry(geometry)

    material = per_vertex_material(entity)
    if width and width > 1.0:
        _attach_line_width(material, width)

    entity.addComponent(renderer)
    entity.addComponent(material)
    # Keep Python references: without them PySide may garbage-collect the
    # wrappers even though Qt3D holds the C++ side, leaving a blank entity.
    entity._qt3d_refs = (geometry, renderer, material)
    return entity


def _attach_line_width(material, width):
    line_width = Qt3DRender.QLineWidth(material)
    line_width.setValue(float(width))
    line_width.setSmooth(True)
    effect = material.effect()
    if effect is None:
        return
    for technique in effect.techniques():
        for render_pass in technique.renderPasses():
            render_pass.addRenderState(line_width)


def build_grid_geometry(bounds, step=None, z=0.0):
    """Return line points for an XY grid spanning *bounds*.

    *bounds* is ``(xmin, xmax, ymin, ymax)``.  ``step`` defaults to a "nice"
    value near a tenth of the longer span.
    """
    xmin, xmax, ymin, ymax = bounds
    span = max(abs(xmax - xmin), abs(ymax - ymin), 1e-6)
    if step is None:
        step = _nice_step(span / 10.0)

    xs = _axis_ticks(xmin, xmax, step)
    ys = _axis_ticks(ymin, ymax, step)

    segments = []
    for x in xs:
        segments.extend(((x, ymin, z), (x, ymax, z)))
    for y in ys:
        segments.extend(((xmin, y, z), (xmax, y, z)))
    return np.asarray(segments, dtype=np.float32) if segments else np.zeros((0, 3), dtype=np.float32)


def _nice_step(raw):
    if raw <= 0:
        return 1.0
    import math
    exp = math.floor(math.log10(raw))
    base = raw / (10 ** exp)
    for nice in (1.0, 2.0, 5.0, 10.0):
        if base <= nice:
            return nice * (10 ** exp)
    return 10.0 * (10 ** exp)


def _axis_ticks(lo, hi, step):
    import math
    if step <= 0:
        return [lo, hi]
    start = math.floor(lo / step) * step
    ticks = []
    value = start
    while value <= hi + 1e-9:
        if value >= lo - 1e-9:
            ticks.append(value)
        value += step
    return ticks


def box_line_points(bounds):
    """Return the 24 line-segment endpoints of an axis-aligned box."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    corners = [
        (xmin, ymin, zmin), (xmax, ymin, zmin), (xmax, ymax, zmin), (xmin, ymax, zmin),
        (xmin, ymin, zmax), (xmax, ymin, zmax), (xmax, ymax, zmax), (xmin, ymax, zmax),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    points = []
    for a, b in edges:
        points.extend((corners[a], corners[b]))
    return np.asarray(points, dtype=np.float32)


def axis_triad_points(length, colors=None):
    """Return coloured line points for an XYZ axis triad at the origin."""
    points = np.asarray([
        (0, 0, 0), (length, 0, 0),
        (0, 0, 0), (0, length, 0),
        (0, 0, 0), (0, 0, length),
    ], dtype=np.float32)
    if colors is None:
        colors = ((255, 60, 60, 255), (60, 220, 60, 255), (80, 120, 255, 255))
    rgba = []
    for color in colors:
        value = color.getRgb() if hasattr(color, "getRgb") else color
        if len(value) == 3:
            value = (*value, 255)
        rgba.extend((value, value))
    return points, np.asarray(rgba, dtype=np.uint8)
