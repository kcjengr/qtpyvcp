"""Qt Quick 3D geometry adapters for the shared backplot data model.

Qt Quick 3D custom geometry is a packed vertex buffer.  Keeping this
conversion in one small adapter makes the LinuxCNC parser and
``BackplotGeometry`` renderer agnostic.
"""

import numpy as np
from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry


def map_vector_to_quick3d(vector):
    """Convert a CNC Z-up vector to Quick 3D's Y-up coordinate system."""
    x, y, z = vector
    return QVector3D(float(x), float(z), float(-y))


def map_points_to_quick3d(points):
    """Convert an ``(N, 3)`` CNC point array to Quick 3D scene coordinates."""
    vertices = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    if not vertices.size:
        return vertices
    return np.ascontiguousarray(
        vertices[:, (0, 2, 1)] * np.asarray((1.0, 1.0, -1.0), dtype=np.float32))


def map_point_from_quick3d(point):
    """Convert a Quick 3D scene point back to CNC (Z-up) coordinates."""
    x, y, z = (float(value) for value in point)
    return np.asarray((x, -z, y), dtype=np.float64)


class LineGeometry(QQuick3DGeometry):
    """A mutable list of independent 3D line segments."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("backplot_lines")
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Lines)
        self.setStride(3 * np.dtype(np.float32).itemsize)
        self.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0,
                          QQuick3DGeometry.Attribute.F32Type)
        self.replace(np.zeros((0, 3), dtype=np.float32))

    def replace(self, points):
        """Replace the segment endpoint array and refresh Quick 3D's bounds."""
        vertices = np.ascontiguousarray(points, dtype=np.float32).reshape(-1, 3)
        self.setVertexData(vertices.tobytes())
        if vertices.size:
            minimum = vertices.min(axis=0)
            maximum = vertices.max(axis=0)
            self.setBounds(QVector3D(*map(float, minimum)),
                           QVector3D(*map(float, maximum)))
        else:
            self.setBounds(QVector3D(), QVector3D())
        self.update()


