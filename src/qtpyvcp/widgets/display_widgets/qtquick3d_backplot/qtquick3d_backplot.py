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
from qtpyvcp.widgets.display_widgets.backplot_common.linuxcnc_datasource import (
    LinuxCncDataSource,
)

from . import machine, tool
from .geometry import (
    Quick3DPlotData,
    map_point_from_quick3d,
    map_points_to_quick3d,
    map_vector_to_quick3d,
)
from .navigation import BackplotNavigation
from .paths import (
    ROLE_NAMES,
    PathGroupModel,
    ray_segment_distances,
    transform_point,
)
from .wcs_origins import WCS_LABELS, SceneLabelModel, WcsOriginModel

LOG = logger.getLogger(__name__)
IN_DESIGNER = os.getenv("DESIGNER", "").lower() not in ("", "0", "false", "no")

# Extra radius around the machine/program bounds, as a fraction of the bounds
# half-diagonal, so the camera fit and clip planes cover space beyond the
# machine envelope. Scale-independent, so it works for inch and metric.
BOUNDS_MARGIN = 0.6
# Used to fit the view before any machine or program bounds are available.
DEFAULT_BOUNDS = (-10.0, 10.0, -10.0, 10.0, -10.0, 10.0)
# Click tolerance as a fraction of the scene half-diagonal.
PICK_TOLERANCE_FRACTION = 0.005
# Cap for line highlighting, so selecting a line used many times cannot upload
# an unbounded buffer.
MAX_HIGHLIGHT_SEGMENTS = 20000
# Number of work coordinate systems (G54 .. G59.3).
NUMBER_OF_WCS = len(WCS_LABELS)
# Work-offset origin marker size as a fraction of the scene half-diagonal.
WCS_ORIGIN_FRACTION = 0.02
# Cube-axis tick length as a fraction of the longest bounds span.
TICK_FRACTION = 0.02
# Live position sampling is independent of the (possibly slow) status plugin
# cycle, so the trail is not limited to one segment per status poll.
LIVE_POSITION_INTERVAL_MS = 16
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
        self._up = self._orthogonalize(
            self._up, (-self._offset).normalized())
        self._apply()

    def set_scene_radius(self, radius):
        try:
            radius = float(radius)
        except (TypeError, ValueError):
            return
        if radius <= 0.0 or radius == self._scene_radius:
            return
        self._scene_radius = radius
        self._apply()

    @property
    def scene_radius(self):
        """Half-diagonal of the scene, or ``None`` before a fit."""
        return self._scene_radius

    def _clip_planes(self):
        eye = max(self._offset.length(), 1e-6)
        radius = self._scene_radius if self._scene_radius else max(eye * 0.5, 1.0)
        # Generous window: the near plane is pulled well in front of the scene
        # and the far plane well behind it, so orbiting/zooming never clips the
        # front or back of the arm.
        near = eye - radius * 2.5
        if near <= 0.0 or near > eye * 0.5:
            near = max(radius * 1e-3, eye * 1e-3, 1e-4)
        far = max(eye + radius * 10.0, near + radius * 10.0,
                  eye * 8.0, near * 100.0)
        return near, far

    def _apply(self):
        position = self._center + self._offset
        orientation = QQuaternion.fromDirection(self._offset, self._up)
        clip_near, clip_far = self._clip_planes()
        try:
            cameras = self._camera_provider()
        except RuntimeError:
            cameras = ()
        applied = False
        for camera in cameras:
            if camera is None or not isValid(camera):
                continue
            try:
                camera.setProperty("position", position)
                camera.setProperty("rotation", orientation)
                camera.setProperty("clipNear", clip_near)
                camera.setProperty("clipFar", clip_far)
                applied = True
            except RuntimeError:
                # Qt Quick may replace its QML root while the editor reloads a
                # scene; the next camera update will reacquire its new objects.
                continue
        if applied:
            # 2D overlay labels project through View3D.mapFrom3DScene, so they
            # need to know that the camera moved.
            self.data.touch_camera()

    def set_perspective(self):
        self._orthographic = False
        self.data.perspective = True
        self._apply()
        # QML switches the active camera on the next event-loop turn; nudge the
        # overlay projection once more after that.
        QTimer.singleShot(0, self.data.touch_camera)

    def set_orthographic(self):
        self._orthographic = True
        self.data.perspective = False
        self._apply()
        QTimer.singleShot(0, self.data.touch_camera)

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
            mapped_up = map_vector_to_quick3d(up).normalized()
            # Keep the Python-side up vector perpendicular to the view; the
            # camera quaternion orthogonalizes internally, but orbit/pan reuse
            # this vector and a tilted one would slowly roll the view.
            self._up = self._orthogonalize(
                mapped_up, -QVector3D(*map(float, mapped_direction)))
        self._offset = QVector3D(*map(float, mapped_direction)) * float(
            distance if distance is not None else max(self._offset.length(), 1.0))
        self._apply()

    @staticmethod
    def _orthogonalize(up, forward):
        """Project *up* perpendicular to *forward*, keeping a stable fallback."""
        projected = up - forward * QVector3D.dotProduct(up, forward)
        if projected.lengthSquared() < 1e-10:
            fallback = QVector3D(0.0, 0.0, 1.0)
            projected = fallback - forward * QVector3D.dotProduct(fallback, forward)
        if projected.lengthSquared() < 1e-10:
            return up
        return projected.normalized()

    def set_view(self, name, center, distance=None):
        direction, up = VIEW_DIRECTIONS.get(str(name or "P").upper(), VIEW_DIRECTIONS["P"])
        self.look_at(center, direction, up, distance)

    def fit_bounds(self, bounds, aspect=1.0, padding=1.1, distance=None):
        if bounds is None:
            bounds = DEFAULT_BOUNDS
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
            try:
                viewport_width, viewport_height = self._viewport_size()
            except (TypeError, ValueError, RuntimeError, AttributeError):
                viewport_width, viewport_height = 1, 1
            span = max(float(np.max(extent)), 1e-6) * max(float(padding), 1.0)
            # Qt Quick 3D magnification is pixels per world unit: the visible
            # world width is viewport_width / magnification. Pick the largest
            # magnification that still fits `span` on the shorter viewport axis.
            magnification = min(max(viewport_width, 1),
                                max(viewport_height, 1)) / span
            self.data.orthoMagnification = magnification
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
        self._up = self._orthogonalize(self._up, (-self._offset).normalized())
        self._apply()

    def pan(self, dx_pixels, dy_pixels, viewport_width, viewport_height):
        height = max(float(viewport_height), 1.0)
        forward = (-self._offset).normalized()
        right = QVector3D.crossProduct(forward, self._up).normalized()
        if right.lengthSquared() < 1e-12:
            return
        true_up = QVector3D.crossProduct(right, forward).normalized()
        if self._orthographic:
            # Magnification is pixels per world unit, so the visible height is
            # viewport_height / magnification.
            world_height = height / max(self.data.orthoMagnification, 1e-9)
        else:
            world_height = 2.0 * self._offset.length() * math.tan(math.radians(self._fov / 2.0))
        delta = right * (-float(dx_pixels) * world_height / height)
        delta += true_up * (float(dy_pixels) * world_height / height)
        self._center += delta
        self._apply()


