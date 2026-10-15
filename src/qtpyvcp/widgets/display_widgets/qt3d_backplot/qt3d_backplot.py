"""Qt3D backplot widget.

A Qt3D rendering of the LinuxCNC program path.  It consumes the renderer
independent :mod:`...backplot_common` layer for geometry, so coordinate math is
shared with the VTK backplot, and reuses the same slot/property names so
existing ``.ui`` signal connections keep working.
"""

import math
import os
from collections import OrderedDict, deque

import numpy as np
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Property, QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QQuaternion, QVector3D
from PySide6.QtWidgets import QVBoxLayout, QWidget
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

from . import scene, tool
from .camera import CameraRig
from .machine import MachineAssembly
from .navigation import BackplotNavigation

LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER', False)

NUMBER_OF_WCS = 9
EXTENTS_PADDING = 1.1


class Qt3D0(QWidget, VCPWidget, BaseBackPlot):
    """Qt3D-based 3D backplot widget."""

    # Emitted when the operator picks a program line in the 3D view.
    programLineSelected = Signal(int)
    programLinesSelected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._designer = bool(IN_DESIGNER)
        self._show_fps = False
        self._show_grid = False
        self._show_machine_bounds = True
        self._show_program_bounds = False
        self._show_machine = True
        self._show_spindle = True
        self._multitool_colors = False
        self._background_color = QColor(0, 0, 0)
        self._background_color2 = QColor(0, 0, 0)
        self._enable_program_ticks = True
        self._default_traverse_color = QColor(*DEFAULT_ROLE_COLORS['traverse'])
        self._default_arcfeed_color = QColor(*DEFAULT_ROLE_COLORS['arcfeed'])
        self._default_feed_color = QColor(*DEFAULT_ROLE_COLORS['feed'])
        self._default_dwell_color = QColor(*DEFAULT_ROLE_COLORS['dwell'])
        self._default_user_color = QColor(*DEFAULT_ROLE_COLORS['user'])
        self._traverse_color = QColor(self._default_traverse_color)
        self._arcfeed_color = QColor(self._default_arcfeed_color)
        self._feed_color = QColor(self._default_feed_color)
        self._dwell_color = QColor(self._default_dwell_color)
        self._user_color = QColor(self._default_user_color)
        self._nav_helper_x_axis_color = QColor(255, 60, 60)
        self._nav_helper_y_axis_color = QColor(60, 220, 60)
        self._nav_helper_z_axis_color = QColor(80, 120, 255)
        self._color_reload_pending = False

        self._geometry = None
        self._paths = OrderedDict()
        self._path_entities = OrderedDict()
        self._path_transforms = OrderedDict()
        self._pickers = OrderedDict()
        self._highlight_entity = None
        self._line_width = 2.0
        self._active_view = 'P'
        self._position = (0.0, 0.0, 0.0)
        self._trail = deque(maxlen=4000)
        self._last_filename = ''

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        if self._designer:
            self.setMinimumSize(400, 300)
            return

        self.datasource = LinuxCncDataSource()
        self._stat = linuxcnc.stat()
        self._is_lathe = self.datasource.isMachineLathe()

        self._build_window()
        self._build_scene()
        self.camera.positionChanged.connect(self._update_gradient_background)
        self.camera.viewCenterChanged.connect(self._update_gradient_background)
        self.camera.upVectorChanged.connect(self._update_gradient_background)
        self.camera.projectionMatrixChanged.connect(self._update_gradient_background)
        # The camera outlives the window container during teardown, so stop
        # reacting to its signals the moment this widget is destroyed.
        self.destroyed.connect(self._disconnect_camera)
        self._update_gradient_background()
        self._wire_signals()
        self._connect_settings()
        LOG.info("Qt3D backplot initialized")
        # LinuxCNC may have loaded its current file before this widget connects
        # to the file-change notification. Retry after startup settles so the
        # initial program is plotted as well as subsequent file changes.
        QTimer.singleShot(0, self._load_current_program)
        QTimer.singleShot(500, self._load_current_program)

    # ------------------------------------------------------------------
    # Scene construction
    # ------------------------------------------------------------------

    def _build_window(self):
        self.window = Qt3DExtras.Qt3DWindow()
        self.window.defaultFrameGraph().setClearColor(self._background_color)
        self.container = QWidget.createWindowContainer(self.window, self)
        self.container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.container.setMinimumSize(QSize(50, 50))
        self._layout.addWidget(self.container)

        self.root = Qt3DCore.QEntity()
        self.window.setRootEntity(self.root)

        self.camera = self.window.camera()
        self.rig = CameraRig(self.camera)

        # VTK-compatible navigation: the Qt3D orbit controller is intentionally
        # not used, because it fights the left-drag rotate / middle-drag pan /
        # right-drag zoom model the VTK backplot exposes.
        self.navigation = BackplotNavigation(
            self.rig, self.container,
            viewport_size=self._viewport_size,
            parent=self)
        self.container.installEventFilter(self.navigation)
        self.window.installEventFilter(self.navigation)

        try:
            picking = self.window.renderSettings().pickingSettings()
            picking.setPickMethod(Qt3DRender.QPickingSettings.LinePicking)
            picking.setPickResultMode(Qt3DRender.QPickingSettings.NearestPick)
        except Exception:
            LOG.debug("line picking unavailable", exc_info=True)

    def _build_scene(self):
        self._paths_root = Qt3DCore.QEntity(self.root)
        self._trail_root = Qt3DCore.QEntity(self.root)
        self._overlay_root = Qt3DCore.QEntity(self.root)
        self._build_light()
        self._rebuild_gradient_background()

        self._grid_entity = None
        self._machine_entity = None
        self._program_entity = None
        self._axes_entity = None
        self._trail_line = None
        self._tool_entity = None
        self._tool_shape = tool.ToolShape()
        self._tool_number = 0
        self._machine_assembly = None

        self.grid_entity = scene.build_line_entity(
            self._overlay_root, scene.build_grid_geometry((-1, 1, -1, 1)),
            width=1.0, name="grid")
        self.grid_entity.setEnabled(False)
        self._grid_entity = self.grid_entity

        self._build_axes()
        self._build_machine_bounds()
        self._build_machine_parts()
        self._build_tool()
        self._build_trail()
        self.setViewMachine()

    def _render_surface_alive(self):
        """True while the Qt3D window backing this widget still exists."""
        window = getattr(self, "window", None)
        return window is not None and isValid(window)

    def _disconnect_camera(self, *_args):
        """Detach camera signal handlers so they cannot fire post-destruction."""
        camera = getattr(self, "camera", None)
        if camera is None or not isValid(camera):
            return
        for signal in (camera.positionChanged, camera.viewCenterChanged,
                       camera.upVectorChanged, camera.projectionMatrixChanged):
            try:
                signal.disconnect(self._update_gradient_background)
            except (RuntimeError, TypeError):
                pass

    def _viewport_size(self):
        """Return ``(width, height)`` of the render surface, or ``(1, 1)``.

        Guards against the container/window C++ objects being deleted, which
        happens during teardown while the camera (and its signals) still live.
        """
        window = getattr(self, "window", None)
        if window is not None and isValid(window):
            try:
                size = window.size()
                return max(size.width(), 1), max(size.height(), 1)
            except RuntimeError:
                pass
        container = getattr(self, "container", None)
        if container is not None and isValid(container):
            try:
                return max(container.width(), 1), max(container.height(), 1)
            except RuntimeError:
                pass
        return 1, 1

    def _update_gradient_background(self, *_args):
        """Keep the two-colour background quad behind the current scene view."""
        transform = getattr(self, '_gradient_transform', None)
        if transform is None or self._designer:
            return
        if not isValid(self.window) or not isValid(transform):
            return

        try:
            self._position_gradient(transform)
        except RuntimeError:
            # The render surface was torn down while the camera was still
            # emitting; nothing left to position the background for.
            LOG.debug("gradient background update skipped (surface gone)",
                      exc_info=True)

    def _position_gradient(self, transform):
        camera = self.camera
        position = camera.position()
        center = camera.viewCenter()
        forward = center - position
        if forward.lengthSquared() < 1e-12:
            return
        forward.normalize()

        bounds = self._machine_box_bounds()
        program_bounds = self._geometry.bounds() if self._geometry is not None else None
        boxes = [box for box in (bounds, program_bounds) if box is not None]
        if boxes:
            minimum = [min(box[i] for box in boxes) for i in (0, 2, 4)]
            maximum = [max(box[i] for box in boxes) for i in (1, 3, 5)]
            radius = math.sqrt(sum((maximum[i] - minimum[i]) ** 2 for i in range(3))) * 0.5
        else:
            radius = max((center - position).length(), 10.0)

        distance = (center - position).length() + max(radius * 1.5, 10.0)
        plane_center = position + forward * distance
        facing_camera = -forward
        rotation = QQuaternion.fromDirection(facing_camera, camera.upVector())

        if camera.projectionType() == Qt3DRender.QCameraLens.OrthographicProjection:
            width = abs(camera.right() - camera.left())
            height = abs(camera.top() - camera.bottom())
        else:
            height = 2.0 * distance * math.tan(math.radians(camera.fieldOfView()) * 0.5)
            viewport_width, viewport_height = self._viewport_size()
            aspect = max(viewport_width / max(viewport_height, 1), 1e-3)
            width = height * aspect

        transform.setTranslation(plane_center)
        transform.setRotation(rotation)
        transform.setScale3D(QVector3D(max(width * 1.1, 1.0),
                                       max(height * 1.1, 1.0), 1.0))

    def _rebuild_gradient_background(self):
        if not isValid(self.window):
            return
        old_entity = getattr(self, '_gradient_entity', None)
        if old_entity is not None and isValid(old_entity):
            old_entity.setEnabled(False)
            old_entity.setParent(None)
            old_entity.deleteLater()
        self._gradient_entity = scene.build_gradient_background(
            self._overlay_root, self._background_color, self._background_color2)
        self._gradient_transform = self._gradient_entity._gradient_transform
        self._update_gradient_background()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not getattr(self, "_designer", True):
            QTimer.singleShot(0, self._update_gradient_background)

    def _path_colors(self):
        return {
            'traverse': self._traverse_color,
            'arcfeed': self._arcfeed_color,
            'feed': self._feed_color,
            'dwell': self._dwell_color,
            'user': self._user_color,
        }

    def _schedule_color_reload(self):
        if (self._designer or not self._render_surface_alive()
                or not self._last_filename or self._color_reload_pending):
            return
        self._color_reload_pending = True
        QTimer.singleShot(0, self._reload_colored_program)

    def _reload_colored_program(self):
        self._color_reload_pending = False
        if self._last_filename:
            self.load_program(self._last_filename, force=True)

    def _build_light(self):
        light_entity = Qt3DCore.QEntity(self.root)
        light = Qt3DRender.QDirectionalLight(light_entity)
        light.setColor(QColor(255, 255, 255))
        light.setIntensity(1.0)
        light.setWorldDirection(QVector3D(-0.4, 0.6, -1.0))
        light_entity.addComponent(light)
        self._light_entity = light_entity
        self._light = light

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
            LOG.warning("Qt3D MACHINE_PARTS not found: %s", path)
            return

        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as handle:
                data = yaml.safe_load(handle)
        except Exception:
            LOG.exception("failed to load MACHINE_PARTS for Qt3D backplot: %s", path)
            return

        self._machine_assembly = MachineAssembly(
            self._overlay_root, data, config_dir=config_dir or os.path.dirname(path))
        self._machine_assembly.set_enabled(self._show_machine)

    def _build_axes(self):
        length = 25.4 if self.datasource.isMachineMetric() else 1.0
        points, colors = scene.axis_triad_points(
            length,
            (self._nav_helper_x_axis_color, self._nav_helper_y_axis_color,
             self._nav_helper_z_axis_color),
        )
        self._axes_entity = scene.build_line_entity(
            self._overlay_root, points, colors, width=2.0, name="axes")

    def _rebuild_axes(self):
        if self._axes_entity is not None:
            self._axes_entity.setEnabled(False)
            self._axes_entity.setParent(None)
            self._axes_entity.deleteLater()
        self._build_axes()

    def _build_machine_bounds(self):
        bounds = self._machine_box_bounds()
        if bounds is None:
            self._machine_entity = None
            return
        points = scene.box_line_points(bounds)
        self._machine_entity = scene.build_line_entity(
            self._overlay_root, points, width=1.0, name="machine_bounds")

    def _build_trail(self):
        # Two vertices per trail segment, plus one for the leading point.
        capacity = max((self._trail.maxlen or 0) * 2, 2)
        self._trail_line = scene.DynamicLine(
            self._trail_root, capacity, color=(0.95, 0.85, 0.2, 1.0), width=2.0)

    # ------------------------------------------------------------------
    # Tool geometry (from the LinuxCNC tool table)
    # ------------------------------------------------------------------

    def _current_tool_number(self):
        stat = getattr(getattr(self.datasource, "_status", None), "stat", None)
        try:
            return int(getattr(stat, "tool_in_spindle", 0) or 0)
        except (TypeError, ValueError):
            return 0

    def _build_tool(self):
        self._tool_number = self._current_tool_number()
        self._tool_entity = None
        self._rebuild_tool()

    def _rebuild_tool(self):
        if not self._render_surface_alive():
            return

        old = getattr(self, "_tool_entity", None)
        if old is not None and isValid(old):
            old.setEnabled(False)
            old.setParent(None)
            old.deleteLater()
        self._tool_entity = None

        try:
            tool_table = self.datasource.getToolTable()
        except Exception:
            LOG.debug("tool table unavailable for Qt3D tool geometry", exc_info=True)
            tool_table = []

        shape = tool.tool_shape(
            tool_table,
            getattr(self, "_tool_number", 0),
            metric=self.datasource.isMachineMetric(),
            lathe=self.datasource.isMachineLathe(),
            robot=False,
            foam=self.datasource.isMachineFoam(),
            jet=self.datasource.isMachineJet(),
        )
        self._tool_shape = shape

        entity = tool.build_tool_entity(self._overlay_root, shape, name="tool")
        self._tool_entity = entity
        if entity is not None:
            entity.setEnabled(self._show_spindle)
            self._update_tool_transform()

    def _update_tool_transform(self):
        entity = getattr(self, "_tool_entity", None)
        if entity is None or not isValid(entity):
            return
        x, y, z = self._position
        offset = tool.tool_body_offset(self._tool_shape)
        transform = entity._tool_transform
        transform.setTranslation(QVector3D(x + offset[0], y + offset[1],
                                           z + offset[2]))

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _wire_signals(self):
        ds = self.datasource
        ds.programLoaded.connect(self.load_program)
        ds.positionChanged.connect(self.update_position)
        ds.g5xOffsetChanged.connect(self.update_g5x_offset)
        ds.g92OffsetChanged.connect(self.update_g92_offset)
        ds.g5xIndexChanged.connect(self.update_g5x_index)
        ds.rotationXYChanged.connect(self.update_rotation_xy)
        ds.toolInSpindleChanged.connect(self.update_tool_number)
        ds.toolTableChanged.connect(self.update_tool_table)
        ds.toolOffsetChanged.connect(self.update_tool_table)
        ds.offsetTableChanged.connect(self.on_offset_table_changed)

        try:
            self._stat.poll()
        except Exception:
            LOG.debug("LinuxCNC status not ready during Qt3D widget startup",
                      exc_info=True)

    def _connect_settings(self):
        connectSetting('backplot.show-grid', self.showGrid)
        connectSetting('backplot.show-program-bounds', self.showProgramBounds)
        connectSetting('backplot.show-machine-bounds', self.showMachineBounds)
        connectSetting('backplot.show-machine', self.showMachine)
        connectSetting('backplot.show-spindle', self.showSpindle)
        connectSetting('backplot.view', self.setView)
        connectSetting('backplot.perspective-view', self.viewPerspective)
        connectSetting('backplot.multitool-colors', self.showMultiColorPath)
        connectSetting('backplot.show-fps', self.showFPS)

    # ------------------------------------------------------------------
    # Program loading
    # ------------------------------------------------------------------

    @Slot()
    def reload_program(self, *args, **kwargs):
        self.load_program(self._last_filename, force=True)

    def _load_current_program(self):
        """Plot the file that was already active when the widget was created."""
        try:
            self._stat.poll()
            filename = self._stat.file
        except Exception:
            LOG.debug("Unable to read active LinuxCNC file for initial Qt3D plot",
                      exc_info=True)
            return
        if filename and os.path.isfile(filename) and filename != self._last_filename:
            self.load_program(filename)

    def load_program(self, fname=None, *, force=False):
        if self._designer or not self._render_surface_alive():
            return

        if not fname:
            fname = self._last_filename
        if not fname or not os.path.isfile(fname):
            return

        if not force and fname == self._last_filename and self._geometry is not None:
            return

        self._last_filename = fname
        LOG.debug("Qt3D backplot loading %s", fname)

        has_table_rotary = any(
            self.datasource.getAxisMotionOwners().get(axis, 'head') == 'table'
            for axis in ('A', 'B', 'C')
        )

        geometry = load_geometry(
            fname,
            self.datasource,
            colors=self._path_colors(),
            prefer_native=True,
            cpp_ok=not has_table_rotary,
        )
        if geometry is None:
            LOG.warning("Qt3D backplot produced no geometry for %s", fname)
            return

        self._geometry = geometry
        self._rebuild_paths()
        self._rebuild_program_bounds()
        self._rebuild_machine_bounds()
        LOG.info("Qt3D backplot loaded %s: %d WCS paths, %d segments, bounds=%s",
                 fname, len(geometry.paths), geometry.added_segments,
                 geometry.bounds())
        self.setViewProgram('p')

    def _rebuild_paths(self):
        for wcs_index, entity in self._path_entities.items():
            picker = self._pickers.get(wcs_index)
            if picker is not None:
                entity.removeComponent(picker)
            entity.setEnabled(False)
            entity.setParent(None)
        self._path_entities.clear()
        self._path_transforms.clear()
        self._pickers.clear()
        self._clear_highlight()
        self._paths = OrderedDict()

        if self._geometry is None:
            return

        for wcs_index, path in self._geometry.paths.items():
            self._paths[wcs_index] = path
            if path.is_empty:
                continue

            entity = scene.build_line_entity(
                self._paths_root, path.points, path.colors,
                width=self._line_width, name=f"path_wcs_{wcs_index}")

            transform = Qt3DCore.QTransform()
            entity.addComponent(transform)
            self._path_transforms[wcs_index] = transform
            self._path_entities[wcs_index] = entity

            picker = Qt3DRender.QObjectPicker(entity)
            picker.setHoverEnabled(False)
            picker.setDragEnabled(False)
            picker.setPriority(1)
            picker.released.connect(
                lambda event, wcs=wcs_index: self._on_path_picked(wcs, event))
            entity.addComponent(picker)
            self._pickers[wcs_index] = picker

        self._update_wcs_transforms()

    # -- picking -----------------------------------------------------------

    def _on_path_picked(self, wcs_index, event):
        # Only treat a click as a pick, matching the VTK backplot: a drag that
        # orbited/panned/zoomed the view must not select a line.
        if getattr(self.navigation, "dragged", False):
            return
        path = self._paths.get(wcs_index)
        if path is None or path.line_numbers.size == 0:
            return
        try:
            vertex = int(event.vertex1Index())
        except (AttributeError, TypeError):
            return
        segment_index = vertex // 2
        if segment_index < 0 or segment_index >= path.line_numbers.size:
            return
        line_number = int(path.line_numbers[segment_index])
        self._highlight_segment(wcs_index, segment_index)
        self.programLineSelected.emit(line_number)
        self.programLinesSelected.emit([line_number])

    def _highlight_segment(self, wcs_index, segment_index):
        self._clear_highlight()
        path = self._paths.get(wcs_index)
        if path is None:
            return
        segment = path.segment(segment_index)
        if segment is None:
            return
        start, end = segment
        points = np.asarray([start, end], dtype=np.float32)
        colors = np.asarray([[255, 230, 51, 255], [255, 230, 51, 255]], dtype=np.uint8)
        self._highlight_entity = scene.build_line_entity(
            self._overlay_root, points, colors, width=5.0, name="highlight")

        x, y, z, rotation = self._wcs_offsets(wcs_index)
        transform = Qt3DCore.QTransform()
        transform.setTranslation(QVector3D(x, y, z))
        transform.setRotationZ(rotation)
        self._highlight_entity.addComponent(transform)

    def _clear_highlight(self):
        if self._highlight_entity is not None:
            self._highlight_entity.setEnabled(False)
            self._highlight_entity.setParent(None)
            self._highlight_entity = None

    def _rebuild_program_bounds(self):
        if self._program_entity is not None:
            self._program_entity.setEnabled(False)
            self._program_entity.setParent(None)
            self._program_entity = None

        bounds = self._geometry.bounds() if self._geometry else None
        if bounds is None:
            return

        points = scene.box_line_points(bounds)
        self._program_entity = scene.build_line_entity(
            self._overlay_root, points, width=1.0, name="program_bounds")
        self._program_entity.setEnabled(self._show_program_bounds)

    def _rebuild_machine_bounds(self):
        if self._machine_entity is not None:
            self._machine_entity.setEnabled(False)
            self._machine_entity.setParent(None)
            self._machine_entity = None
        self._build_machine_bounds()
        if self._machine_entity is not None:
            self._machine_entity.setEnabled(self._show_machine_bounds)

    # ------------------------------------------------------------------
    # Coordinate transforms
    # ------------------------------------------------------------------

    def _offset_columns(self):
        """Column-name -> index map for the offset table (cached)."""
        columns = getattr(self, "_offset_columns_cache", None)
        if columns is not None:
            return columns
        try:
            columns = dict(self.datasource.getOffsetColumns() or {})
        except Exception:
            LOG.debug("offset columns unavailable", exc_info=True)
            columns = {}
        self._offset_columns_cache = columns
        return columns

    def _wcs_offsets(self, wcs_index):
        """Return ``(x, y, z, rotation)`` for *wcs_index* in machine units."""
        try:
            table = self.datasource.getWcsOffsets()
        except Exception:
            return (0.0, 0.0, 0.0, 0.0)
        entry = table.get(wcs_index) if isinstance(table, dict) else None
        if entry is None:
            return (0.0, 0.0, 0.0, 0.0)

        values = list(entry)
        columns = self._offset_columns()

        def _get(name, default=0.0):
            index = columns.get(name)
            if index is None or index >= len(values):
                return default
            try:
                return float(values[index])
            except (TypeError, ValueError):
                return default

        # Use the column map when available; fall back to the conventional
        # X, Y, Z, R order.
        if columns:
            return _get('X'), _get('Y'), _get('Z'), _get('R')
        while len(values) < 4:
            values.append(0.0)
        return values[0], values[1], values[2], values[3]

    def _update_wcs_transforms(self):
        if not self._render_surface_alive():
            return
        for wcs_index, transform in self._path_transforms.items():
            x, y, z, rotation = self._wcs_offsets(wcs_index)
            transform.setTranslation(QVector3D(x, y, z))
            transform.setRotationZ(rotation)

    def _machine_box_bounds(self):
        try:
            axis = self.datasource.getAxis()
        except Exception:
            return None
        if not axis:
            return None
        try:
            xmin, xmax = axis[0]['min_position_limit'], axis[0]['max_position_limit']
            ymin, ymax = axis[1]['min_position_limit'], axis[1]['max_position_limit']
            zmin, zmax = axis[2]['min_position_limit'], axis[2]['max_position_limit']
        except (KeyError, IndexError, TypeError):
            return None
        return (xmin, xmax, ymin, ymax, zmin, zmax)

    # ------------------------------------------------------------------
    # Live position
    # ------------------------------------------------------------------

    def update_position(self, position):
        if self._designer or not self._render_surface_alive() or position is None:
            return
        x, y, z = float(position[0]), float(position[1]), float(position[2])
        if self.datasource.isMachineLathe():
            z, y = y, z
        self._position = (x, y, z)

        self._update_tool_transform()

        if self._trail.maxlen:
            self._trail.append((x, y, z))
            self._update_trail()

    def _update_trail(self):
        if not self._render_surface_alive() or self._trail_line is None:
            return

        trail = list(self._trail)
        if len(trail) < 2:
            self._trail_line.clear()
            return

        points = np.asarray(trail, dtype=np.float32)
        segments = np.empty(((points.shape[0] - 1) * 2, 3), dtype=np.float32)
        segments[0::2] = points[:-1]
        segments[1::2] = points[1:]
        self._trail_line.set_points(segments)

    @Slot()
    def clearLivePlot(self):
        self._trail.clear()
        if not self._render_surface_alive():
            return
        if self._trail_line is not None:
            self._trail_line.clear()

    # ------------------------------------------------------------------
    # Offset / motion slots
    # ------------------------------------------------------------------

    def update_g5x_offset(self, _offset):
        self._update_wcs_transforms()

    @Slot(object)
    def on_offset_table_changed(self, _offset_table=None):
        """Re-place the loaded paths when the WCS offset table is edited.

        Editing a G54..G59 offset in the offset-table widget does not change
        the ``g5x_offset`` status channel immediately, so without this the
        plot stays put until the interpreter re-applies the offset.
        """
        self._update_wcs_transforms()

    def update_g92_offset(self, _offset):
        pass

    def update_g5x_index(self, _index):
        self._update_wcs_transforms()

    def update_rotation_xy(self, _rotation):
        self._update_wcs_transforms()

    def motion_type(self, value):
        pass

    # ------------------------------------------------------------------
    # Camera / view slots
    # ------------------------------------------------------------------

    def _active_center(self):
        if self._active_view == 'M' and self._machine_entity is not None:
            bounds = self._machine_box_bounds()
        else:
            bounds = self._geometry.bounds() if self._geometry else None
        if bounds is None:
            bounds = self._machine_box_bounds()
        if bounds is None:
            return (0.0, 0.0, 0.0)
        return ((bounds[0] + bounds[1]) / 2,
                (bounds[2] + bounds[3]) / 2,
                (bounds[4] + bounds[5]) / 2)

    @Slot()
    def setViewP(self):
        self._active_view = 'P'
        self.rig.set_perspective()
        self.rig.set_view('P', self._active_center())

    @Slot()
    def setViewX(self):
        self._active_view = 'X'
        self.rig.set_view('X', self._active_center())

    @Slot()
    def setViewY(self):
        self._active_view = 'Y'
        self.rig.set_view('Y', self._active_center())

    @Slot()
    def setViewZ(self):
        self._active_view = 'Z'
        self.rig.set_view('Z', self._active_center())

    @Slot()
    def setViewZ2(self):
        self._active_view = 'Z2'
        self.rig.set_view('Z2', self._active_center())

    @Slot()
    def setViewXZ(self):
        self._active_view = 'XZ'
        self.rig.set_view('XZ', self._active_center())

    @Slot()
    def setViewXZ2(self):
        self._active_view = 'XZ2'
        self.rig.set_view('XZ2', self._active_center())

    @Slot()
    def setViewMachine(self):
        self._active_view = 'M'
        bounds = self._machine_box_bounds()
        self.rig.set_orthographic()
        self.rig.fit_bounds(bounds, padding=EXTENTS_PADDING)

    @Slot()
    def setViewPath(self):
        self._active_view = 'Path'
        self.rig.set_view('P', self._active_center())

    @Slot()
    def setViewProgram(self, view='p'):
        self._active_view = 'Program'
        bounds = self._geometry.bounds() if self._geometry else None
        if bounds is None:
            bounds = self._machine_box_bounds()
        self.rig.set_orthographic()
        self.rig.fit_bounds(bounds, padding=EXTENTS_PADDING)
        self.clearLivePlot()

    @Slot()
    def setViewOrtho(self):
        self.rig.set_orthographic()
        self.rig.fit_bounds(self._geometry.bounds() if self._geometry else None)

    @Slot()
    def setViewPersp(self):
        self.rig.set_perspective()

    @Slot(int)
    @Slot(str)
    @Slot(object)
    def setView(self, view):
        if isinstance(view, int):
            options = list(getSetting("backplot.view").enum_options or ())
            names = [opt.split(':')[0] for opt in options]
            if 0 <= view < len(names):
                view = names[view]
        name = str(view or 'P').upper()
        dispatch = {
            'X': self.setViewX, 'Y': self.setViewY, 'Z': self.setViewZ,
            'Z2': self.setViewZ2, 'XZ': self.setViewXZ, 'XZ2': self.setViewXZ2,
            'P': self.setViewP, 'M': self.setViewMachine,
        }
        handler = dispatch.get(name, self.setViewP)
        handler()

    @Slot(bool)
    @Slot(object)
    def viewPerspective(self, persp):
        if persp:
            self.setViewPersp()
        else:
            self.setViewOrtho()

    @Slot()
    def zoomIn(self):
        self.rig.zoom(0.9)

    @Slot()
    def zoomOut(self):
        self.rig.zoom(1.1)

    # ------------------------------------------------------------------
    # Visibility slots
    # ------------------------------------------------------------------

    @Slot(bool)
    @Slot(object)
    def showGrid(self, show):
        self._show_grid = bool(show)
        if self._render_surface_alive() and self._grid_entity is not None:
            self._grid_entity.setEnabled(self._show_grid)

    @Slot(bool)
    @Slot(object)
    def showMachineBounds(self, show):
        self._show_machine_bounds = bool(show)
        if self._render_surface_alive() and self._machine_entity is not None:
            self._machine_entity.setEnabled(self._show_machine_bounds)

    @Slot(bool)
    @Slot(object)
    def showProgramBounds(self, show):
        self._show_program_bounds = bool(show)
        if self._render_surface_alive() and self._program_entity is not None:
            self._program_entity.setEnabled(self._show_program_bounds)

    @Slot(bool)
    @Slot(object)
    def showMachine(self, show):
        self._show_machine = bool(show)
        if self._render_surface_alive() and self._machine_assembly is not None:
            self._machine_assembly.set_enabled(self._show_machine)

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
        """Rebuild the tool body when the tool table / TLO changes."""
        self._rebuild_tool()

    @Slot(object)
    def update_joints(self, joint_values):
        """Animate rotary machine parts from live joint feedback."""
        if (self._render_surface_alive() and self._machine_assembly is not None
                and joint_values is not None):
            self._machine_assembly.apply_joint_values(joint_values)

    @Slot(bool)
    @Slot(object)
    def showSpindle(self, show):
        self._show_spindle = bool(show)
        entity = getattr(self, "_tool_entity", None)
        if self._render_surface_alive() and entity is not None and isValid(entity):
            entity.setEnabled(self._show_spindle)

    @Slot(bool)
    @Slot(object)
    def showSurface(self, show):
        self._show_surface = bool(show)

    @Slot(bool)
    @Slot(object)
    def showMachineTicks(self, show):
        pass

    @Slot(bool)
    @Slot(object)
    def showMachineLabels(self, show):
        pass

    @Slot(bool)
    @Slot(object)
    def showMultiColorPath(self, show):
        self._multitool_colors = bool(show)

    @Slot(bool)
    @Slot(object)
    def showFPS(self, show):
        self._show_fps = bool(show)

    @Slot(bool)
    def enable_panning(self, enabled):
        if getattr(self, "navigation", None) is not None:
            self.navigation.pan_mode = bool(enabled)

    @Slot(bool)
    def enableMultiTouch(self, enabled):
        pass

    @Slot(bool)
    def enableBreadcrumbs(self, enabled):
        pass

    @Slot(bool)
    def setProgramViewWhenLoadingProgram(self, enabled, view='p'):
        pass

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(QColor, freset=reset_to('backgroundColor', lambda self: QColor(0, 0, 0)))
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self._background_color = QColor(color)
        if self._designer or not self._render_surface_alive():
            return
        self.window.defaultFrameGraph().setClearColor(self._background_color)
        self._rebuild_gradient_background()

    @Property(QColor, freset=reset_to('backgroundColor2', lambda self: QColor(0, 0, 0)))
    def backgroundColor2(self):
        return self._background_color2

    @backgroundColor2.setter
    def backgroundColor2(self, color):
        self._background_color2 = QColor(color)
        if self._designer or not self._render_surface_alive():
            return
        self._rebuild_gradient_background()

    @Property(bool, freset=reset_to('enableProgramTicks', True))
    def enableProgramTicks(self):
        return self._enable_program_ticks

    @enableProgramTicks.setter
    def enableProgramTicks(self, enabled):
        self._enable_program_ticks = bool(enabled)

    @Property(QColor, freset=reset_to('traverseColor', lambda self: QColor(self._default_traverse_color)))
    def traverseColor(self):
        return self._traverse_color

    @traverseColor.setter
    def traverseColor(self, color):
        self._traverse_color = QColor(color)
        self._schedule_color_reload()

    @Property(QColor, freset=reset_to('arcfeedColor', lambda self: QColor(self._default_arcfeed_color)))
    def arcfeedColor(self):
        return self._arcfeed_color

    @arcfeedColor.setter
    def arcfeedColor(self, color):
        self._arcfeed_color = QColor(color)
        self._schedule_color_reload()

    @Property(QColor, freset=reset_to('feedColor', lambda self: QColor(self._default_feed_color)))
    def feedColor(self):
        return self._feed_color

    @feedColor.setter
    def feedColor(self, color):
        self._feed_color = QColor(color)
        self._schedule_color_reload()

    @Property(QColor, freset=reset_to('dwellColor', lambda self: QColor(self._default_dwell_color)))
    def dwellColor(self):
        return self._dwell_color

    @dwellColor.setter
    def dwellColor(self, color):
        self._dwell_color = QColor(color)
        self._schedule_color_reload()

    @Property(QColor, freset=reset_to('userColor', lambda self: QColor(self._default_user_color)))
    def userColor(self):
        return self._user_color

    @userColor.setter
    def userColor(self, color):
        self._user_color = QColor(color)
        self._schedule_color_reload()

    @Property(QColor, freset=reset_to('navHelperXAxisColor', lambda self: QColor(255, 60, 60)))
    def navHelperXAxisColor(self):
        return self._nav_helper_x_axis_color

    @navHelperXAxisColor.setter
    def navHelperXAxisColor(self, color):
        self._nav_helper_x_axis_color = QColor(color)
        if not self._designer:
            self._rebuild_axes()

    @Property(QColor, freset=reset_to('navHelperYAxisColor', lambda self: QColor(60, 220, 60)))
    def navHelperYAxisColor(self):
        return self._nav_helper_y_axis_color

    @navHelperYAxisColor.setter
    def navHelperYAxisColor(self, color):
        self._nav_helper_y_axis_color = QColor(color)
        if not self._designer:
            self._rebuild_axes()

    @Property(QColor, freset=reset_to('navHelperZAxisColor', lambda self: QColor(80, 120, 255)))
    def navHelperZAxisColor(self):
        return self._nav_helper_z_axis_color

    @navHelperZAxisColor.setter
    def navHelperZAxisColor(self, color):
        self._nav_helper_z_axis_color = QColor(color)
        if not self._designer:
            self._rebuild_axes()

    @Property(bool, freset=reset_to('showGrid', False))
    def gridVisible(self):
        return self._show_grid

    @gridVisible.setter
    def gridVisible(self, value):
        self.showGrid(value)
