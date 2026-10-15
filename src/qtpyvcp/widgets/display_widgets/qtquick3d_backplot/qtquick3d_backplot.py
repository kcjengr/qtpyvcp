"""LinuxCNC backplot rendered with Qt Quick 3D.

The parser, coordinate normalization, work-coordinate paths, and segment
bookkeeping come from ``backplot_common``.  This widget owns the Qt Quick host
and converts those arrays to QQuick3DGeometry buffers; it does not import or
depend on Qt3D.
"""

import math
import os
from collections import deque

import numpy as np
from PySide6.QtCore import Property, QObject, QSize, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QQuaternion, QVector3D
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from shiboken6 import isValid

import linuxcnc
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import connectSetting, getSetting
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.widgets.base_widgets.base_widget import reset_to
from qtpyvcp.widgets.display_widgets.backplot_common import (
    DEFAULT_ROLE_COLORS,
    load_geometry,
)
from qtpyvcp.widgets.display_widgets.vtk_backplot.base_backplot import BaseBackPlot
from qtpyvcp.widgets.display_widgets.vtk_backplot.linuxcnc_datasource import (
    LinuxCncDataSource,
)

from . import machine, tool
from .geometry import (
    Quick3DPlotData,
    map_points_to_quick3d,
    map_vector_to_quick3d,
)
from .navigation import BackplotNavigation

LOG = logger.getLogger(__name__)
IN_DESIGNER = os.getenv("DESIGNER", "").lower() not in ("", "0", "false", "no")

ROLE_NAMES = ("traverse", "arcfeed", "feed", "dwell", "user")

# Extra radius around the machine/program bounds, as a fraction of the bounds
# half-diagonal, so the camera fit and clip planes cover a little space beyond
# the machine envelope. Scale-independent, so it works for inch and metric.
BOUNDS_MARGIN = 0.1
VIEW_DIRECTIONS = {
    "P": ((1.0, -1.0, 1.0), (0.0, 0.0, 1.0)),
    "X": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    "Y": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "Z": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    "Z2": ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    "XZ": ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    "XZ2": ((0.0, -1.0, 0.0), (-1.0, 0.0, 0.0)),
}


def _unit(vector):
    result = np.asarray(vector, dtype=np.float64)
    length = float(np.linalg.norm(result))
    return result / length if length > 1e-12 else np.array((1.0, -1.0, 1.0)) / math.sqrt(3.0)


def _box_lines(bounds):
    if bounds is None:
        return np.zeros((0, 3), dtype=np.float32)
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    corners = ((xmin, ymin, zmin), (xmax, ymin, zmin),
               (xmax, ymax, zmin), (xmin, ymax, zmin),
               (xmin, ymin, zmax), (xmax, ymin, zmax),
               (xmax, ymax, zmax), (xmin, ymax, zmax))
    edges = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
             (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))
    return np.asarray([corners[index] for edge in edges for index in edge],
                      dtype=np.float32)


def segment_role_indices(colors, palette):
    """Map each segment RGBA colour to a role index in *palette*.

    Exact palette matches are preferred so a distinct feed/arcfeed colour is
    never confused with a neighbour. Unmatched colours fall back to the nearest
    palette entry using 64-bit math, because ``255 ** 2`` overflows ``int16``
    and silently selects the wrong role.
    """
    colors = np.asarray(colors, dtype=np.int64).reshape(-1, 4)
    palette = np.asarray(palette, dtype=np.int64).reshape(-1, 4)
    if colors.shape[0] == 0 or palette.shape[0] == 0:
        return np.zeros(colors.shape[0], dtype=np.int64)

    exact = (colors[:, None, :] == palette[None, :, :]).all(axis=2)
    indices = exact.argmax(axis=1)
    unmatched = ~exact.any(axis=1)
    if unmatched.any():
        distances = np.square(
            colors[unmatched, None, :] - palette[None, :, :]).sum(axis=2)
        indices[unmatched] = distances.argmin(axis=1)
    return indices