class Quick3DPlotData(QObject):
    """QML-facing style properties and shared overlay geometries.

    Motion paths are *not* held here: they live in
    :class:`~.paths.PathGroupModel`, one row per WCS/motion role, so work-offset
    changes never rewrite vertex buffers.  This object keeps the overlay
    geometries (grid, axes, bounds, trail, highlight), the projection state and
    the motion-role colours.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._geometries = {name: LineGeometry() for name in (
            "grid", "axesX", "axesY", "axesZ", "machineBounds",
            "programBounds", "trail", "highlight", "transitions",
        )}
        for name, geometry in self._geometries.items():
            geometry.setObjectName("backplot_" + name)
        self._background = "#101820"
        self._background2 = "#101820"
        self._colors = {
            "traverse": "#c82323",
            "arcfeed": "#6e6eff",
            "feed": "#d2d2ff",
            "dwell": "#0000ff",
            "user": "#0064ff",
            "grid": "#454d55",
            "axesX": "#ff3c3c",
            "axesY": "#3cdc3c",
            "axesZ": "#5078ff",
            "bounds": "#b8c2cc",
            "trail": "#f2d84b",
            "highlight": "#ffe633",
            "transition": "#6e6eff",
        }
        self._grid_visible = False
        self._machine_bounds_visible = True
        self._program_bounds_visible = False
        self._perspective = False
        self._panning = False
        # Qt Quick 3D orthographic magnification is pixels per world unit, so
        # 1.0 shows one unit per pixel. A real fit replaces this at startup.
        self._ortho_magnification = 1.0
        self._tool_kind = "none"
        self._tool_visible = False
        self._tool_color = "#d2d2d7"
        self._tool_position = QVector3D()
        self._tool_scale = QVector3D(1.0, 1.0, 1.0)
        self._machine_visible = True

    colorChanged = Signal()
    toolChanged = Signal()
    picked = Signal(QVector3D, QVector3D)

    @Slot(QVector3D, QVector3D)
    def reportPick(self, near, far):
        """Called from QML with the click ray; forwards it to Python."""
        self.picked.emit(near, far)

    @Property(bool, notify=toolChanged)
    def machineVisible(self):
        return self._machine_visible

    @machineVisible.setter
    def machineVisible(self, value):
        value = bool(value)
        if value != self._machine_visible:
            self._machine_visible = value
            self.toolChanged.emit()

    def geometry(self, name):
        return self._geometries[name]

    def _geometry_property(name):
        return Property(QObject, lambda self: self.geometry(name), constant=True)

    grid = _geometry_property("grid")
    axesX = _geometry_property("axesX")
    axesY = _geometry_property("axesY")
    axesZ = _geometry_property("axesZ")
    machineBounds = _geometry_property("machineBounds")
    programBounds = _geometry_property("programBounds")
    trail = _geometry_property("trail")
    highlight = _geometry_property("highlight")
    transitions = _geometry_property("transitions")

    def _string_property(name, notify=colorChanged):
        return Property(str, lambda self: self._colors[name],
                        lambda self, value: self._set_color(name, value),
                        notify=notify)

    def _set_color(self, name, value):
        value = str(value)
        if value != self._colors[name]:
            self._colors[name] = value
            self.colorChanged.emit()

    traverseColor = _string_property("traverse")
    arcfeedColor = _string_property("arcfeed")
    feedColor = _string_property("feed")
    dwellColor = _string_property("dwell")
    userColor = _string_property("user")
    gridColor = _string_property("grid")
    axesXColor = _string_property("axesX")
    axesYColor = _string_property("axesY")
    axesZColor = _string_property("axesZ")
    boundsColor = _string_property("bounds")
    trailColor = _string_property("trail")
    highlightColor = _string_property("highlight")
    transitionColor = _string_property("transition")

    backgroundChanged = Signal()
    visibilityChanged = Signal()
    projectionChanged = Signal()
    interactionChanged = Signal()

    @Property(str, notify=backgroundChanged)
    def backgroundColor(self):
        return self._background

    @backgroundColor.setter
    def backgroundColor(self, value):
        value = str(value)
        if value != self._background:
            self._background = value
            self.backgroundChanged.emit()

    @Property(str, notify=backgroundChanged)
    def backgroundColor2(self):
        return self._background2

    @backgroundColor2.setter
    def backgroundColor2(self, value):
        value = str(value)
        if value != self._background2:
            self._background2 = value
            self.backgroundChanged.emit()

    @Property(bool, notify=visibilityChanged)
    def gridVisible(self):
        return self._grid_visible

    @gridVisible.setter
    def gridVisible(self, value):
        self._grid_visible = bool(value)
        self.visibilityChanged.emit()

    @Property(bool, notify=visibilityChanged)
    def machineBoundsVisible(self):
        return self._machine_bounds_visible

    @machineBoundsVisible.setter
    def machineBoundsVisible(self, value):
        self._machine_bounds_visible = bool(value)
        self.visibilityChanged.emit()

    @Property(bool, notify=visibilityChanged)
    def programBoundsVisible(self):
        return self._program_bounds_visible

    @programBoundsVisible.setter
    def programBoundsVisible(self, value):
        self._program_bounds_visible = bool(value)
        self.visibilityChanged.emit()

    @Property(bool, notify=projectionChanged)
    def perspective(self):
        return self._perspective

    @perspective.setter
    def perspective(self, value):
        self._perspective = bool(value)
        self.projectionChanged.emit()

    @Property(bool, notify=interactionChanged)
    def panning(self):
        return self._panning

    @panning.setter
    def panning(self, value):
        self._panning = bool(value)
        self.interactionChanged.emit()

    @Property(float, notify=projectionChanged)
    def orthoMagnification(self):
        return self._ortho_magnification

    @orthoMagnification.setter
    def orthoMagnification(self, value):
        self._ortho_magnification = max(float(value), 1e-6)
        self.projectionChanged.emit()

    # -- active tool body -------------------------------------------------

    @Property(str, notify=toolChanged)
    def toolKind(self):
        return self._tool_kind

    @toolKind.setter
    def toolKind(self, value):
        value = str(value)
        if value != self._tool_kind:
            self._tool_kind = value
            self.toolChanged.emit()

    @Property(bool, notify=toolChanged)
    def toolVisible(self):
        return self._tool_visible

    @toolVisible.setter
    def toolVisible(self, value):
        value = bool(value)
        if value != self._tool_visible:
            self._tool_visible = value
            self.toolChanged.emit()

    @Property(str, notify=toolChanged)
    def toolColor(self):
        return self._tool_color

    @toolColor.setter
    def toolColor(self, value):
        value = str(value)
        if value != self._tool_color:
            self._tool_color = value
            self.toolChanged.emit()

    @Property(QVector3D, notify=toolChanged)
    def toolPosition(self):
        return self._tool_position

    @toolPosition.setter
    def toolPosition(self, value):
        self._tool_position = QVector3D(value)
        self.toolChanged.emit()

    @Property(QVector3D, notify=toolChanged)
    def toolScale(self):
        return self._tool_scale

    @toolScale.setter
    def toolScale(self, value):
        self._tool_scale = QVector3D(value)
        self.toolChanged.emit()