class Qt3D0(QWidget, VCPWidget):
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
        self._g92_offset = (0.0, 0.0, 0.0)
        # Floating (G91-only) programs have no meaningful WCS origin; their
        # shape is anchored to the machine instead.
        self._floating_wcs = set()
        self._anchor_offset = None
        self._anchor_latched = False
        self._program_running = False
        self._highlighted_lines = []
        self._breadcrumbs_enabled = True
        self._last_breadcrumb_motion_line = None
        self._program_view_on_load = True
        self._program_view_name = "p"
        self._last_wcs_origin_points = None
        self._pending_initial_fit = True
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

        # Create the QQuickWidget first so it is destroyed before plot_data /
        # path_groups / machine_parts. QObject deletes children in creation
        # order; if those died first, every QML binding would re-evaluate
        # against a null object at teardown.
        self.quick_widget = QQuickWidget(self)
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.quick_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.plot_data = Quick3DPlotData(self)
        self.path_groups = PathGroupModel(self)
        self.wcs_origins = WcsOriginModel(self)
        self.machine_tick_labels = SceneLabelModel(self)
        self.program_tick_labels = SceneLabelModel(self)
        self._apply_plot_colors()
        self.machine_parts = machine.MachinePartsModel(self)
        context = self.quick_widget.rootContext()
        context.setContextProperty("plotData", self.plot_data)
        context.setContextProperty("pathGroups", self.path_groups)
        context.setContextProperty("machineParts", self.machine_parts)
        context.setContextProperty("wcsOrigins", self.wcs_origins)
        context.setContextProperty("machineTickLabels", self.machine_tick_labels)
        context.setContextProperty("programTickLabels", self.program_tick_labels)
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
        self.plot_data.pinchZoomed.connect(self._on_pinch_zoom)
        self.plot_data.pinchPanned.connect(self._on_pinch_pan)
        self.plot_data.pinchRotated.connect(self._on_pinch_rotate)
        self.plot_data.viewRequested.connect(self._on_view_requested)
        self.plot_data.cameraChanged.connect(self._sync_nav_helper)

        self.datasource = LinuxCncDataSource()
        self.config_dir = self._resolve_config_dir()
        self._stat = linuxcnc.stat()
        self._use_actual_position = True
        try:
            self._use_actual_position = bool(
                self.datasource._info.getPositionFeedback())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            self._use_actual_position = True
        self._position_timer = QTimer(self)
        self._position_timer.setInterval(LIVE_POSITION_INTERVAL_MS)
        self._position_timer.timeout.connect(self._poll_live_position)
        self._position_timer.start()
        self._is_lathe = self.datasource.isMachineLathe()
        self._seed_g92_state()
        self._seed_wcs_state()
        self._initialize_geometry()
        self._wire_signals()
        self._connect_settings()
        self.setViewMachine()
        self._sync_nav_helper()
        QTimer.singleShot(0, self._load_current_program)
        QTimer.singleShot(500, self._load_current_program)
        LOG.info("Qt Quick 3D backplot initialized")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Qt Quick 3D orthographic magnification is pixels per world unit, so a
        # fit computed while the widget still had its default size is wrong.
        # Refit once, on the first real resize, before the user can interact.
        if self._pending_initial_fit and not self._designer:
            self._pending_initial_fit = False
            QTimer.singleShot(0, self._fit_initial_view)

    def _fit_initial_view(self):
        if not isValid(self) or not hasattr(self, "rig"):
            return
        if self._program_bounds is not None:
            self.setViewProgram("p")
        else:
            self.setViewMachine()

    def _resolve_config_dir(self):
        """Config directory used to resolve MACHINE_PARTS and model paths."""
        ini_path = os.getenv("INI_FILE_NAME")
        if ini_path:
            return os.path.dirname(ini_path)
        return getattr(self.datasource, "config_dir", None)

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
        self._rebuild_wcs_origins()

    # -- machine parts (MACHINE_PARTS) --------------------------------------

    def _build_machine_parts(self):
        ini = getattr(self.datasource, "_inifile", None)
        if ini is None:
            return
        parts_file = ini.find("VTK", "MACHINE_PARTS")
        if not parts_file:
            return
        # Part model paths in the YAML are relative to the config directory
        # (MACHINE_PARTS lives under <config>/models), matching the config
        # convention where the config dir is the working directory.
        config_dir = self.config_dir
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

        # The spindle comes from [VTK] SPINDLE, not the machine-parts YAML.
        spindle_file = ini.find("VTK", "SPINDLE")
        skip_ids = ("spindle",) if spindle_file else ()
        self.machine_parts.load(data, config_dir=config_dir, skip_ids=skip_ids)

        if spindle_file:
            resolved = spindle_file
            if not os.path.isabs(resolved) and config_dir:
                resolved = os.path.normpath(os.path.join(config_dir, resolved))
            geometry = self._load_model_geometry(resolved)
            if geometry is not None:
                self.machine_parts.set_spindle(geometry)
                self.machine_parts.set_spindle_visible(self._show_spindle)
            else:
                LOG.warning("Quick 3D [VTK] SPINDLE unavailable: %s", resolved)
        self._update_clip_reference()

    @staticmethod
    def _load_model_geometry(path):
        """Load an STL/glTF model file into a Quick 3D geometry, or None."""
        if not path or not os.path.isfile(path):
            return None
        lower = str(path).lower()
        try:
            if lower.endswith(".stl"):
                return machine._stl_geometry(path)
            if lower.endswith((".glb", ".gltf")):
                return machine._gltf_geometry(path)
        except (OSError, ValueError, KeyError, IndexError):
            LOG.exception("failed to load model geometry: %s", path)
        LOG.warning("Unsupported model format for Qt Quick 3D: %s", path)
        return None

    def _apply_joint_feedback(self):
        if self.machine_parts.rowCount() == 0:
            return
        status = getattr(self.datasource, "_status", None)
        stat = getattr(status, "stat", None)
        joints = getattr(stat, "joint_actual_position", None)
        if not joints:
            return
        snapshot = tuple(float(value) for value in joints)
        if snapshot == self._joints:
            return
        self._joints = snapshot
        self.machine_parts.apply_joint_values(snapshot)
        self._update_clip_reference()

    # -- picking / highlighting --------------------------------------------

    def _clear_highlight(self):
        self.plot_data.highlight.replace(np.zeros((0, 3), np.float32))

    def _pick_tolerance(self):
        """World-space distance within which a click counts as a hit."""
        radius = getattr(self.rig, "scene_radius", None)
        if not radius:
            return 1e-3
        return max(float(radius) * PICK_TOLERANCE_FRACTION, 1e-6)

    def _set_highlight_segments(self, starts, ends):
        starts = np.asarray(starts, dtype=np.float32).reshape(-1, 3)
        ends = np.asarray(ends, dtype=np.float32).reshape(-1, 3)
        count = min(starts.shape[0], ends.shape[0], MAX_HIGHLIGHT_SEGMENTS)
        if count == 0:
            self._clear_highlight()
            return
        points = np.empty((count * 2, 3), dtype=np.float32)
        points[0::2] = starts[:count]
        points[1::2] = ends[:count]
        self.plot_data.highlight.replace(map_points_to_quick3d(points))

    def _update_highlight_for_lines(self, lines):
        """Highlight every segment belonging to the given program lines."""
        self._highlighted_lines = [int(value) for value in lines if int(value) >= 0]
        starts, ends = self.path_groups.segments_for_lines(self._highlighted_lines)
        self._set_highlight_segments(starts, ends)

    def _on_picked(self, near, far):
        """Select the path segment nearest the click ray.

        QML unprojects the click into a scene-space ray, so this does not
        depend on Qt Quick 3D supporting picking for line primitives.
        Candidates within a small world-space tolerance are ranked by distance
        along the ray, so the segment in front wins when several lines overlap
        on screen.
        """
        if self._geometry is None or not self.path_groups.rows():
            return
        origin = map_point_from_quick3d((near.x(), near.y(), near.z()))
        target = map_point_from_quick3d((far.x(), far.y(), far.z()))
        direction = target - origin
        length = float(np.linalg.norm(direction))
        if length < 1e-9:
            return
        direction /= length

        tolerance = self._pick_tolerance()
        best = None
        for row in self.path_groups.rows():
            local_origin = np.asarray(row.local_point(origin), dtype=np.float64)
            local_far = np.asarray(row.local_point(target), dtype=np.float64)
            local_direction = local_far - local_origin
            local_length = float(np.linalg.norm(local_direction))
            if local_length < 1e-9:
                continue
            local_direction /= local_length
            distances, ray_t = ray_segment_distances(
                local_origin, local_direction, row.starts, row.ends)
            if distances.size == 0:
                continue
            index = int(np.argmin(distances))
            if distances[index] > tolerance:
                continue
            candidate = (float(ray_t[index]), float(distances[index]), row, index)
            if best is None or candidate[0] < best[0]:
                best = candidate

        if best is None:
            return
        _, _, row, index = best
        line_number = int(row.line_numbers[index]) if index < row.line_numbers.size else -1
        if line_number >= 0:
            self._update_highlight_for_lines([line_number])
            self.programLineSelected.emit(line_number)
            self.programLinesSelected.emit([line_number])
        else:
            self._highlighted_lines = []
            self._set_highlight_segments(
                [row.world_point(row.starts[index])],
                [row.world_point(row.ends[index])])

    # -- active tool body ---------------------------------------------------

    def _current_tool_number(self):
        stat = getattr(getattr(self.datasource, "_status", None), "stat", None)
        try:
            return int(getattr(stat, "tool_in_spindle", 0) or 0)
        except (TypeError, ValueError):
            return 0

    def _resolve_tool_mesh(self, tool_entry, lathe):
        """Return ``(geometry, shape, kind)`` for an insert or per-tool model.

        Lathe tools prefer the DB insert silhouette, matching the tool-table
        editor. Mill tools can supply an STL/glTF path on their table row.
        ``None`` keeps the generic cylinder/cone primitive.
        """
        if lathe:
            record = tool.resolve_insert_record(
                self.datasource, self._tool_number, tool_entry)
            if record is not None:
                polygon = tool.insert_polygon(record, tool_entry)
                mesh = tool.insert_mesh(polygon) if polygon else None
                if mesh is not None:
                    vertices, normals = mesh
                    geometry = machine._geometry_from_arrays(
                        vertices, normals=normals)
                    if geometry is not None:
                        geometry.setObjectName("backplot_tool_insert")
                        xs = [point[0] for point in polygon]
                        zs = [point[1] for point in polygon]
                        radius = max(max(abs(value) for value in xs), 1e-3)
                        length = max(max(zs) - min(zs), 1e-3)
                        shape = tool.ToolShape(
                            kind="insert", radius=radius, length=length,
                            tool_number=self._tool_number)
                        LOG.debug(
                            "Qt Quick 3D lathe insert: T%s family=%s "
                            "points=%d radius=%.4f length=%.4f",
                            self._tool_number, record.get('type'),
                            len(polygon), radius, length)
                        return geometry, shape, "insert"

        path = tool.resolve_tool_model_path(
            self.datasource, tool_entry, self._tool_number)
        if path:
            geometry = self._load_model_geometry(path)
            if geometry is not None:
                geometry.setObjectName("backplot_tool_model")
                shape = tool.ToolShape(
                    kind="mesh", radius=1.0, length=1.0,
                    tool_number=self._tool_number)
                LOG.debug("Qt Quick 3D per-tool model: T%s %s",
                          self._tool_number, path)
                return geometry, shape, "mesh"
        return None

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

        lathe = _flag("isMachineLathe")
        shape = tool.tool_shape(
            tool_table,
            self._tool_number,
            metric=_flag("isMachineMetric"),
            lathe=lathe,
            robot=False,
            foam=_flag("isMachineFoam"),
            jet=_flag("isMachineJet"),
        )
        tool_entry = tool.resolve_tool_entry(tool_table, self._tool_number)
        mesh = self._resolve_tool_mesh(tool_entry, lathe)
        if mesh is not None:
            geometry, shape, mesh_kind = mesh
            self.plot_data.toolMesh = geometry
            if mesh_kind == "insert":
                shape.kind = "insert"
        else:
            self.plot_data.toolMesh = None

        self._tool_shape = shape
        self.plot_data.toolKind = shape.kind
        self.plot_data.toolColor = "#d2d2d7"
        LOG.debug(
            "Qt Quick 3D tool: number=%s entries=%s kind=%s visible=%s "
            "spindle_model=%s radius=%.4f length=%.4f",
            self._tool_number, len(tool_table), shape.kind, shape.visible,
            self._show_spindle, shape.radius, shape.length)
        if shape.kind == "none":
            LOG.info(
                "Qt Quick 3D tool body not drawn (foam=%s jet=%s); use a "
                "machine-parts model for this machine type",
                _flag("isMachineFoam"), _flag("isMachineJet"))
        if shape.visible:
            # Built-in primitives are 100 units tall with a 100-unit diameter.
            self.plot_data.toolScale = QVector3D(
                shape.radius / 50.0, shape.length / 100.0, shape.radius / 50.0)
        # The cutter bit is its own object; backplot.show-spindle only
        # controls the [VTK] SPINDLE machine model.
        self.plot_data.toolVisible = bool(shape.visible)
        self._update_tool_transform()

    def _current_tool_offset(self):
        # Prefer the high-rate polled stat object so G43/G43.1 changes are
        # picked up at the same rate as the trail/tool position.
        stat = getattr(self, "_stat", None)
        if stat is None or not hasattr(stat, "tool_offset"):
            stat = getattr(getattr(self.datasource, "_status", None), "stat", None)
        try:
            values = getattr(stat, "tool_offset", None)
            return tuple(float(v) for v in values)
        except (TypeError, ValueError):
            return (0.0,) * 9

    def _tool_tip_position(self):
        """Live machine position adjusted by the active G43/G43.1 offset.

        LinuxCNC keeps ``stat.tool_offset`` at the offset currently in effect:
        G43/G43.1 set it, and G49 clears it.  The trail and the cutter bit must
        use this tip position, while the spindle model stays at the raw machine
        position (the tool top).
        """
        x, y, z = self._position
        tlo = self._current_tool_offset()
        return (
            x - (tlo[0] if len(tlo) > 0 else 0.0),
            y - (tlo[1] if len(tlo) > 1 else 0.0),
            z - (tlo[2] if len(tlo) > 2 else 0.0),
        )

    def _update_tool_transform(self):
        # The spindle model is the head, not the cutter: keep it at the live
        # machine position even when no tool bit is loaded. Robot/DH assemblies
        # position the spindle from their tool frame instead.
        if hasattr(self, "machine_parts"):
            self.machine_parts.set_spindle_position(self._position)

        shape = self._tool_shape
        if not shape.visible:
            return
        tip = self._tool_tip_position()
        offset = tool.tool_body_offset(shape)
        self.plot_data.toolPosition = map_vector_to_quick3d(
            (tip[0] + offset[0], tip[1] + offset[1], tip[2] + offset[2]))

    def _apply_plot_colors(self):
        if not hasattr(self, "plot_data"):
            return
        self.plot_data.backgroundColor = self._background_color.name()
        self.plot_data.backgroundColor2 = self._background_color2.name()
        for role in ROLE_NAMES:
            setattr(self.plot_data, role + "Color", self._role_colors[role].name())
        if hasattr(self, "path_groups"):
            self.path_groups.set_colors(self._role_color_map())

    def _role_color_map(self):
        return {role: self._role_colors[role].name() for role in ROLE_NAMES}

    def _wcs_transform(self, wcs_index):
        """WCS placement for a path row: ``(x, y, z, rotation_degrees)``.

        Floating (G91-only) paths have no meaningful work offset; they are
        anchored to the machine position instead.
        """
        if wcs_index in self._floating_wcs:
            anchor = self._anchor_offset or (0.0, 0.0, 0.0)
            return float(anchor[0]), float(anchor[1]), float(anchor[2]), 0.0
        return self._wcs_offsets(wcs_index)

    def _rebuild_program_geometry(self):
        self._highlighted_lines = []
        self.path_groups.build(self._geometry, self._role_color_map(),
                               self._wcs_transform)
        self._program_bounds = self.path_groups.world_bounds()
        self._rebuild_program_bounds()
        self._rebuild_offset_transitions()
        self._clear_highlight()
        self._update_clip_reference()
        self._rebuild_wcs_origins()

    def _rebuild_offset_transitions(self):
        """Draw the link between the end of one WCS path and the next."""
        points = []
        if self._geometry is not None:
            for transition in self._geometry.offset_transitions:
                from_transform = self._wcs_transform(transition.from_wcs)
                to_transform = self._wcs_transform(transition.to_wcs)
                start = transform_point(transition.from_end, *from_transform)
                end = transform_point(transition.to_start, *to_transform)
                # Elbow: from -> same Z as the start -> to.
                elbow = (end[0], end[1], start[2])
                points.extend((start, elbow, elbow, end))
        self.plot_data.transitions.replace(
            map_points_to_quick3d(points) if points
            else np.zeros((0, 3), dtype=np.float32))

    def _wcs_origin_indices(self):
        """Work offsets that should show an origin marker.

        Only offsets that the loaded program actually uses are shown, so an
        empty file (or no file) draws no part origins. Configured but unused
        offsets are intentionally ignored: they are not part of the current
        job. Floating (G91-only) paths are anchored to the machine rather than
        to a work offset, so they are skipped.
        """
        if self._geometry is None:
            return []

        needed = set()
        for index, path in self._geometry.paths.items():
            try:
                index = int(index)
            except (TypeError, ValueError):
                continue
            if (0 <= index < NUMBER_OF_WCS and not path.is_empty
                    and index not in self._floating_wcs):
                needed.add(index)
        return sorted(needed)

    def _rebuild_wcs_origins(self):
        """Draw a small origin glyph and a G54..G59.3 label at each WCS origin."""
        radius = getattr(self.rig, "scene_radius", None) or 10.0
        length = max(float(radius) * WCS_ORIGIN_FRACTION, 1e-3)
        half = length * 0.35
        points = []
        rows = []
        for index in self._wcs_origin_indices():
            try:
                x, y, z, rotation = self._wcs_transform(index)
            except (AttributeError, RuntimeError, TypeError, ValueError):
                continue
            radians = math.radians(rotation)
            cosine, sine = math.cos(radians), math.sin(radians)

            # A small square in the WCS XY plane (so the work-offset rotation
            # is visible) plus a vertical stem.
            corners = []
            for local_x, local_y in ((-half, -half), (half, -half),
                                     (half, half), (-half, half)):
                corners.append((
                    x + cosine * local_x - sine * local_y,
                    y + sine * local_x + cosine * local_y,
                    z,
                ))
            for corner, next_corner in zip(corners, corners[1:] + corners[:1]):
                points.extend((corner, next_corner))
            points.extend(((x, y, z), (x, y, z + length)))

            rows.append((WCS_LABELS[index],
                         map_vector_to_quick3d((x, y, z)), index))

        scene_points = (map_points_to_quick3d(points) if points
                        else np.zeros((0, 3), dtype=np.float32))
        if (rows == self.wcs_origins.rows()
                and self._last_wcs_origin_points is not None
                and np.array_equal(scene_points, self._last_wcs_origin_points)):
            return
        self._last_wcs_origin_points = scene_points
        self.plot_data.origins.replace(scene_points)
        self.wcs_origins.set_rows(rows)

    def _refresh_path_transforms(self):
        """Apply new WCS/anchor values without re-uploading vertex data."""
        if self.path_groups.update_transforms(self._wcs_transform):
            self._program_bounds = self.path_groups.world_bounds()
            self._rebuild_program_bounds()
            self._rebuild_offset_transitions()
            self._update_clip_reference()
        if self._highlighted_lines:
            self._update_highlight_for_lines(self._highlighted_lines)
        self._rebuild_wcs_origins()

    def _seed_g92_state(self):
        try:
            self._g92_offset = tuple(
                float(value) for value in self.datasource.getG92_offset()[:3])
        except (AttributeError, RuntimeError, TypeError, ValueError):
            self._g92_offset = (0.0, 0.0, 0.0)

    def _compute_anchor_offset(self):
        """Machine position with any baked-in G92 removed, in machine units."""
        try:
            machine_position = self.datasource.getMachinePosition()
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return None
        if machine_position is None:
            return None
        values = list(machine_position[:3])
        while len(values) < 3:
            values.append(0.0)
        return tuple(
            float(values[index]) - float(self._g92_offset[index])
            for index in range(3)
        )

    def _is_program_running(self):
        checker = getattr(self.datasource, "isProgramRunning", None)
        if not callable(checker):
            return False
        try:
            return bool(checker())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return False

    def _update_floating_anchor(self):
        """Track or latch the anchor for floating (G91-only) programs."""
        if not self._floating_wcs:
            return
        anchor = self._compute_anchor_offset()
        if anchor is None:
            return

        running = self._is_program_running()
        if running != self._program_running:
            self._program_running = running
            self._anchor_latched = running

        if self._anchor_latched:
            return
        if anchor == self._anchor_offset:
            return
        self._anchor_offset = anchor
        self._refresh_path_transforms()

    @staticmethod
    def _nice_step(raw):
        if raw <= 0:
            return 1.0
        exponent = math.floor(math.log10(raw))
        base = raw / (10 ** exponent)
        for nice in (1.0, 2.0, 5.0, 10.0):
            if base <= nice:
                return nice * (10 ** exponent)
        return 10.0 * (10 ** exponent)

    @classmethod
    def _tick_values(cls, low, high, step):
        if step <= 0:
            return [low, high]
        values = []
        value = math.ceil(low / step) * step
        while value <= high + 1e-9:
            values.append(value)
            value += step
        return values or [low, high]

    @classmethod
    def _build_cube_ticks(cls, bounds):
        """Return ``(tick_line_points, label_rows)`` for a bounds box."""
        if bounds is None:
            return [], []
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        span = max(xmax - xmin, ymax - ymin, zmax - zmin, 1e-6)
        tick = max(span * TICK_FRACTION, 1e-6)
        points = []

        for value in cls._tick_values(
                xmin, xmax, cls._nice_step(max(xmax - xmin, 1e-6) / 10.0)):
            points.extend(((value, ymin, zmin), (value, ymin + tick, zmin)))
        for value in cls._tick_values(
                ymin, ymax, cls._nice_step(max(ymax - ymin, 1e-6) / 10.0)):
            points.extend(((xmin, value, zmin), (xmin + tick, value, zmin)))
        for value in cls._tick_values(
                zmin, zmax, cls._nice_step(max(zmax - zmin, 1e-6) / 10.0)):
            points.extend(((xmin, ymin, value), (xmin + tick, ymin, value)))

        labels = []
        for axis, values, anchor in (
            ('x', tuple(dict.fromkeys((xmin, (xmin + xmax) / 2.0, xmax))),
             (0.0, ymin, zmin)),
            ('y', tuple(dict.fromkeys((ymin, (ymin + ymax) / 2.0, ymax))),
             (xmin, 0.0, zmin)),
            ('z', tuple(dict.fromkeys((zmin, (zmin + zmax) / 2.0, zmax))),
             (xmin, ymin, 0.0)),
        ):
            axis_index = 'xyz'.index(axis)
            for value in values:
                position = list(anchor)
                position[axis_index] = value
                labels.append((f"{value:.3f}",
                               map_vector_to_quick3d(position), -1))
        return points, labels

    def _rebuild_machine_ticks(self):
        bounds = self._machine_box_bounds()
        points, labels = self._build_cube_ticks(bounds)
        self.plot_data.machineTicks.replace(
            map_points_to_quick3d(points) if points
            else np.zeros((0, 3), np.float32))
        self.machine_tick_labels.set_rows(labels)

    def _rebuild_program_ticks(self):
        points, labels = self._build_cube_ticks(self._program_bounds)
        self.plot_data.programTicks.replace(
            map_points_to_quick3d(points) if points
            else np.zeros((0, 3), np.float32))
        self.program_tick_labels.set_rows(labels)

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
        boxes = [b for b in (self._program_bounds, self._machine_bounds) if b]
        # The arm/tool can reach outside the Cartesian limits, so include the
        # machine-parts extent or the clip planes eat it front and back.
        if getattr(self, "machine_parts", None) is not None:
            world_bounds = self.machine_parts.world_bounds()
            if world_bounds is not None:
                low, high = world_bounds
                boxes.append((low[0], high[0], low[1], high[1], low[2], high[2]))
        if not boxes:
            return
        minimum = [min(box[i] for box in boxes) for i in (0, 2, 4)]
        maximum = [max(box[i] for box in boxes) for i in (1, 3, 5)]
        diagonal = math.sqrt(sum(
            (maximum[i] - minimum[i]) ** 2 for i in range(3)))
        half = diagonal * 0.5
        self.rig.set_scene_radius(max(half * (1.0 + BOUNDS_MARGIN), 0.5))

    def _rebuild_program_bounds(self):
        bounds = self._program_bounds
        self.plot_data.programBounds.replace(
            map_points_to_quick3d(_box_lines(bounds)) if bounds else np.zeros((0, 3), np.float32))
        self._rebuild_program_ticks()

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
        # Live position is polled by _position_timer at a higher rate than the
        # status plugin (75 ms in some configs). Connecting positionChanged
        # here would insert stale 75 ms samples between the high-rate polls.
        ds.g5xOffsetChanged.connect(self.update_g5x_offset)
        ds.g92OffsetChanged.connect(self.update_g92_offset)
        ds.g5xIndexChanged.connect(self.update_g5x_index)
        ds.rotationXYChanged.connect(self.update_rotation_xy)
        ds.offsetTableChanged.connect(self.on_offset_table_changed)
        ds.toolInSpindleChanged.connect(self.update_tool_number)
        ds.toolTableChanged.connect(self.update_tool_table)
        ds.toolOffsetChanged.connect(self.update_tool_table)

        # Optional signals: keep the widget usable with older/minimal
        # datasources (and with the fakes used by the tests).
        for name, slot in (
            ("runStateChanged", self.on_run_state_changed),
            ("activeOffsetChanged", self.update_active_wcs),
            ("motionTypeChanged", self.motion_type),
        ):
            signal = getattr(ds, name, None)
            if signal is not None and hasattr(signal, "connect"):
                signal.connect(slot)

        # Tool-table plugin edits (remark/comment-only changes may not produce a
        # LinuxCNC status event).
        tooltable = getattr(ds, "_tooltable", None)
        plugin_signal = getattr(tooltable, "tool_table_changed", None)
        if plugin_signal is not None and hasattr(plugin_signal, "connect"):
            plugin_signal.connect(self.update_tool_table)

        self._bind_line_highlight_channels()

        try:
            self._stat.poll()
            # Place the tool at the current machine position before the first
            # motion update, otherwise it sits at the machine origin and can be
            # outside the fitted program view.
            attribute = ("actual_position" if self._use_actual_position
                         else "position")
            position = getattr(self._stat, attribute, None)
            if position is None:
                position = self._stat.position
            self.update_position(tuple(position))
        except Exception:
            LOG.debug("LinuxCNC status not ready during Qt Quick 3D startup", exc_info=True)
        self._seed_wcs_state()

    def _bind_line_highlight_channels(self):
        """Follow the G-code editor's selected line(s)."""
        status = getattr(self.datasource, "_status", None)
        for name, handler in (
            ("selected_program_line", self._on_selected_program_line),
            ("selected_program_lines", self._on_selected_program_lines),
        ):
            channel = getattr(status, name, None)
            notify = getattr(channel, "notify", None)
            if not callable(notify):
                continue
            try:
                notify(handler)
            except Exception:
                LOG.debug("Unable to watch status channel %s", name, exc_info=True)

    @staticmethod
    def _normalize_lines(value):
        if isinstance(value, (list, tuple, set)):
            values = list(value)
        elif value is None:
            values = []
        else:
            values = [value]
        normalized = []
        for item in values:
            try:
                normalized.append(int(item))
            except (TypeError, ValueError):
                continue
        return normalized

    def _on_selected_program_line(self, line):
        self._update_highlight_for_lines(self._normalize_lines(line))

    def _on_selected_program_lines(self, lines):
        self._update_highlight_for_lines(self._normalize_lines(lines))

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
        connectSetting("backplot.show-machine-ticks", self.showMachineTicks)
        connectSetting("backplot.show-machine-labels", self.showMachineLabels)
        connectSetting("backplot.show-machine", self.showMachine)
        connectSetting("backplot.show-wcs-origins", self.showWcsOrigins)
        connectSetting("backplot.show-spindle", self.showSpindle)
        connectSetting("backplot.multitool-colors", self.showMultiColorPath)
        connectSetting("backplot.show-points-surface", self.showSurface)
        connectSetting("backplot.show-fps", self.showFPS)
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
        self._floating_wcs = set(geometry.floating_wcs)
        self._program_running = self._is_program_running()
        self._anchor_latched = self._program_running
        self._anchor_offset = (self._compute_anchor_offset()
                               if self._floating_wcs else None)
        self._rebuild_program_geometry()
        if self._program_view_on_load:
            self.setViewProgram(self._program_view_name)
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
        self._refresh_path_transforms()

    @Slot(object)
    def on_offset_table_changed(self, _offset_table=None):
        self._refresh_path_transforms()

    def update_g92_offset(self, offset):
        if offset is not None:
            values = list(offset)[:3]
            while len(values) < 3:
                values.append(0.0)
            self._g92_offset = tuple(float(value) for value in values)
        if self._floating_wcs:
            self._update_floating_anchor()

    def update_g5x_index(self, index):
        try:
            self._active_wcs_index = int(index)
        except (TypeError, ValueError):
            pass
        self._refresh_path_transforms()

    def update_rotation_xy(self, rotation):
        try:
            self._active_rotation = float(rotation)
        except (TypeError, ValueError):
            self._active_rotation = 0.0
        self._refresh_path_transforms()

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

    # -- live trail (breadcrumbs) -----------------------------------------

    def _poll_live_position(self):
        """Sample LinuxCNC at a fixed rate independent of the status plugin."""
        stat = getattr(self, "_stat", None)
        if stat is None:
            return
        try:
            stat.poll()
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            return
        attribute = "actual_position" if self._use_actual_position else "position"
        position = getattr(stat, attribute, None)
        if position is None:
            position = (getattr(stat, "position", None)
                        or getattr(stat, "actual_position", None))
        if position is None:
            return
        try:
            self.update_position(tuple(position))
        except (TypeError, ValueError):
            return

    def _current_motion_line(self):
        """G-code line currently being executed, or 0 when unknown."""
        stat = getattr(self, "_stat", None)
        try:
            line = int(getattr(stat, "motion_line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        if line > 0:
            return line

        status = getattr(self.datasource, "_status", None)
        channel = getattr(status, "motion_line", None)
        try:
            line = int(getattr(channel, "value", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        if line > 0:
            return line
        stat = getattr(status, "stat", None)
        try:
            return max(0, int(getattr(stat, "motion_line", 0) or 0))
        except (TypeError, ValueError):
            return 0

    def _segments_for_motion_lines(self, lines):
        """World-space segments executed by the given G-code lines."""
        wanted = sorted({int(line) for line in lines
                         if line is not None and int(line) > 0})
        if not wanted or not hasattr(self, "path_groups"):
            return []
        segments = []
        for row in self.path_groups.rows():
            if row.line_numbers.size == 0:
                continue
            mask = np.isin(row.line_numbers, wanted)
            if not mask.any():
                continue
            starts = row.world_points(row.starts[mask])
            ends = row.world_points(row.ends[mask])
            segments.extend(zip(starts, ends))
        return segments

    @staticmethod
    def _project_point_onto_segment(point, start, end):
        point = np.asarray(point, dtype=np.float64)
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        direction = end - start
        length_sq = float(np.dot(direction, direction))
        if length_sq <= 1e-24:
            return tuple(start), float(np.dot(point - start, point - start))
        t = float(np.dot(point - start, direction) / length_sq)
        t = max(0.0, min(1.0, t))
        projected = start + direction * t
        delta = point - projected
        return tuple(projected), float(np.dot(delta, delta))

    def _snapped_trail_point(self, point):
        """Project the live tip onto the active program segment.

        Actual-position feedback carries following error and encoder noise at
        speed, which makes a raw breadcrumb wander around the programmed path.
        The old VTK plotter snapped each sample to the current (and adjacent)
        motion line; doing the same here keeps the yellow trail on the path.
        Samples farther than 5 mm / 0.2 in from any candidate segment are kept
        raw, so a jog or a bad line number cannot pull the trail onto the part.
        """
        line = self._current_motion_line()
        previous = self._last_breadcrumb_motion_line
        try:
            metric = bool(self.datasource.isMachineMetric())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            metric = True
        tolerance = 5.0 if metric else 0.2
        limit_sq = tolerance * tolerance
        self._last_breadcrumb_motion_line = line or previous

        def nearest(lines):
            best_point = None
            best_distance_sq = None
            for start, end in self._segments_for_motion_lines(lines):
                projected, distance_sq = self._project_point_onto_segment(
                    point, start, end)
                if best_distance_sq is None or distance_sq < best_distance_sq:
                    best_distance_sq = distance_sq
                    best_point = projected
            return best_point, best_distance_sq

        # Prefer the line the interpreter says is executing. Adjacent/previous
        # lines are only a fallback for the sample that lands just after a
        # motion-line transition; using them outright made a point near a
        # corner snap onto the next line too early.
        best_point, best_distance_sq = nearest([line])
        if best_point is not None and best_distance_sq <= limit_sq:
            return best_point

        fallback = []
        if previous and previous != line:
            fallback.append(previous)
        if line > 1:
            fallback.append(line - 1)
        if line > 0:
            fallback.append(line + 1)
        best_point, best_distance_sq = nearest(fallback)
        if best_point is not None and best_distance_sq <= limit_sq:
            return best_point
        return point

    def _append_trail_point(self, point):
        """Append one breadcrumb and rebuild the yellow trail geometry."""
        if self._trail:
            last = self._trail[-1]
            dx = float(point[0]) - float(last[0])
            dy = float(point[1]) - float(last[1])
            dz = float(point[2]) - float(last[2])
            if dx * dx + dy * dy + dz * dz <= 1e-12:
                return

        self._trail.append(point)
        points = np.asarray(self._trail, dtype=np.float32).reshape(-1, 3)
        if len(points) >= 2:
            segments = np.empty((2 * (len(points) - 1), 3), dtype=np.float32)
            segments[0::2], segments[1::2] = points[:-1], points[1:]
            self.plot_data.trail.replace(map_points_to_quick3d(segments))
        else:
            self.plot_data.trail.replace(np.zeros((0, 3), dtype=np.float32))

    def update_position(self, position):
        if self._designer or position is None:
            return
        x, y, z = map(float, position[:3])
        if self.datasource.isMachineLathe():
            z, y = y, z
        self._position = (x, y, z)
        self._update_tool_transform()
        self._update_floating_anchor()
        self._apply_joint_feedback()
        if self._breadcrumbs_enabled:
            # Breadcrumbs follow the cutter tip, not the spindle/tool top.
            # _tool_tip_position() applies the live G43/G43.1 offset and is
            # zero when G49 is active, so the trail stays correct either way.
            # Snap to the active program segment to suppress following-error
            # wander at speed.
            self._append_trail_point(
                self._snapped_trail_point(self._tool_tip_position()))

    @Slot()
    def clearLivePlot(self):
        self._trail.clear()
        self._last_breadcrumb_motion_line = None
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
        self.rig.fit_bounds(self._program_bounds or self._machine_bounds,
                            padding=1.1)
        direction = str(view or "p").upper()
        if direction in VIEW_DIRECTIONS:
            self.rig.set_view(direction, self._active_center())
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

    # -- touch and camera-orientation gizmo -------------------------------

    def _on_pinch_zoom(self, factor):
        if factor > 0.0 and math.isfinite(factor):
            self.rig.zoom(factor)

    def _on_pinch_pan(self, dx, dy):
        width, height = self._viewport_size()
        self.rig.pan(dx, dy, width, height)

    def _on_pinch_rotate(self, degrees):
        if degrees:
            self.rig.orbit(degrees, 0.0)

    def _on_view_requested(self, axis):
        handler = {
            "X": self.setViewX, "Y": self.setViewY, "Z": self.setViewZ,
            "P": self.setViewP,
        }.get(str(axis or "").upper())
        if handler is not None:
            handler()

    def _sync_nav_helper(self):
        """Push the current camera basis and ``navHelper*`` config to QML."""
        if not hasattr(self, "plot_data") or not hasattr(self, "rig"):
            return
        props = self._nav_helper_props
        enabled = bool(props.get("enabled") or False)
        size = props.get("size") or QSize(96, 96)
        padding = props.get("padding") or QSize(12, 12)
        labels = props.get("labels") or ["X", "Y", "Z"]
        labels = [str(label) for label in labels]
        width = max(int(size.width()), 48)
        height = max(int(size.height()), 48)
        axis_color = props.get("axis_color")
        config = {
            "enabled": enabled,
            "anchor": str(props.get("anchor") or "lower-left"),
            "width": width,
            "height": height,
            "padding_x": max(int(padding.width()), 0),
            "padding_y": max(int(padding.height()), 0),
            "labels_visible": bool(props.get("labels_visible", True)),
            "labels": labels,
            "length": max(10.0, min(width, height) * 0.34),
            "pickable": bool(props.get("pickable", True)),
            "axis_color": (QColor(axis_color).name()
                           if isinstance(axis_color, QColor) else "#b8c2cc"),
        }
        axes = []
        if enabled:
            forward = (-self.rig._offset).normalized()
            up = self.rig._up
            right = QVector3D.crossProduct(forward, up).normalized()
            true_up = QVector3D.crossProduct(right, forward).normalized()
            for name, vector, color in (
                ("X", QVector3D(1.0, 0.0, 0.0),
                 self._nav_helper_x_axis_color.name()),
                ("Y", QVector3D(0.0, 0.0, -1.0),
                 self._nav_helper_y_axis_color.name()),
                ("Z", QVector3D(0.0, 1.0, 0.0),
                 self._nav_helper_z_axis_color.name()),
            ):
                axes.append({
                    "axis": name,
                    "dx": QVector3D.dotProduct(vector, right),
                    "dy": -QVector3D.dotProduct(vector, true_up),
                    "depth": QVector3D.dotProduct(vector, forward),
                    "color": color,
                })
        self.plot_data.set_nav_helper(axes, config)

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
        self._show_machine_ticks = bool(show)
        self.plot_data.machineTicksVisible = self._show_machine_ticks

    @Slot()
    def toggleMachineTicks(self):
        self.showMachineTicks(not self._show_machine_ticks)

    @Slot(bool)
    @Slot(object)
    def showMachineLabels(self, show):
        self._show_machine_labels = bool(show)
        self.plot_data.machineLabelsVisible = self._show_machine_labels

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
    @Slot(object)
    def showWcsOrigins(self, show):
        self.plot_data.wcsOriginsVisible = bool(show)

    @Slot(bool)
    @Slot(object)
    def showSpindle(self, show):
        self._show_spindle = bool(show)
        if hasattr(self, "machine_parts"):
            self.machine_parts.set_spindle_visible(self._show_spindle)
        # The cutter bit is not the spindle; leave it visible.
        if hasattr(self, "plot_data"):
            self.plot_data.toolVisible = bool(self._tool_shape.visible)

    @Slot(bool)
    @Slot(object)
    def showMachine(self, show):
        self._show_machine = bool(show)
        if hasattr(self, "plot_data"):
            self.plot_data.machineVisible = self._show_machine
        if hasattr(self, "machine_parts"):
            self.machine_parts.set_enabled(self._show_machine)

    @Slot(bool)
    @Slot(object)
    def showMultiColorPath(self, show):
        self._multitool_colors = bool(show)

    @Slot()
    def toggleMultiColorPath(self):
        self.showMultiColorPath(not self._multitool_colors)

    @Slot(bool)
    @Slot(object)
    def showFPS(self, show):
        self._show_fps = bool(show)

    @Slot(bool)
    @Slot(object)
    def showSurface(self, show):
        # The legacy VTK "points surface" was a hard-coded probe demo, not a
        # data-driven mode; keep the setting as state for config compatibility
        # but do not draw it. Machine geometry belongs in MACHINE_PARTS.
        self._show_surface = bool(show)
        LOG.debug("Qt Quick 3D showSurface is deprecated (legacy probe demo)")

    @Slot(bool)
    def alphaBlend(self, alpha):
        self._alpha_blend = bool(alpha)

    @Slot(bool)
    def enableMultiTouch(self, enabled):
        if hasattr(self, "plot_data"):
            self.plot_data.touchEnabled = bool(enabled)
        # Touch and click-to-pick compete for the same surface; QML disables
        # the single-click picker while pinch navigation is active.

    @Slot(bool)
    def enableBreadcrumbs(self, enabled):
        self._breadcrumbs_enabled = bool(enabled)
        if hasattr(self, "plot_data"):
            self.plot_data.trailVisible = self._breadcrumbs_enabled
        if not self._breadcrumbs_enabled:
            self.clearLivePlot()

    @Slot(bool)
    def setProgramViewWhenLoadingProgram(self, enabled, view="p"):
        self._program_view_on_load = bool(enabled)
        self._program_view_name = str(view or "p")

    # -- API-parity methods ------------------------------------------------

    @Slot()
    def reapplyNavHelperConfig(self):
        """Re-read ``navHelper*`` properties into the 2D orientation gizmo."""
        self._sync_nav_helper()

    @Slot()
    def printView(self):
        """Save a PNG snapshot of the current plot view.

        ``printView`` writes a real image next to the
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
        self._program_running = self._running
        self._anchor_latched = self._running
        if self._floating_wcs:
            self._update_floating_anchor()

    @Slot(object)
    def update_joints(self, joint_values):
        if not joint_values:
            return
        self._joints = tuple(float(value) for value in joint_values)
        if hasattr(self, "machine_parts"):
            self.machine_parts.apply_joint_values(self._joints)

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
            # Path geometry is grouped by role at load time, so a colour change
            # only needs the material colours refreshed -- no re-parse.
            if hasattr(self, "path_groups"):
                self.path_groups.set_colors(self._role_color_map())
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
        if hasattr(self, "plot_data"):
            self.plot_data.backgroundColor2 = self._background_color2.name()

    @Property(bool, freset=reset_to("enableProgramTicks", True))
    def enableProgramTicks(self):
        return self._enable_program_ticks

    @enableProgramTicks.setter
    def enableProgramTicks(self, value):
        self._enable_program_ticks = bool(value)
        if hasattr(self, "plot_data"):
            self.plot_data.programTicksVisible = self._enable_program_ticks

    @Property(bool, freset=reset_to("gridVisible", False))
    def gridVisible(self):
        return getattr(getattr(self, "plot_data", None), "gridVisible", False)

    @gridVisible.setter
    def gridVisible(self, value):
        self.showGrid(value)

    @Property(bool, freset=reset_to("wcsOriginsVisible", True))
    def wcsOriginsVisible(self):
        return bool(getattr(self.plot_data, "wcsOriginsVisible", True))

    @wcsOriginsVisible.setter
    def wcsOriginsVisible(self, value):
        self.showWcsOrigins(value)

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
        self._sync_nav_helper()

    @Property(QColor, freset=reset_to("navHelperYAxisColor", lambda self: QColor(60, 220, 60)))
    def navHelperYAxisColor(self):
        return self._nav_helper_y_axis_color

    @navHelperYAxisColor.setter
    def navHelperYAxisColor(self, color):
        self._nav_helper_y_axis_color = QColor(color)
        self._sync_nav_helper()

    @Property(QColor, freset=reset_to("navHelperZAxisColor", lambda self: QColor(80, 120, 255)))
    def navHelperZAxisColor(self):
        return self._nav_helper_z_axis_color

    @navHelperZAxisColor.setter
    def navHelperZAxisColor(self, color):
        self._nav_helper_z_axis_color = QColor(color)
        self._sync_nav_helper()

    @staticmethod
    def _nav_prop(qt_type, key):
        def getter(self):
            return self._nav_helper_props.get(key)

        def setter(self, value):
            self._nav_helper_props[key] = value
            self._sync_nav_helper()

        def reset(self):
            self._nav_helper_props.pop(key, None)
            self._sync_nav_helper()

        return Property(qt_type, getter, setter, freset=reset)

    # Retained for panels and helper widgets. Values are retained
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