class QuickCameraRig:
    """Small camera controller compatible with the existing navigation filter."""

    def __init__(self, plot_data, camera_provider, viewport_size):
        self.data = plot_data
        self._camera_provider = camera_provider
        self._viewport_size = viewport_size
        self._center = QVector3D()
        self._offset = QVector3D(100.0, 100.0, 100.0)
        self._up = QVector3D(0.0, 1.0, 0.0)
        self._orthographic = True
        self._fov = 35.0
        # Half the scene diagonal, used to derive clip planes. Set from the
        # machine/program bounds so inch and metric machines both get a sane
        # near/far range instead of a fixed 0.01 / 1e6 span.
        self._scene_radius = None
        self._apply()

    def set_scene_radius(self, radius):
        try:
            radius = float(radius)
        except (TypeError, ValueError):
            return
        if radius > 0.0:
            self._scene_radius = radius
            self._apply()

    def _clip_planes(self):
        eye = max(self._offset.length(), 1e-6)
        radius = self._scene_radius if self._scene_radius else max(eye * 0.5, 1.0)
        near = eye - radius
        # Keep the near plane in front of the camera but away from the eye, so
        # it never clips the whole scene when the camera is inside the bounds.
        if near <= 0.0 or near > eye * 0.5:
            near = max(radius * 1e-3, eye * 1e-3, 1e-4)
        far = max(eye + radius * 4.0, near + radius * 4.0, near * 10.0)
        return near, far

    def _apply(self):
        position = self._center + self._offset
        orientation = QQuaternion.fromDirection(self._offset, self._up)
        clip_near, clip_far = self._clip_planes()
        try:
            cameras = self._camera_provider()
        except RuntimeError:
            cameras = ()
        for camera in cameras:
            if camera is None or not isValid(camera):
                continue
            try:
                camera.setProperty("position", position)
                camera.setProperty("rotation", orientation)
                camera.setProperty("clipNear", clip_near)
                camera.setProperty("clipFar", clip_far)
            except RuntimeError:
                # Qt Quick may replace its QML root while the editor reloads a
                # scene; the next camera update will reacquire its new objects.
                continue

    def set_perspective(self):
        self._orthographic = False
        self.data.perspective = True
        self._apply()

    def set_orthographic(self):
        self._orthographic = True
        self.data.perspective = False
        self._apply()

    @property
    def is_orthographic(self):
        return self._orthographic

    def look_at(self, center, direction, up=None, distance=None):
        self._center = map_vector_to_quick3d(center)
        direction = np.asarray(direction, dtype=np.float64)
        mapped_direction = np.asarray((direction[0], direction[2], -direction[1]))
        mapped_direction = _unit(mapped_direction)
        if up is not None:
            up = np.asarray(up, dtype=np.float64)
            self._up = map_vector_to_quick3d(up).normalized()
        self._offset = QVector3D(*map(float, mapped_direction)) * float(
            distance if distance is not None else max(self._offset.length(), 1.0))
        self._apply()

    def set_view(self, name, center, distance=None):
        direction, up = VIEW_DIRECTIONS.get(str(name or "P").upper(), VIEW_DIRECTIONS["P"])
        self.look_at(center, direction, up, distance)

    def fit_bounds(self, bounds, aspect=1.0, padding=1.1, distance=None):
        if bounds is None:
            return
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        center = ((xmin + xmax) * 0.5, (ymin + ymax) * 0.5,
                  (zmin + zmax) * 0.5)
        extent = np.asarray((xmax - xmin, ymax - ymin, zmax - zmin), dtype=float)
        diagonal = max(float(np.linalg.norm(extent)), 1.0)
        # Add a margin so the fit/clip envelope sits just outside the bounds.
        self._scene_radius = diagonal * 0.5 * (1.0 + BOUNDS_MARGIN)
        direction = self._offset
        direction = np.asarray((direction.x(), -direction.z(), direction.y()))
        if self._orthographic:
            span = max(float(np.max(extent)), 1.0) * max(float(padding), 1.0)
            self.data.orthoMagnification = 2.0 / span
            distance = distance or diagonal * 2.0
        else:
            distance = distance or diagonal * 0.5 / math.sin(math.radians(self._fov / 2.0)) * padding
        direction = _unit(direction)
        self.look_at(center, direction, (0.0, 0.0, 1.0), distance)

    def zoom(self, factor):
        factor = float(factor)
        if factor <= 0:
            return
        if self._orthographic:
            self.data.orthoMagnification = self.data.orthoMagnification / factor
        else:
            self._offset *= factor
        self._apply()

    def dolly(self, factor):
        factor = float(factor)
        if factor <= 0:
            return
        if self._orthographic:
            self.data.orthoMagnification *= factor
        else:
            self._offset /= factor
        self._apply()

    def orbit(self, azimuth_deg, elevation_deg):
        around_z = QQuaternion.fromAxisAndAngle(QVector3D(0, 1, 0), float(azimuth_deg))
        self._offset = around_z.rotatedVector(self._offset)
        self._up = around_z.rotatedVector(self._up)
        forward = (-self._offset).normalized()
        right = QVector3D.crossProduct(forward, self._up).normalized()
        if right.lengthSquared() > 1e-12:
            pitch = QQuaternion.fromAxisAndAngle(right, float(elevation_deg))
            self._offset = pitch.rotatedVector(self._offset)
            self._up = pitch.rotatedVector(self._up)
        self._apply()

    def pan(self, dx_pixels, dy_pixels, viewport_width, viewport_height):
        height = max(float(viewport_height), 1.0)
        forward = (-self._offset).normalized()
        right = QVector3D.crossProduct(forward, self._up).normalized()
        if right.lengthSquared() < 1e-12:
            return
        true_up = QVector3D.crossProduct(right, forward).normalized()
        world_height = (1.0 / max(self.data.orthoMagnification, 1e-6)
                        if self._orthographic else
                        2.0 * self._offset.length() * math.tan(math.radians(self._fov / 2.0)))
        delta = right * (-float(dx_pixels) * world_height / height)
        delta += true_up * (float(dy_pixels) * world_height / height)
        self._center += delta
        self._apply()


class Qt3D0(QWidget, VCPWidget, BaseBackPlot):
    """Qt Quick 3D backplot using the historical ``Qt3D0`` widget name."""

    programLineSelected = Signal(int)
    programLinesSelected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._designer = IN_DESIGNER
        self._geometry = None
        # Bounds must exist before any view slot runs: setViewProgram/Ortho or
        # a camera action can fire before a program has been loaded.
        self._machine_bounds = None
        self._program_bounds = None
        self._last_filename = ""
        self._active_view = "P"
        self._position = (0.0, 0.0, 0.0)
        self._trail = deque(maxlen=4000)
        self._show_fps = False
        self._show_spindle = True
        self._show_machine = True
        self._show_machine_ticks = False
        self._show_machine_labels = False
        self._show_surface = False
        self._alpha_blend = False
        self._multitool_colors = False
        self._enable_program_ticks = True
        self._running = False
        self._joints = None
        self._background_color = QColor("#101820")
        self._background_color2 = QColor("#101820")
        self._nav_helper_x_axis_color = QColor(255, 60, 60)
        self._nav_helper_y_axis_color = QColor(60, 220, 60)
        self._nav_helper_z_axis_color = QColor(80, 120, 255)
        self._nav_helper_props = {}
        # Live WCS state: the active WCS must use the status values, not the
        # offset-table snapshot (see _wcs_offsets).
        self._active_wcs_index = None
        self._active_wcs_offset = None
        self._active_rotation = 0.0
        self._tool_shape = tool.ToolShape()
        self._tool_number = 0
        self._default_role_colors = {
            role: QColor(*DEFAULT_ROLE_COLORS[role]) for role in ROLE_NAMES
        }
        self._role_colors = {role: QColor(color)
                             for role, color in self._default_role_colors.items()}

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        if self._designer:
            label = QLabel("Qt Quick 3D Backplot\n(3D visualization)", self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(label)
            self.setMinimumSize(400, 300)
            return

        # Create the QQuickWidget first so it is destroyed before plot_data.
        # QObject deletes children in creation order; if plot_data died first,
        # every QML binding would re-evaluate against a null object at teardown.
        self.quick_widget = QQuickWidget(self)
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.quick_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.plot_data = Quick3DPlotData(self)
        self._apply_plot_colors()
        self.machine_parts = machine.MachinePartsModel(self)
        self.quick_widget.rootContext().setContextProperty("plotData", self.plot_data)
        self.quick_widget.rootContext().setContextProperty("machineParts", self.machine_parts)
        self.plot_data.picked.connect(self._on_picked)
        qml_path = os.path.join(os.path.dirname(__file__), "scene.qml")
        self.quick_widget.setSource(QUrl.fromLocalFile(qml_path))
        self._layout.addWidget(self.quick_widget)
        for error in self.quick_widget.errors():
            LOG.error("Qt Quick 3D scene load error: %s", error.toString())

        self.rig = QuickCameraRig(self.plot_data, self._find_cameras,
                                  self._viewport_size)
        self.navigation = BackplotNavigation(
            self.rig, self.quick_widget, self._viewport_size, parent=self)
        self.quick_widget.installEventFilter(self.navigation)

        self.datasource = LinuxCncDataSource()
        self._stat = linuxcnc.stat()
        self._is_lathe = self.datasource.isMachineLathe()
        self._pick = {}
        self._initialize_geometry()
        self._wire_signals()
        self._connect_settings()
        self.setViewMachine()
        QTimer.singleShot(0, self._load_current_program)
        QTimer.singleShot(500, self._load_current_program)
        LOG.info("Qt Quick 3D backplot initialized")

    # -- scene and geometry -------------------------------------------------

    def _viewport_size(self):
        widget = getattr(self, "quick_widget", None)
        if widget is None:
            return 1, 1
        return max(widget.width(), 1), max(widget.height(), 1)

    def _find_cameras(self):
        """Return currently-live QML cameras, avoiding cached scene wrappers."""
        widget = getattr(self, "quick_widget", None)
        if widget is None or not isValid(widget):
            return ()
        try:
            root = widget.rootObject()
            if root is None or not isValid(root):
                return ()
            cameras = tuple(root.findChild(QObject, name) for name in (
                "perspectiveCamera", "orthographicCamera"))
        except RuntimeError:
            return ()
        return tuple(camera for camera in cameras
                     if camera is not None and isValid(camera))

    def _initialize_geometry(self):
        self._machine_bounds = self._machine_box_bounds()
        self._rebuild_machine_bounds()
        self._rebuild_axes()
        self._rebuild_grid()
        self._rebuild_tool()
        self._build_machine_parts()

    # -- machine parts (MACHINE_PARTS) --------------------------------------

    def _build_machine_parts(self):
        ini = getattr(self.datasource, "_inifile", None)
        if ini is None:
            return
        parts_file = ini.find("VTK", "MACHINE_PARTS")
        if not parts_file:
            return
        config_dir = getattr(self.datasource, "config_dir", None)
        path = parts_file
        if not os.path.isabs(path) and config_dir:
            path = os.path.normpath(os.path.join(config_dir, path))
        if not os.path.isfile(path):
            LOG.warning("Quick 3D MACHINE_PARTS not found: %s", path)
            return
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except Exception:
            LOG.exception("failed to load MACHINE_PARTS for Qt Quick 3D: %s", path)
            return
        self.machine_parts.load(
            data, config_dir=config_dir or os.path.dirname(path))

    def _apply_joint_feedback(self):
        if self.machine_parts.rowCount() == 0:
            return
        status = getattr(self.datasource, "_status", None)
        stat = getattr(status, "stat", None)
        joints = getattr(stat, "joint_actual_position", None)
        if joints:
            self.machine_parts.apply_joint_values(joints)

    # -- picking / highlighting --------------------------------------------

    @staticmethod
    def _dist_point_segments(point, starts, ends):
        ab = ends - starts
        denom = np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-12)
        t = np.clip(np.einsum("ij,ij->i", point - starts, ab) / denom, 0.0, 1.0)
        projected = starts + t[:, None] * ab
        return np.linalg.norm(projected - point, axis=1)

    def _clear_highlight(self):
        self.plot_data.highlight.replace(np.zeros((0, 3), np.float32))

    def _on_picked(self, point):
        if self._geometry is None or not self._pick:
            return
        p = np.asarray((point.x(), point.y(), point.z()), dtype=np.float32)
        best = None
        for starts, ends, meta in self._pick.values():
            if starts.shape[0] == 0:
                continue
            distances = self._dist_point_segments(p, starts, ends)
            index = int(np.argmin(distances))
            if best is None or distances[index] < best[0]:
                best = (float(distances[index]), starts[index],
                        ends[index], meta[index])
        if best is None:
            return
        _, start, end, meta = best
        self.plot_data.highlight.replace(
            np.asarray([start, end], dtype=np.float32))
        line_number = int(meta[2])
        if line_number >= 0:
            self.programLineSelected.emit(line_number)
            self.programLinesSelected.emit([line_number])

    # -- active tool body ---------------------------------------------------

    def _current_tool_number(self):
        stat = getattr(getattr(self.datasource, "_status", None), "stat", None)
        try:
            return int(getattr(stat, "tool_in_spindle", 0) or 0)
        except (TypeError, ValueError):
            return 0

    def _rebuild_tool(self):
        self._tool_number = self._current_tool_number()
        try:
            tool_table = self.datasource.getToolTable()
        except (AttributeError, RuntimeError, TypeError, ValueError):
            LOG.debug("tool table unavailable for Qt Quick 3D tool geometry",
                      exc_info=True)
            tool_table = []

        def _flag(name):
            fn = getattr(self.datasource, name, None)
            if not callable(fn):
                return False
            try:
                return bool(fn())
            except (AttributeError, RuntimeError, TypeError, ValueError):
                return False

        shape = tool.tool_shape(
            tool_table,
            self._tool_number,
            metric=_flag("isMachineMetric"),
            lathe=_flag("isMachineLathe"),
            robot=False,
            foam=_flag("isMachineFoam"),
            jet=_flag("isMachineJet"),
        )
        self._tool_shape = shape
        self.plot_data.toolKind = shape.kind
        self.plot_data.toolColor = "#d2d2d7"
        if shape.visible:
            # Built-in primitives are 100 units tall with a 100-unit diameter.
            self.plot_data.toolScale = QVector3D(
                shape.radius / 50.0, shape.length / 100.0, shape.radius / 50.0)
        self.plot_data.toolVisible = bool(self._show_spindle and shape.visible)
        self._update_tool_transform()

    def _current_tool_offset(self):
        stat = getattr(getattr(self.datasource, "_status", None), "stat", None)
        try:
            values = getattr(stat, "tool_offset", None)
            return tuple(float(v) for v in values)
        except (TypeError, ValueError):
            return (0.0,) * 9

    def _update_tool_transform(self):
        shape = self._tool_shape
        if not shape.visible:
            return
        x, y, z = self._position
        # The loaded path is drawn without TLO, so apply the runtime tool offset
        # to the tool here. QtPyVCP's DRO uses work = position - g5x - tool - g92
        # (plugins/positions.py), so the tool tip is position - tool_offset.
        tlo = self._current_tool_offset()
        tip = (
            x - (tlo[0] if len(tlo) > 0 else 0.0),
            y - (tlo[1] if len(tlo) > 1 else 0.0),
            z - (tlo[2] if len(tlo) > 2 else 0.0),
        )
        offset = tool.tool_body_offset(shape)
        self.plot_data.toolPosition = map_vector_to_quick3d(
            (tip[0] + offset[0], tip[1] + offset[1], tip[2] + offset[2]))

    def _apply_plot_colors(self):
        if not hasattr(self, "plot_data"):
            return
        self.plot_data.backgroundColor = self._background_color.name()
        for role in ROLE_NAMES:
            setattr(self.plot_data, role + "Color", self._role_colors[role].name())

    def _rebuild_program_geometry(self):
        groups = {role: [] for role in ROLE_NAMES}
        # Per-role scene-space segment endpoints plus (wcs, segment, line)
        # metadata, used to turn a 3D pick into a program line selection.
        pick = {role: ([], [], []) for role in ROLE_NAMES}
        transformed = []
        if self._geometry is not None:
            palette = np.asarray([self._role_colors[role].getRgb() for role in ROLE_NAMES],
                                 dtype=np.int64)
            for wcs_index, path in self._geometry.paths.items():
                if path.is_empty:
                    continue
                x, y, z, rotation = self._wcs_offsets(wcs_index)
                radians = math.radians(rotation)
                cosine, sine = math.cos(radians), math.sin(radians)
                points = np.asarray(path.points, dtype=np.float32).copy()
                px, py = points[:, 0].copy(), points[:, 1].copy()
                points[:, 0] = cosine * px - sine * py + x
                points[:, 1] = sine * px + cosine * py + y
                points[:, 2] += z
                transformed.append(points)
                colors = np.asarray(path.colors, dtype=np.int64).reshape(-1, 4)
                if colors.shape[0] != points.shape[0] // 2:
                    colors = np.tile(palette[2], (points.shape[0] // 2, 1))
                role_indices = segment_role_indices(colors, palette)
                segment_points = points.reshape(-1, 2, 3)
                line_numbers = np.asarray(path.line_numbers, dtype=np.int64)
                segment_count = segment_points.shape[0]
                for role_index, role in enumerate(ROLE_NAMES):
                    mask = role_indices == role_index
                    if not mask.any():
                        continue
                    selected = segment_points[mask]
                    groups[role].append(selected.reshape(-1, 3))
                    scene = map_points_to_quick3d(
                        selected.reshape(-1, 3)).reshape(-1, 2, 3)
                    pick[role][0].append(scene[:, 0, :])
                    pick[role][1].append(scene[:, 1, :])
                    indices = np.nonzero(mask)[0]
                    if line_numbers.shape[0] == segment_count:
                        lines = line_numbers[indices]
                    else:
                        lines = np.full(indices.shape[0], -1, dtype=np.int64)
                    meta = np.stack((
                        np.full(indices.shape[0], wcs_index, dtype=np.int64),
                        indices, lines), axis=1)
                    pick[role][2].append(meta)

        self._pick = {}
        for role in ROLE_NAMES:
            starts, ends, metas = pick[role]
            if starts:
                self._pick[role] = (
                    np.concatenate(starts, axis=0),
                    np.concatenate(ends, axis=0),
                    np.concatenate(metas, axis=0),
                )

        for role, chunks in groups.items():
            data = np.concatenate(chunks, axis=0) if chunks else np.zeros((0, 3), np.float32)
            self.plot_data.geometry(role).replace(map_points_to_quick3d(data))
        self._clear_highlight()
        if transformed:
            points = np.concatenate(transformed, axis=0)
            self._program_bounds = (
                float(points[:, 0].min()), float(points[:, 0].max()),
                float(points[:, 1].min()), float(points[:, 1].max()),
                float(points[:, 2].min()), float(points[:, 2].max()),
            )
        else:
            self._program_bounds = None
        self._rebuild_program_bounds()
        self._update_clip_reference()

    def _rebuild_machine_bounds(self):
        self._machine_bounds = self._machine_box_bounds()
        bounds = self._machine_bounds
        self.plot_data.machineBounds.replace(
            map_points_to_quick3d(_box_lines(bounds)) if bounds else np.zeros((0, 3), np.float32))
        self._update_clip_reference()

    def _update_clip_reference(self):
        """Size the camera clip range from the machine/program extents.

        Uses the current program bounds when available, else the machine
        bounds, so inch (small) and metric (large) machines both get a
        proportional near/far range.
        """
        bounds = self._program_bounds or self._machine_bounds
        if not bounds:
            return
        diagonal = math.sqrt(sum(
            (bounds[i + 1] - bounds[i]) ** 2 for i in (0, 2, 4)))
        half = diagonal * 0.5
        self.rig.set_scene_radius(max(half * (1.0 + BOUNDS_MARGIN), 0.5))

    def _rebuild_program_bounds(self):
        bounds = self._program_bounds
        self.plot_data.programBounds.replace(
            map_points_to_quick3d(_box_lines(bounds)) if bounds else np.zeros((0, 3), np.float32))

    def _rebuild_axes(self):
        length = 25.4 if self.datasource.isMachineMetric() else 1.0
        self.plot_data.axesX.replace(map_points_to_quick3d(((0, 0, 0), (length, 0, 0))))
        self.plot_data.axesY.replace(map_points_to_quick3d(((0, 0, 0), (0, length, 0))))
        self.plot_data.axesZ.replace(map_points_to_quick3d(((0, 0, 0), (0, 0, length))))

    def _rebuild_grid(self):
        bounds = self._machine_bounds
        if bounds is None:
            self.plot_data.grid.replace(np.zeros((0, 3), dtype=np.float32))
            return
        xmin, xmax, ymin, ymax = bounds[0], bounds[1], bounds[2], bounds[3]
        span = max(xmax - xmin, ymax - ymin, 1.0)
        raw_step = span / 10.0
        exponent = 10 ** math.floor(math.log10(raw_step))
        step = next((value * exponent for value in (1, 2, 5, 10)
                     if raw_step / exponent <= value), 10 * exponent)
        points = []
        x = math.ceil(xmin / step) * step
        while x <= xmax + 1e-8:
            points.extend(((x, ymin, 0), (x, ymax, 0)))
            x += step
        y = math.ceil(ymin / step) * step
        while y <= ymax + 1e-8:
            points.extend(((xmin, y, 0), (xmax, y, 0)))
            y += step
        self.plot_data.grid.replace(map_points_to_quick3d(points))

    # -- LinuxCNC and program input ----------------------------------------

    def _wire_signals(self):
        ds = self.datasource
        ds.programLoaded.connect(self.load_program)
        ds.positionChanged.connect(self.update_position)
        ds.g5xOffsetChanged.connect(self.update_g5x_offset)
        ds.g92OffsetChanged.connect(self.update_g92_offset)
        ds.g5xIndexChanged.connect(self.update_g5x_index)
        ds.rotationXYChanged.connect(self.update_rotation_xy)
        ds.offsetTableChanged.connect(self.on_offset_table_changed)
        ds.toolInSpindleChanged.connect(self.update_tool_number)
        ds.toolTableChanged.connect(self.update_tool_table)
        ds.toolOffsetChanged.connect(self.update_tool_table)
        try:
            self._stat.poll()
        except Exception:
            LOG.debug("LinuxCNC status not ready during Qt Quick 3D startup", exc_info=True)
        self._seed_wcs_state()

    def _seed_wcs_state(self):
        """Capture the live active-WCS offsets/rotation for path placement."""
        ds = self.datasource
        try:
            self._active_wcs_index = ds.getActiveWcsIndex()
        except (AttributeError, RuntimeError, TypeError, ValueError):
            self._active_wcs_index = None
        try:
            self._active_wcs_offset = tuple(ds.getActiveWcsOffsets())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            self._active_wcs_offset = None
        try:
            self._active_rotation = float(ds.getRotationOfActiveWcs())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            self._active_rotation = 0.0

    def _connect_settings(self):
        connectSetting("backplot.show-grid", self.showGrid)
        connectSetting("backplot.show-program-bounds", self.showProgramBounds)
        connectSetting("backplot.show-machine-bounds", self.showMachineBounds)
        connectSetting("backplot.view", self.setView)
        connectSetting("backplot.perspective-view", self.viewPerspective)

    def _load_current_program(self):
        try:
            self._stat.poll()
            filename = self._stat.file
        except Exception:
            LOG.debug("Unable to read active LinuxCNC file", exc_info=True)
            return
        if filename and os.path.isfile(filename) and filename != self._last_filename:
            self.load_program(filename)

    @Slot()
    def reload_program(self, *args, **kwargs):
        self.load_program(self._last_filename, force=True)

    def load_program(self, filename=None, *, force=False):
        if self._designer:
            return
        filename = filename or self._last_filename
        if not filename or not os.path.isfile(filename):
            return
        if not force and filename == self._last_filename and self._geometry is not None:
            return
        self._last_filename = filename
        table_rotary = any(
            self.datasource.getAxisMotionOwners().get(axis, "head") == "table"
            for axis in ("A", "B", "C"))
        geometry = load_geometry(
            filename, self.datasource,
            colors={key: color.getRgb() for key, color in self._role_colors.items()},
            prefer_native=True, cpp_ok=not table_rotary)
        if geometry is None:
            LOG.warning("Qt Quick 3D backplot produced no geometry for %s", filename)
            return
        self._geometry = geometry
        self._rebuild_program_geometry()
        self.setViewProgram("p")
        LOG.info("Qt Quick 3D backplot loaded %s: %d WCS paths, %d segments",
                 filename, len(geometry.paths), geometry.added_segments)

    def _offset_columns(self):
        if not hasattr(self, "_offset_columns_cache"):
            try:
                self._offset_columns_cache = dict(self.datasource.getOffsetColumns() or {})
            except (AttributeError, RuntimeError, TypeError, ValueError):
                self._offset_columns_cache = {}
        return self._offset_columns_cache

    def _wcs_offsets(self, wcs_index):
        columns = self._offset_columns()
        try:
            entry = self.datasource.getWcsOffsets().get(wcs_index)
            values = list(entry) if entry is not None else []
        except (AttributeError, RuntimeError, TypeError, ValueError, KeyError):
            values = []

        def table_value(name):
            index = columns.get(name)
            if index is None:
                return None
            try:
                return float(values[index])
            except (IndexError, TypeError, ValueError):
                return None

        x = table_value("X") or 0.0
        y = table_value("Y") or 0.0
        z = table_value("Z") or 0.0
        rotation = table_value("R") or 0.0

        # Prefer live status values for the active WCS: the offset-table
        # snapshot can be stale or not yet loaded, which drew the active path
        # at program coordinates while the tool sat at program + offset.
        if wcs_index == self._active_wcs_index:
            live = self._active_wcs_offset
            if isinstance(live, (list, tuple)):
                if len(live) > 0:
                    x = float(live[0])
                if len(live) > 1:
                    y = float(live[1])
                if len(live) > 2:
                    z = float(live[2])
            live_rotation = float(self._active_rotation or 0.0)
            if live_rotation != 0.0:
                rotation = live_rotation

        return x, y, z, rotation

    def _machine_box_bounds(self):
        try:
            axes = self.datasource.getAxis()
            return tuple(float(axes[index][key]) for index in range(3)
                         for key in ("min_position_limit", "max_position_limit"))
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            return None

    # -- coordinates and live position ------------------------------------

    def update_g5x_offset(self, offset):
        if offset is not None:
            self._active_wcs_offset = tuple(offset)
        self._rebuild_program_geometry()

    @Slot(object)
    def on_offset_table_changed(self, _offset_table=None):
        self._rebuild_program_geometry()

    def update_g92_offset(self, _offset):
        pass

    def update_g5x_index(self, index):
        try:
            self._active_wcs_index = int(index)
        except (TypeError, ValueError):
            pass
        self._rebuild_program_geometry()

    def update_rotation_xy(self, rotation):
        try:
            self._active_rotation = float(rotation)
        except (TypeError, ValueError):
            self._active_rotation = 0.0
        self._rebuild_program_geometry()

    @Slot(object)
    @Slot(int)
    def update_tool_number(self, tool_number):
        """Rebuild the tool body when the spindle tool changes."""
        try:
            self._tool_number = int(tool_number)
        except (TypeError, ValueError):
            self._tool_number = 0
        self._rebuild_tool()

    @Slot(object)
    def update_tool_table(self, *_args):
        """Rebuild the tool body when the tool table or TLO changes."""
        self._rebuild_tool()

    def update_position(self, position):
        if self._designer or position is None:
            return
        x, y, z = map(float, position[:3])
        if self.datasource.isMachineLathe():
            z, y = y, z
        self._position = (x, y, z)
        self._update_tool_transform()
        self._apply_joint_feedback()
        self._trail.append(self._position)
        points = np.asarray(self._trail, dtype=np.float32).reshape(-1, 3)
        if len(points) >= 2:
            segments = np.empty((2 * (len(points) - 1), 3), dtype=np.float32)
            segments[0::2], segments[1::2] = points[:-1], points[1:]
            self.plot_data.trail.replace(map_points_to_quick3d(segments))
        else:
            self.plot_data.trail.replace(np.zeros((0, 3), dtype=np.float32))

    @Slot()
    def clearLivePlot(self):
        self._trail.clear()
        if hasattr(self, "plot_data"):
            self.plot_data.trail.replace(np.zeros((0, 3), dtype=np.float32))

    # -- camera controls ----------------------------------------------------

    def _active_center(self):
        bounds = self._machine_bounds if self._active_view == "M" else self._program_bounds
        bounds = bounds or self._machine_bounds
        if bounds is None:
            return (0.0, 0.0, 0.0)
        return tuple((bounds[i] + bounds[i + 1]) / 2.0 for i in (0, 2, 4))

    @Slot()
    def setViewP(self):
        self._active_view = "P"
        self.rig.set_perspective()
        self.rig.set_view("P", self._active_center())

    @Slot()
    def setViewX(self):
        self._active_view = "X"
        self.rig.set_view("X", self._active_center())

    @Slot()
    def setViewY(self):
        self._active_view = "Y"
        self.rig.set_view("Y", self._active_center())

    @Slot()
    def setViewZ(self):
        self._active_view = "Z"
        self.rig.set_view("Z", self._active_center())

    @Slot()
    def setViewZ2(self):
        self._active_view = "Z2"
        self.rig.set_view("Z2", self._active_center())

    @Slot()
    def setViewXZ(self):
        self._active_view = "XZ"
        self.rig.set_view("XZ", self._active_center())

    @Slot()
    def setViewXZ2(self):
        self._active_view = "XZ2"
        self.rig.set_view("XZ2", self._active_center())

    @Slot()
    def setViewMachine(self):
        self._active_view = "M"
        self.rig.set_orthographic()
        self.rig.fit_bounds(self._machine_bounds, padding=1.1)

    @Slot()
    def setViewPath(self):
        self._active_view = "Path"
        self.rig.set_view("P", self._active_center())

    @Slot()
    @Slot(str)
    def setViewProgram(self, view="p"):
        self._active_view = "Program"
        self.rig.set_orthographic()
        self.rig.fit_bounds(self._program_bounds or self._machine_bounds, padding=1.1)
        self.clearLivePlot()

    @Slot()
    def setViewOrtho(self):
        self.rig.set_orthographic()
        self.rig.fit_bounds(self._program_bounds or self._machine_bounds)

    @Slot()
    def setViewPersp(self):
        self.rig.set_perspective()

    @Slot(int)
    @Slot(str)
    @Slot(object)
    def setView(self, view):
        if isinstance(view, int):
            options = list(getSetting("backplot.view").enum_options or ())
            names = [option.split(":")[0] for option in options]
            if 0 <= view < len(names):
                view = names[view]
        dispatch = {name: getattr(self, "setView" + name, None)
                    for name in ("P", "X", "Y", "Z", "Z2", "XZ", "XZ2", "Machine")}
        dispatch["M"] = self.setViewMachine
        handler = dispatch.get(str(view or "P").upper(), self.setViewP)
        if handler is not None:
            handler()

    @Slot(bool)
    @Slot(object)
    def viewPerspective(self, perspective):
        self.setViewPersp() if perspective else self.setViewOrtho()

    @Slot()
    def zoomIn(self):
        self.rig.zoom(0.9)

    @Slot()
    def zoomOut(self):
        self.rig.zoom(1.1)

    # -- visibility and host-widget properties ----------------------------

    @Slot(bool)
    @Slot(object)
    def showGrid(self, show):
        self.plot_data.gridVisible = bool(show)

    @Slot(bool)
    @Slot(object)
    def showMachineBounds(self, show):
        show = bool(show)
        self.plot_data.machineBoundsVisible = show
        setting = getSetting("backplot.show-machine-bounds")
        if setting is not None and setting.value != show:
            setting.setValue(show)

    @Slot()
    def toggleMachineBounds(self):
        self.showMachineBounds(not bool(self.plot_data.machineBoundsVisible))

    @Slot(bool)
    @Slot(object)
    def showProgramBounds(self, show):
        show = bool(show)
        self.plot_data.programBoundsVisible = show
        setting = getSetting("backplot.show-program-bounds")
        if setting is not None and setting.value != show:
            setting.setValue(show)

    @Slot()
    def toggleProgramBounds(self):
        self.showProgramBounds(not bool(self.plot_data.programBoundsVisible))

    @Slot(bool)
    @Slot(object)
    def showMachineTicks(self, show):
        # Machine ticks are a VTK machine-actor feature; retained as state for
        # panels that still drive the setting.
        self._show_machine_ticks = bool(show)

    @Slot()
    def toggleMachineTicks(self):
        self.showMachineTicks(not self._show_machine_ticks)

    @Slot(bool)
    @Slot(object)
    def showMachineLabels(self, show):
        self._show_machine_labels = bool(show)

    @Slot()
    def toggleMachineLabels(self):
        self.showMachineLabels(not self._show_machine_labels)

    @Slot(bool)
    @Slot(object)
    def enable_panning(self, enabled):
        if hasattr(self, "navigation"):
            self.navigation.pan_mode = bool(enabled)
        if hasattr(self, "plot_data"):
            self.plot_data.panning = bool(enabled)

    @Slot(bool)
    def showSpindle(self, _show):
        self._show_spindle = bool(_show)
        if hasattr(self, "plot_data"):
            self.plot_data.toolVisible = bool(
                self._show_spindle and self._tool_shape.visible)

    @Slot(bool)
    def showMachine(self, show):
        self._show_machine = bool(show)
        if hasattr(self, "plot_data"):
            self.plot_data.machineVisible = self._show_machine
        if hasattr(self, "machine_parts"):
            self.machine_parts.set_enabled(self._show_machine)

    @Slot(bool)
    def showMultiColorPath(self, show):
        self._multitool_colors = bool(show)

    @Slot()
    def toggleMultiColorPath(self):
        self.showMultiColorPath(not self._multitool_colors)

    @Slot(bool)
    def showFPS(self, show):
        self._show_fps = bool(show)

    @Slot(bool)
    def showSurface(self, show):
        # Height-field surface is not rendered by the Qt Quick 3D stage yet.
        self._show_surface = bool(show)

    @Slot(bool)
    def alphaBlend(self, alpha):
        self._alpha_blend = bool(alpha)

    @Slot(bool)
    def enableMultiTouch(self, _enabled):
        pass

    @Slot(bool)
    def enableBreadcrumbs(self, _enabled):
        pass

    @Slot(bool)
    def setProgramViewWhenLoadingProgram(self, _enabled, view="p"):
        pass

    # -- VTK-parity methods (not all are meaningful to the Quick 3D scene) --

    @Slot()
    def reapplyNavHelperConfig(self):
        """Nav-helper camera gizmo is not rendered by this stage.

        The ``navHelper*`` properties are retained for panel compatibility, so
        this is a no-op kept for API parity with ``VTKBackPlot``.
        """
        return

    @Slot()
    def printView(self):
        """Save a PNG snapshot of the current plot view.

        VTK's ``printView`` is a no-op; this writes a real image next to the
        loaded program (or the temp dir) so the button has an effect.
        """
        if self._designer or not hasattr(self, "quick_widget"):
            return
        if not isValid(self.quick_widget):
            return
        try:
            image = self.quick_widget.grabFramebuffer()
        except (AttributeError, RuntimeError):
            LOG.debug("printView: framebuffer grab unavailable", exc_info=True)
            return
        directory = os.path.dirname(self._last_filename) if self._last_filename else ""
        if not directory or not os.path.isdir(directory):
            import tempfile
            directory = tempfile.gettempdir()
        path = os.path.join(directory, "backplot_view.png")
        try:
            image.save(path)
            LOG.info("printView: saved %s", path)
        except Exception:
            LOG.exception("printView: failed to save %s", path)

    @Slot(bool)
    def on_run_state_changed(self, running=False):
        self._running = bool(running)

    @Slot(object)
    def update_joints(self, joint_values):
        self._joints = joint_values
        if joint_values and hasattr(self, "machine_parts"):
            self.machine_parts.apply_joint_values(joint_values)

    @Slot(int)
    def update_active_wcs(self, wcs_index):
        self.update_g5x_index(wcs_index)

    @Slot(object)
    def update_tool(self, *_args):
        self._rebuild_tool()

    def tlo(self, _tlo):
        # Tool length offset is read live from status; kept for API parity.
        pass

    @Slot(int)
    @Slot(object)
    def motion_type(self, _value):
        pass

    def _role_property(role):
        def getter(self):
            return self._role_colors[role]
        def setter(self, color):
            self._role_colors[role] = QColor(color)
            if hasattr(self, "plot_data"):
                setattr(self.plot_data, role + "Color", QColor(color).name())
                if self._last_filename:
                    QTimer.singleShot(0, lambda: self.load_program(self._last_filename, force=True))
        return Property(QColor, getter, setter,
                        freset=reset_to(role + "Color", lambda self: QColor(self._default_role_colors[role])))

    traverseColor = _role_property("traverse")
    arcfeedColor = _role_property("arcfeed")
    feedColor = _role_property("feed")
    dwellColor = _role_property("dwell")
    userColor = _role_property("user")

    @Property(QColor, freset=reset_to("backgroundColor", lambda self: QColor("#101820")))
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self._background_color = QColor(color)
        if hasattr(self, "plot_data"):
            self.plot_data.backgroundColor = self._background_color.name()

    @Property(QColor, freset=reset_to("backgroundColor2", lambda self: QColor("#101820")))
    def backgroundColor2(self):
        return self._background_color2

    @backgroundColor2.setter
    def backgroundColor2(self, color):
        self._background_color2 = QColor(color)

    @Property(bool, freset=reset_to("enableProgramTicks", True))
    def enableProgramTicks(self):
        return self._enable_program_ticks

    @enableProgramTicks.setter
    def enableProgramTicks(self, value):
        self._enable_program_ticks = bool(value)

    @Property(bool, freset=reset_to("gridVisible", False))
    def gridVisible(self):
        return getattr(getattr(self, "plot_data", None), "gridVisible", False)

    @gridVisible.setter
    def gridVisible(self, value):
        self.showGrid(value)

    @Property(bool, freset=reset_to("machineBoundsVisible", True))
    def machineBoundsVisible(self):
        return getattr(getattr(self, "plot_data", None), "machineBoundsVisible", True)

    @machineBoundsVisible.setter
    def machineBoundsVisible(self, value):
        self.showMachineBounds(value)

    @Property(bool, freset=reset_to("programBoundsVisible", False))
    def programBoundsVisible(self):
        return getattr(getattr(self, "plot_data", None), "programBoundsVisible", False)

    @programBoundsVisible.setter
    def programBoundsVisible(self, value):
        self.showProgramBounds(value)

    @Property(QColor, freset=reset_to("navHelperXAxisColor", lambda self: QColor(255, 60, 60)))
    def navHelperXAxisColor(self):
        return self._nav_helper_x_axis_color

    @navHelperXAxisColor.setter
    def navHelperXAxisColor(self, color):
        self._nav_helper_x_axis_color = QColor(color)
        if hasattr(self, "plot_data"):
            self.plot_data.axesXColor = self._nav_helper_x_axis_color.name()

    @Property(QColor, freset=reset_to("navHelperYAxisColor", lambda self: QColor(60, 220, 60)))
    def navHelperYAxisColor(self):
        return self._nav_helper_y_axis_color

    @navHelperYAxisColor.setter
    def navHelperYAxisColor(self, color):
        self._nav_helper_y_axis_color = QColor(color)
        if hasattr(self, "plot_data"):
            self.plot_data.axesYColor = self._nav_helper_y_axis_color.name()

    @Property(QColor, freset=reset_to("navHelperZAxisColor", lambda self: QColor(80, 120, 255)))
    def navHelperZAxisColor(self):
        return self._nav_helper_z_axis_color

    @navHelperZAxisColor.setter
    def navHelperZAxisColor(self, color):
        self._nav_helper_z_axis_color = QColor(color)
        if hasattr(self, "plot_data"):
            self.plot_data.axesZColor = self._nav_helper_z_axis_color.name()

    @staticmethod
    def _nav_prop(qt_type, key):
        def getter(self):
            return self._nav_helper_props.get(key)

        def setter(self, value):
            self._nav_helper_props[key] = value

        def reset(self):
            self._nav_helper_props.pop(key, None)

        return Property(qt_type, getter, setter, freset=reset)

    # Shared with VTKBackPlot's camera-orientation helper. Values are retained
    # for panels and helper widgets that configure these through Designer.
    navHelperEnabled = _nav_prop(bool, "enabled")
    navHelperAnimate = _nav_prop(bool, "animate")
    navHelperShouldResetCamera = _nav_prop(bool, "should_reset_camera")
    navHelperKeyActivation = _nav_prop(str, "key_activation")
    navHelperAnchor = _nav_prop(str, "anchor")
    navHelperPadding = _nav_prop(QSize, "padding")
    navHelperSize = _nav_prop(QSize, "size")
    navHelperTotalLength = _nav_prop(float, "total_length")
    navHelperHandleSize = _nav_prop(float, "handle_size")
    navHelperNormalizedHandleDia = _nav_prop(float, "normalized_handle_dia")
    navHelperContainerVisibility = _nav_prop(bool, "container_visibility")
    navHelperDragable = _nav_prop(bool, "dragable")
    navHelperPickable = _nav_prop(bool, "pickable")
    navHelperShaftResolution = _nav_prop(int, "shaft_resolution")
    navHelperHandleResolution = _nav_prop(int, "handle_resolution")
    navHelperHandleVisibility = _nav_prop(bool, "handle_visibility")
    navHelperLabelsVisible = _nav_prop(bool, "labels_visible")
    navHelperLabels = _nav_prop("QStringList", "labels")
    navHelperAxisColor = _nav_prop(QColor, "axis_color")
    navHelperContainerCircumferentialResolution = _nav_prop(
        int, "container_circumferential_resolution")
    navHelperContainerRadialResolution = _nav_prop(
        int, "container_radial_resolution")
    navHelperAnimatorTotalFrames = _nav_prop(int, "animator_total_frames")
    navHelperProcessEvents = _nav_prop(bool, "process_events")
    navHelperManagesCursor = _nav_prop(bool, "manages_cursor")
    navHelperPriority = _nav_prop(float, "priority")
