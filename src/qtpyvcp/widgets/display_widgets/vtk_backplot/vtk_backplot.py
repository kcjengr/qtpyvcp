#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

import yaml
import math

import linuxcnc
import os
import re
import logging
import shutil
from operator import add
from collections import OrderedDict

import time

import vtk
import vtk.qt
from vtkmodules.vtkCommonCore import (
    VTK_VERSION_NUMBER,
    vtkVersion
)
from qtpy.QtCore import Qt, Property, Slot, QObject, QEvent, QTimer
from qtpy.QtGui import QColor

from qtpyvcp.actions import machine_actions

# Fix polygons not drawing correctly on some GPU
# https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1

vtk.qt.QVTKRWIBase = "QGLWidget"

# Fix end

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionWidgets import vtkCameraOrientationWidget

from qtpyvcp import actions
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import connectSetting, getSetting


from .base_backplot import BaseBackPlot
from .axes_actor import AxesActor
from .tool_actor import ToolActor, ToolBitActor
from .points_surface import PointsSurfaceActor
from .table_actor import TableActor
from .spindle_actor import SpindleActor
from .machine_actor import MachineCubeActor, MachineLineActor, MachinePartsASM
from .path_cache_actor import PathCacheActor
from .program_bounds_actor import ProgramBoundsActor
from .vtk_canon import VTKCanon, COLOR_MAP
from .linuxcnc_datasource import LinuxCncDataSource

try:
    from qtpyvcp.native.backplot_cpp import build_backplot_from_file
except Exception:
    build_backplot_from_file = None

try:
    from qtpyvcp.utilities.load_perf_summary import PROGRAM_LOAD_PERF_SUMMARY
except Exception:
    class _NoopPerfSummary:
        def mark_phase(self, *args, **kwargs):
            return None

        def elapsed_since_start_ms(self, *args, **kwargs):
            return 0.0

        def update_backplot(self, *args, **kwargs):
            return None

    PROGRAM_LOAD_PERF_SUMMARY = _NoopPerfSummary()

LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER', False)
NUMBER_OF_WCS = 9
EXTENTS_PADDING = 1.1


# turn on antialiasing
from qtpy.QtOpenGL import QGLFormat
f = QGLFormat()
f.setSampleBuffers(True)
f.setSamples(8)  # Request 8x antialiasing (adjustable)

QGLFormat.setDefaultFormat(f)


def vtk_version_ok(major, minor):
    """
    Check the VTK version.

    :param major: Major version.
    :param minor: Minor version.
    :return: True if the requested VTK version is greater or equal to the actual VTK version.
    """
    needed_version = 10000000000 * int(major) \
                     + 100000000 * int(minor)
    try:
        vtk_version_number = VTK_VERSION_NUMBER
    except AttributeError:
        # Expand component-wise comparisons for VTK versions < 8.90.
        ver = vtkVersion()
        vtk_version_number = 10000000000 * ver.GetVTKMajorVersion() \
                             + 100000000 * ver.GetVTKMinorVersion()
    if vtk_version_number == needed_version:
        return True
    else:
        return False

class InteractorEventFilter(QObject):
    def __init__(self, parent=None, jog_safety_off=True):
        super(InteractorEventFilter, self).__init__(parent)
        self._keyboard_jog_ctrl_off = jog_safety_off
        self.slow_jog = False
        self.rapid_jog = True

        # Add lathe mode detection
        inifile = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        # Treat either LATHE=1 or BACK_TOOL_LATHE=1 as lathe mode for backplot logic
        lathe_val = (inifile.find("DISPLAY", "LATHE") or "0").strip()
        back_tool_val = (inifile.find("DISPLAY", "BACK_TOOL_LATHE") or "0").strip()
        self._lathe_mode = (lathe_val not in ["0", "false", "no", "n", ""]) or (back_tool_val not in ["0", "false", "no", "n", ""])
        self._back_tool_lathe = back_tool_val not in ["0", "false", "no", "n", ""]
        self._lathe_plan_view = 'XZ' if self._back_tool_lathe else 'XZ2'
        # Store reference to parent for jog speed slider access
        self._parent = parent
        # Get linuxcnc status for max_velocity
        self._status = linuxcnc.stat()
        # Try to resolve jog_speed_slider reference at init if possible
        self._jog_speed_slider = getattr(self._parent, "jog_speed_slider", None)

    def get_jog_speed(self, event=None):
        # If Shift is held, use linuxcnc status max_velocity (units/sec)
        if event is not None and event.modifiers() & Qt.ShiftModifier:
            self._status.poll()
            max_vel = getattr(self._status, "max_velocity", None)
            if max_vel is not None:
                return float(max_vel)
        # Otherwise use the standard QtPyVCP jog speed logic
        return machine_actions.jog_linear_speed.value / 60.0

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.isAutoRepeat():
                return super().eventFilter(obj, event)

            if event.modifiers() & Qt.ControlModifier:
                jog_active = 1
            elif self._keyboard_jog_ctrl_off:
                jog_active = 1
            else:
                jog_active = 0

            # Use jog speed from slider, or Shift for max speed
            speed = self.get_jog_speed(event)

            if self._lathe_mode:
                # Invert X axis only if BACK_TOOL_LATHE is enabled
                x_sign = -1 if self._back_tool_lathe else 1
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('X', -1 * jog_active * x_sign, speed=speed)
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('X', 1 * jog_active * x_sign, speed=speed)
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('Z', -1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('Z', 1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Y', 1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Y', -1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_Minus:
                    self.slow_jog = True
                    self.rapid_jog = False
                elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                    self.rapid_jog = True
                    self.slow_jog = False
            else:
                # Default mill mapping
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('Y', 1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('Y', -1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('X', -1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('X', 1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Z', 1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Z', -1 * jog_active, speed=speed)
                elif event.key() == Qt.Key_Minus:
                    self.slow_jog = True
                    self.rapid_jog = False
                elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                    self.rapid_jog = True
                    self.slow_jog = False
        elif event.type() == QEvent.KeyRelease:
            if event.isAutoRepeat():
                return super().eventFilter(obj, event)

            # Lathe mode jog key remapping
            if self._lathe_mode:
                x_sign = -1 if self._back_tool_lathe else 1
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('X', 0)
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('X', 0)
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('Z', 0)
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('Z', 0)
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Y', 0)
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Y', 0)
                elif event.key() == Qt.Key_Minus:
                    self.slow_jog = False
                elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                    self.rapid_jog = False
            else:
                # Default mill mapping
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('Y', 0)
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('Y', 0)
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('X', 0)
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('X', 0)
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Z', 0)
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Z', 0)
                elif event.key() == Qt.Key_Minus:
                    self.slow_jog = False
                elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                    self.rapid_jog = False

        return super().eventFilter(obj, event)

class VTKBackPlot(QVTKRenderWindowInteractor, VCPWidget, BaseBackPlot):
    def __init__(self, parent=None):
        super(VTKBackPlot, self).__init__(parent)
        
        # Disable VTK debug warnings
        vtk.vtkObject.GlobalWarningDisplayOff()

        self._datasource = LinuxCncDataSource()

        self._is_machine_lathe = self._datasource.isMachineLathe()
        self._is_machine_foam = self._datasource.isMachineFoam()
        self._is_machine_jet = self._datasource.isMachineJet()

        self.axis_motion_owner = self._datasource.getAxisMotionOwners()
        self.rotary_axis_origin = {'A': None, 'B': None, 'C': None}
        self.rotary_axis_origin.update(self._datasource.getRotaryAxisOrigins())
        self._overlay_pivot_log_cache = None
        
        # Detect lathe mode for backplot view logic (LATHE=1 or BACK_TOOL_LATHE=1)
        inifile = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        lathe_val = (inifile.find("DISPLAY", "LATHE") or "0").strip()
        back_tool_val = (inifile.find("DISPLAY", "BACK_TOOL_LATHE") or "0").strip()
        transform_debug_val = str(inifile.find("VTK", "TRANSFORM_DEBUG") or "0").strip().lower()
        self._transform_debug = transform_debug_val in ("1", "true", "yes", "on")
        breadcrumb_frame = str(inifile.find("VTK", "BREADCRUMB_FRAME") or "auto").strip().lower()
        if breadcrumb_frame in ("world", "machine"):
            self._breadcrumb_frame = "world"
        elif breadcrumb_frame in ("tool",):
            self._breadcrumb_frame = "tool"
        else:
            has_table_linear = any(self.axis_motion_owner.get(axis, 'head') == 'table' for axis in ('X', 'Y', 'Z'))
            has_table_rotary = any(self.axis_motion_owner.get(axis, 'head') == 'table' for axis in ('A', 'B', 'C'))
            self._breadcrumb_frame = 'tool' if (has_table_linear or has_table_rotary) else 'world'
        self._breadcrumb_world_frame = (self._breadcrumb_frame == "world")
        LOG.debug(
            "VTK breadcrumb mode resolved: requested=%s resolved=%s owners=%s",
            breadcrumb_frame,
            self._breadcrumb_frame,
            self.axis_motion_owner,
        )

        cpp_backplot_val = str(inifile.find("VTK", "CPP_BACKPLOT") or "1").strip().lower()
        cpp_backplot_requested = cpp_backplot_val in ("1", "true", "yes", "on")
        has_table_rotary = any(self.axis_motion_owner.get(axis, 'head') == 'table' for axis in ('A', 'B', 'C'))
        self._use_cpp_backplot = bool(cpp_backplot_requested and not has_table_rotary and build_backplot_from_file)
        self._lathe_mode = (lathe_val not in ["0", "false", "no", "n", ""]) or (back_tool_val not in ["0", "false", "no", "n", ""])
        self._back_tool_lathe = back_tool_val not in ["0", "false", "no", "n", ""]
        
        # Keyboard jogging is handled at the global level.
        if self._datasource.getKeyboardJog().lower() in ['true', '1', 't', 'y', 'yes']:
            jog_safety_off = self._datasource.getKeyboardJogLock().lower() in ['true', '1', 't', 'y', 'yes']
            event_filter = InteractorEventFilter(self, jog_safety_off)
            self.installEventFilter(event_filter)
            # Ensure this widget does not keep focus after mouse clicks
            self.setFocusPolicy(Qt.NoFocus)

        self.current_time = round(time.time() * 1000)
        self.plot_interval = 1000/self._datasource.getFPS()  # 1 second / 30 fps
        self.prev_plot_time = 0
        
        self.parent = parent
        self.ploter_enabled = True
        self.touch_enabled = False
        # provide a control to UI builders to suppress when line "breadcrumbs" are plotted
        self.breadcrumbs_plotted = True

        machine_ext_scale_setting = getSetting("backplot.machine-ext-scale")
        machine_ext_scale_value = getattr(machine_ext_scale_setting, 'value', 1.0)
        self.machine_ext_scale = self._coerce_float(machine_ext_scale_value, 1.0)
        
        # Set default view for lathe/back-tool-lathe
        if self._is_machine_lathe:
            self.default_view = "M"
        else:
            view_default_setting = getSetting("backplot.view").value
            view_options_setting = getSetting("backplot.view").enum_options
            view_options = list()
            
            for option in view_options_setting:
                view_options.append(option.split(':')[0])

            self.default_view = view_options[view_default_setting]

        
        self.program_view_when_loading_program = False
        self.program_view_when_loading_program_view = 'p'
        self.pan_mode = False
        self.line = None
        self._last_filename = str()
        self.rotating = 0
        self.panning = 0
        self.zooming = 0
        self._render_scheduled = False
        
        self.machine_parts = None
        self.machine_parts_data = None
        self.kinematics_overlay_shift = (0.0, 0.0, 0.0)
        self.kinematics_overlay_rotation = (0.0, 0.0, 0.0)
        self._runtime_switchkins_type = 0
        self._runtime_switchkins_cmd_lines = {}
        self._runtime_switchkins_logged_lines = set()
        self._cache_overlay_transform = vtk.vtkTransform()
        self._active_path_transform = vtk.vtkTransform()
        self._machine_bounds_base = None
        
        # assume that we are standing upright and compute azimuth around that axis
        self.natural_view_up = (0, 0, 1)
        
        #used to set the perspective view direction
        self.view_x_vec = 1
        self.view_y_vec = -1
        self.view_z_vec = 1

        self._plot_machine = True
        
        self._background_color = QColor(0, 0, 0)
        self._background_color2 = QColor(0, 0, 0)
        self._enableProgramTicks = True

        self._default_traverse_color = QColor(200, 35, 35, 255)
        self._default_arcfeed_color = QColor(110, 110, 255, 255)
        self._default_feed_color = QColor(210, 210, 255, 255)
        self._default_dwell_color = QColor(0, 0, 255, 255)
        self._default_user_color = QColor(0, 100, 255, 255)

        self._traverse_color = self._default_traverse_color
        self._arcfeed_color = self._default_arcfeed_color
        self._feed_color = self._default_feed_color
        self._dwel_color = self._default_dwell_color
        self._user_color = self._default_user_color

        if IN_DESIGNER:
            return

        self.active_wcs_index = self._datasource.getActiveWcsIndex()
        self._set_wcs_offsets(self._datasource.getWcsOffsets())
        self.active_wcs_offset = self._datasource.getActiveWcsOffsets()
        self.g92_offset = self._datasource.getG92_offset()
        self.active_rotation = self._datasource.getRotationOfActiveWcs()
        
        self.rotation_xy_table = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.original_g5x_offset = [0.0] * NUMBER_OF_WCS
        self.original_g92_offset = [0.0] * NUMBER_OF_WCS

        self.spindle_position = (0.0, 0.0, 0.0)
        self.machine_motion_position = (0.0, 0.0, 0.0)
        self.spindle_rotation = (0.0, 0.0, 0.0)
        self.tooltip_position = (0.0, 0.0, 0.0)
        self.current_motion_type = None
        self._breadcrumbs_armed = False
        self._path_cache_seeded = False
        self._last_breadcrumb_world = None
        
        self.joints = self._datasource._status.joint

        self.foam_offset = [0.0, 0.0]

        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()
        
        self.path_actors = OrderedDict()

        self.path_end_point = OrderedDict()
        self.path_angle_point = OrderedDict()
        self.path_start_point = OrderedDict()
        self.offset_transitions = list()

        self.offset_change_start_actor = OrderedDict()
        self.offset_change_end_actor = OrderedDict()
        self.offset_change_line_actor = OrderedDict()
        
        if self._datasource.isMachineMetric():
            self.position_mult = 1000 #500 here works for me
            self.clipping_range_near = 0.01
            self.clipping_range_far = 10000.0
        else:
            self.position_mult = 100
            self.clipping_range_near = 0.001
            self.clipping_range_far = 1000.0

        self.camera.SetClippingRange(self.clipping_range_near, self.clipping_range_far)
        
        if self._datasource.getAntialias():
            #self.camera.SetUseAntialiasing(True)  # VTK 9.x+
            pass
        
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetActiveCamera(self.camera)

        self.renderer_window = self.GetRenderWindow()
        self.renderer_window.AddRenderer(self.renderer)

        if self._graphics_diagnostics_enabled():
            self._log_graphics_diagnostics()

        # self.nav_style = vtk.vtkInteractorStyleTrackballCamera()
        self.nav_style = vtk.vtkInteractorStyleMultiTouchCamera() if self.touch_enabled else None

        self.interactor = self.renderer_window.GetInteractor()
        self.interactor.SetInteractorStyle(self.nav_style)
        self.interactor.render_window = self.renderer_window
        # self.interactor.SetRenderWindow(self.renderer_window)
        
        if self._datasource.getAntialias() in ["true", "True", "TRUE", 1, "1"]:
            self.renderer_window.SetMultiSamples(8)  # Enable 8x multisampling for antialiasing

            
        if self._datasource.getNavHelper() in ["true", "True", "TRUE", 1, "1"]:
            self.cam_orient_manipulator = vtkCameraOrientationWidget()
            self.cam_orient_manipulator.SetParentRenderer(self.renderer)
            
        if not IN_DESIGNER:
            
            bounds_type = self._datasource.getMachineBounds()
            if bounds_type == "line":
                self.machine_actor = MachineLineActor(self._datasource)
            else:
                self.machine_actor = MachineCubeActor(self._datasource)
            
            self.machine_actor.SetCamera(self.camera)

            self.axes_actor = AxesActor(self._datasource)

            transform = vtk.vtkTransform()
            transform.Translate(*self.active_wcs_offset[:3])
            transform.RotateZ(self._datasource.getRotationOfActiveWcs())
            
            
            # Machine-space transform intentionally not applied to global axes actor.
            # self.axes_actor.SetUserTransform(transform)
            self.path_actors = OrderedDict()
            self.path_cache_actor = PathCacheActor(tuple(self.tooltip_position[:3]))
            if not self._breadcrumb_world_frame:
                self.path_cache_actor.SetUserTransform(self._active_path_transform)

            self.points_surface_actor = PointsSurfaceActor(self._datasource)

            self.table_model = self._datasource._inifile.find("VTK", "TABLE")
            if self.table_model is not None:
                self.table_actor = TableActor(self.table_model)

            x_vec = float(self._datasource._inifile.find("VTK", "VIEW_X") or 0.0)
            y_vec = float(self._datasource._inifile.find("VTK", "VIEW_Y") or 0.0)
            z_vec = float(self._datasource._inifile.find("VTK", "VIEW_Z") or 0.0)
            
            if x_vec:
                self.view_x_vec = x_vec
            if y_vec:
                self.view_y_vec = y_vec
            if z_vec:
                self.view_z_vec = z_vec

            self.spindle_model = self._datasource._inifile.find("VTK", "SPINDLE") or False

            if self.spindle_model:
                self.spindle_actor = SpindleActor(self._datasource, self.spindle_model)
            
            
            if self._plot_machine:
                
                self.machine_parts = self._datasource._inifile.find("VTK", "MACHINE_PARTS")
            
                if self.machine_parts:
                    with open(self.machine_parts, 'r') as f:
                        self.machine_parts_data = yaml.load(f, Loader=yaml.SafeLoader)

                        axis_dataset = self._datasource.getAxisConfigurationDataset()
                        LOG.debug(
                            "VTK rotary setup: owners=%s origins=%s validation=%s",
                            self.axis_motion_owner,
                            self.rotary_axis_origin,
                            axis_dataset.get('validation'),
                        )
                        
                        self.machine_parts_actor = MachinePartsASM(self.machine_parts_data)
            
            self.tool_actor = ToolActor(self._datasource)
            self.tool_bit_actor = ToolBitActor(self._datasource)


            # view settings
            connectSetting('backplot.show-spindle', self.showSpindle)
            connectSetting('backplot.show-grid', self.showGrid)
            connectSetting('backplot.show-program-bounds', self.showProgramBounds)
            # connectSetting('backplot.show-program-labels', self.showProgramLabels)
            # connectSetting('backplot.show-program-ticks', self.showProgramTicks)
            connectSetting('backplot.show-machine-bounds', self.showMachineBounds)
            connectSetting('backplot.show-machine-labels', self.showMachineLabels)
            connectSetting('backplot.show-machine-ticks', self.showMachineTicks)
            connectSetting('backplot.show-machine', self.showMachine)
            connectSetting('backplot.show-points-surface', self.showSurface)
            connectSetting('backplot.perspective-view', self.viewPerspective)
            connectSetting('backplot.view', self.setView)
            connectSetting('backplot.multitool-colors', self.showMultiColorPath)
            connectSetting('backplot.show-machine-model', self.showMachine)


            self.path_colors = {'traverse': self._traverse_color,
                           'arcfeed': self._arcfeed_color,
                           'feed': self._feed_color,
                           'dwell': QColor(0, 0, 255, 255),
                           'user': QColor(0, 100, 255, 255)
                       }

            self.offset_axes = OrderedDict()
            self.program_bounds_actors = OrderedDict()
            self.show_program_bounds = bool()

            # Add the observers to watch for particular events. These invoke Python functions.
            self.interactor.AddObserver("LeftButtonPressEvent", self.button_event)
            self.interactor.AddObserver("LeftButtonReleaseEvent", self.button_event)
            self.interactor.AddObserver("MiddleButtonPressEvent", self.button_event)
            self.interactor.AddObserver("MiddleButtonReleaseEvent", self.button_event)
            self.interactor.AddObserver("RightButtonPressEvent", self.button_event)
            self.interactor.AddObserver("RightButtonReleaseEvent", self.button_event)
            self.interactor.AddObserver("MouseMoveEvent", self.mouse_move)
            self.interactor.AddObserver("KeyPressEvent", self.keypress)
            self.interactor.AddObserver("MouseWheelForwardEvent", self.mouse_scroll_forward)
            self.interactor.AddObserver("MouseWheelBackwardEvent", self.mouse_scroll_backward)


            
            self.interactor.Initialize()
            self.renderer_window.Render()
            self.interactor.Start()

            # Add the observers to watch for particular events. These invoke Python functions.
            self._datasource.programLoaded.connect(self.load_program)
            
            self._datasource.positionChanged.connect(self.update_position)
            self._datasource.motionTypeChanged.connect(self.motion_type)
            
            # self._datasource.rotationXYChanged.connect(self.update_rotation_xy)
            self._datasource.g5xIndexChanged.connect(self.update_g5x_index)
            self._datasource.g5xOffsetChanged.connect(self.update_g5x_offset)
            self._datasource.g92OffsetChanged.connect(self.update_g92_offset)

            motion_line_channel = getattr(self._datasource._status, 'motion_line', None)
            motion_line_notify = getattr(motion_line_channel, 'notify', None)
            if callable(motion_line_notify):
                motion_line_notify(self._on_motion_line_changed)
            
            self._datasource.offsetTableChanged.connect(self.on_offset_table_changed)
            self._datasource.activeOffsetChanged.connect(self.update_active_wcs)
            
            self._datasource.toolTableChanged.connect(self.update_tool)
            self._datasource.toolOffsetChanged.connect(self.update_tool)
            self._datasource.toolInSpindleChanged.connect(self.update_tool)
            # self.status.g5x_index.notify(self.update_g5x_index)
            
            self.offsetTableColumnsIndex = self._datasource.getOffsetColumns()
            
            self.canon = VTKCanon(colors=self.path_colors, cpp_mode=self._use_cpp_backplot)

            self.path_actors = self.canon.get_path_actors()

            for wcs_index, path_actor in list(self.path_actors.items()):
                current_offsets = self._safe_get_offsets(wcs_index, self.offsetTableColumnsIndex)
                r_column = self.offsetTableColumnsIndex.get('R') if self.offsetTableColumnsIndex else None
                rotation = current_offsets[r_column] if r_column is not None and r_column < len(current_offsets) else 0.0

                actor_transform = vtk.vtkTransform()
                actor_transform.Translate(*current_offsets[:3])
                actor_transform.RotateZ(rotation)

                path_actor.SetUserTransform(actor_transform)
                path_actor.SetPosition(0.0, 0.0, 0.0)

                program_bounds_actor = ProgramBoundsActor(self.camera, path_actor)

                axes = path_actor.get_axes_actor()

                self.offset_axes[wcs_index] = axes
                self.program_bounds_actors[wcs_index] = program_bounds_actor

                self.renderer.AddActor(axes)
                self.renderer.AddActor(program_bounds_actor)
                self.renderer.AddActor(path_actor)
                
            if self._plot_machine:
                if self.machine_parts:
                    self.renderer.AddActor(self.machine_parts_actor)
                
                if self.table_model is not None:
                    self.renderer.AddActor(self.table_actor)

            if self.spindle_model:
                self.renderer.AddActor(self.spindle_actor)


            self.renderer.AddActor(self.tool_actor)
            self.renderer.AddActor(self.tool_bit_actor)
            tool_in_spindle = self._tool_in_spindle()

            if tool_in_spindle <= 0:
                self.tool_actor.SetVisibility(1)
                self.tool_bit_actor.SetVisibility(0)
            else:
                self.tool_actor.SetVisibility(1)
                self.tool_bit_actor.SetVisibility(1)
            self.renderer.AddActor(self.points_surface_actor)
            self.renderer.AddActor(self.machine_actor)
            self.renderer.AddActor(self.axes_actor)
            self.renderer.AddActor(self.path_cache_actor)

            self._machine_bounds_base = tuple(self.machine_actor.GetBounds())
            self._apply_kinematics_overlay_shift()

            self.setView(self.default_view)

            self.interactor.ReInitialize()
            
            self.renderer.ResetCameraClippingRange()
            self.renderer_window.Render()

            # self.setViewP()
            # self.renderer.ResetCamera()
            if self._datasource.getNavHelper() in ["true", "True", "TRUE", 1, "1"]:
                self.cam_orient_manipulator.On()

    def button_event(self, obj, event):

        if event == "LeftButtonPressEvent":
            if self.pan_mode is True:
                self.panning = 1
            else:
                self.rotating = 1

        elif event == "LeftButtonReleaseEvent":
            if self.pan_mode is True:
                self.panning = 0
            else:
                self.rotating = 0

        elif event == "MiddleButtonPressEvent":
            if self.pan_mode is True:
                self.rotating = 1
            else:
                self.panning = 1

        elif event == "MiddleButtonReleaseEvent":
            if self.pan_mode is True:
                self.rotating = 0
            else:
                self.panning = 0

        elif event == "RightButtonPressEvent":
            self.zooming = 1
        elif event == "RightButtonReleaseEvent":
            self.zooming = 0

    def mouse_scroll_backward(self, obj, event):
        self.zoomOut()

    def mouse_scroll_forward(self, obj, event):
        self.zoomIn()

    # General high-level logic
    def mouse_move(self, obj, event):
        lastXYpos = self.interactor.GetLastEventPosition()
        lastX = lastXYpos[0]
        lastY = lastXYpos[1]

        xypos = self.interactor.GetEventPosition()
        x = xypos[0]
        y = xypos[1]

        center = self.renderer_window.GetSize()
        centerX = center[0] / 2.0
        centerY = center[1] / 2.0

        if self.rotating:
            self.rotate(self.renderer, self.camera, x, y, lastX, lastY, centerX, centerY)
        elif self.panning:
            self.pan(self.renderer, self.camera, x, y, lastX, lastY, centerX, centerY)
        elif self.zooming:
            self.dolly(self.renderer, self.camera, x, y, lastX, lastY, centerX, centerY)

    def keypress(self, obj, event):
        key = obj.GetKeySym()
        if key == 'w' or key == 's':
            self._setRepresentation(key)

    # Functions that translate the events into camera motions.

    # This one is associated with the left mouse button. It translates x
    # and y relative motions into camera azimuth and elevation commands.
    def rotate(self, renderer, camera, x, y, lastX, lastY, centerX, centerY):
        self.natural_azimuth(camera, lastX - x)
        camera.Elevation(lastY - y)
        camera.OrthogonalizeViewUp()
        camera.SetClippingRange(self.clipping_range_near, self.clipping_range_far)
        renderer.ResetCameraClippingRange()
        self._render_frame(interactive=True)

    # Change azimuth around natural view up vector
    def natural_azimuth(self, camera, angle):
        fp = self.camera.GetFocalPoint()

        t = vtk.vtkTransform()
        t.Translate(fp[0], fp[1], fp[2])
        t.RotateWXYZ(angle, self.natural_view_up)
        t.Translate(-fp[0], -fp[1], -fp[2])
        camera.ApplyTransform(t)

    # Pan translates x-y motion into translation of the focal point and position.
    def pan(self, renderer, camera, x, y, lastX, lastY, centerX, centerY):
        FPoint = camera.GetFocalPoint()
        FPoint0 = FPoint[0]
        FPoint1 = FPoint[1]
        FPoint2 = FPoint[2]

        PPoint = camera.GetPosition()
        PPoint0 = PPoint[0]
        PPoint1 = PPoint[1]
        PPoint2 = PPoint[2]

        renderer.SetWorldPoint(FPoint0, FPoint1, FPoint2, 1.0)
        renderer.WorldToDisplay()
        DPoint = renderer.GetDisplayPoint()
        focalDepth = DPoint[2]

        APoint0 = centerX + (x - lastX)
        APoint1 = centerY + (y - lastY)

        renderer.SetDisplayPoint(APoint0, APoint1, focalDepth)
        renderer.DisplayToWorld()
        RPoint = renderer.GetWorldPoint()
        RPoint0 = RPoint[0]
        RPoint1 = RPoint[1]
        RPoint2 = RPoint[2]
        RPoint3 = RPoint[3]

        if RPoint3 != 0.0:
            RPoint0 = RPoint0 / RPoint3
            RPoint1 = RPoint1 / RPoint3
            RPoint2 = RPoint2 / RPoint3

        camera.SetFocalPoint((FPoint0 - RPoint0) / 1.0 + FPoint0,
                             (FPoint1 - RPoint1) / 1.0 + FPoint1,
                             (FPoint2 - RPoint2) / 1.0 + FPoint2)

        camera.SetPosition((FPoint0 - RPoint0) / 1.0 + PPoint0,
                           (FPoint1 - RPoint1) / 1.0 + PPoint1,
                           (FPoint2 - RPoint2) / 1.0 + PPoint2)

        self._render_frame(interactive=True)

    # Dolly converts y-motion into a camera dolly commands.
    def dolly(self, renderer, camera, x, y, lastX, lastY, centerX, centerY):
        dollyFactor = pow(1.02, (0.5 * (y - lastY)))
        if camera.GetParallelProjection():
            parallelScale = camera.GetParallelScale() * dollyFactor
            camera.SetParallelScale(parallelScale)
        else:
            camera.Dolly(dollyFactor)
            renderer.ResetCameraClippingRange()

        self._render_frame(interactive=True)

    # Surface sets the representation of all actors to surface or wireframe.
    def _setRepresentation(self, keyPressed):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        actor = actors.GetNextItem()
        while actor:
            if keyPressed == 's':
                # sets the representation of all actors to surface.
                actor.GetProperty().SetRepresentationToSurface()
            elif keyPressed == 'w':
                # sets the representation of all actors to wireframe.
                actor.GetProperty().SetRepresentationToWireframe()
            actor = actors.GetNextItem()
        self._render_frame(interactive=True)

    def tlo(self, tlo):
        pass

    @Slot()
    def reload_program(self, *args, **kwargs):
        self.load_program(self._last_filename)

    def load_program(self, fname=None):
        self._datasource._status.addLock()
        PROGRAM_LOAD_PERF_SUMMARY.mark_phase(fname, phase='vtk-load-program-enter', percent=48)
        self._index_runtime_switchkins_commands(fname)

        for start_actor in self.offset_change_start_actor.values():
            if start_actor:
                self.renderer.RemoveActor(start_actor)
        for end_actor in self.offset_change_end_actor.values():
            if end_actor:
                self.renderer.RemoveActor(end_actor)
        for line_actor in self.offset_change_line_actor.values():
            if line_actor:
                self.renderer.RemoveActor(line_actor)

        self.offset_change_start_actor.clear()
        self.offset_change_end_actor.clear()
        self.offset_change_line_actor.clear()

        # Cleanup the scene, remove any previous actors if any.
        # Do this for each WCS.
        for wcs_index, actor in self.path_actors.items():
            axes_actor = actor.get_axes_actor()
            program_bounds_actor = self.program_bounds_actors[wcs_index]

            # if wcs_index == self.active_wcs_index:

            self.renderer.RemoveActor(axes_actor)
            
            self.renderer.RemoveActor(actor)
            self.renderer.RemoveActor(program_bounds_actor)


        self.path_actors.clear()
        self.offset_axes.clear()
        self.program_bounds_actors.clear()

        start_time = time.time()

        if not fname:
            self._datasource._status.removeLock()
            return

        self.canon = VTKCanon(colors=self.path_colors, cpp_mode=self._use_cpp_backplot)

        cpp_used = False
        if self._use_cpp_backplot and build_backplot_from_file:
            try:
                cpp_result = build_backplot_from_file(
                    fname,
                    self._datasource,
                    path_colors=self.path_colors,
                    unitcode="G%d" % (20 + (self.stat.linear_units == 1)),
                    initcode=self.ini.find("RS274NGC", "RS274NGC_STARTUP_CODE") or "",
                    parameter_file=self.parameter_file,
                    temp_parameter_file=self.temp_parameter_file,
                )
            except Exception as exc:
                LOG.warning("VTK C++ backplot failed, falling back to Python: %s", exc)
                cpp_result = None

            if cpp_result is not None:
                cpp_used = True
                self.path_actors = cpp_result.path_actors
                self.offset_transitions = cpp_result.offset_transitions or list()
                self.canon.added_segments = int(getattr(cpp_result, 'added_segments', 0))
            else:
                self.load(fname)
        else:
            self.load(fname)

        if not cpp_used:
            self.canon.draw_lines()
            self.path_actors = self.canon.get_path_actors()
            self.offset_transitions = self.canon.get_offset_transitions()

        LOG.info("-------Draw time %s seconds ---" % (time.time() - start_time))

        if self._is_machine_foam:

            self.foam_offset = self.canon.get_foam()
            LOG.warning(self.foam_offset)
            z = self.foam_offset[0]
            w = self.foam_offset[1]

            self.tool_bit_actor.set_foam_offsets(z, w)

        offset_columns = self._datasource.getOffsetColumns()

        for wcs_index, actor in self.path_actors.items():
            current_offsets = self._safe_get_offsets(wcs_index, offset_columns)
            # rotation = self._datasource.getRotationOfActiveWcs()

            x_column = offset_columns.get('X')
            y_column = offset_columns.get('Y')
            z_column = offset_columns.get('Z')
            r_column = offset_columns.get('R')

            if x_column is not None:
                x = current_offsets[x_column]
            else:
                x = 0.0

            if y_column is not None:
                y = current_offsets[y_column]
            else:
                y = 0.0

            if z_column is not None:
                z = current_offsets[z_column]
            else:
                z = 0.0

            if r_column is not None:
                rotation = current_offsets[r_column]
            else:
                rotation = 0.0

            if 0 <= wcs_index < len(self.rotation_xy_table):
                self.rotation_xy_table[wcs_index] = rotation
            
            actor_transform = self._compose_wcs_transform(x, y, z, rotation)
            axes_transform = self._compose_wcs_transform(x, y, z, rotation)
            
            # Scale up the axes for the active WCS to provide visual feedback
            if wcs_index == self.active_wcs_index:
                axes_transform.Scale(1.5, 1.5, 1.5)  # Make active WCS axes 50% larger
                self._active_path_transform.DeepCopy(actor_transform)
                if not self._breadcrumb_world_frame:
                    self.path_cache_actor.SetUserTransform(self._active_path_transform)

            
            actor.SetUserTransform(actor_transform)
            actor.SetPosition(0.0, 0.0, 0.0)

            program_bounds_actor = ProgramBoundsActor(self.camera, actor)

            axes = actor.get_axes_actor()

            self.offset_axes[wcs_index] = axes
            self.program_bounds_actors[wcs_index] = program_bounds_actor

            axes.SetUserTransform(axes_transform)  # Keep per-WCS axes aligned with path actor transform.

            self.renderer.AddActor(axes)
            self.renderer.AddActor(program_bounds_actor)
            self.renderer.AddActor(actor)

        self._rebuild_transition_actors(offset_columns)
        # self.renderer.AddActor(self.axes_actor)
        self._request_render()
        if self.program_view_when_loading_program:
            self.setViewProgram(self.program_view_when_loading_program_view)

        QTimer.singleShot(300, self._datasource._status.removeLock)


    def motion_type(self, value):
        self.current_motion_type = value
        if value == linuxcnc.MOTION_TYPE_TOOLCHANGE:
            self.update_tool()

    def _on_motion_line_changed(self, _line):
        self._log_runtime_switchkins_command_hit(
            self._current_switchkins_type(),
            motion_line_value=_line,
        )

    def _should_plot_breadcrumb_for_motion(self):
        mt = self.current_motion_type
        if mt is None:
            status_obj = getattr(self._datasource, '_status', None)
            stat_obj = getattr(status_obj, 'stat', None)
            mt = getattr(stat_obj, 'motion_type', None)

        if mt == linuxcnc.MOTION_TYPE_TOOLCHANGE:
            return False

        if not self._breadcrumbs_armed:
            self._breadcrumbs_armed = True

        return True

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

        float_pattern = r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$'
        if re.fullmatch(float_pattern, text):
            return float(text)
        return default

    @staticmethod
    def _point3_or_none(value):
        if not isinstance(value, (list, tuple)) or len(value) < 3:
            return None
        x = VTKBackPlot._coerce_float(value[0], None)
        y = VTKBackPlot._coerce_float(value[1], None)
        z = VTKBackPlot._coerce_float(value[2], None)
        if x is None or y is None or z is None:
            return None
        return (x, y, z)

    def _tool_in_spindle(self):
        status_obj = getattr(self._datasource, '_status', None)
        stat_obj = getattr(status_obj, 'stat', None)
        raw = getattr(stat_obj, 'tool_in_spindle', 0)
        return self._coerce_int(raw, 0)

    @staticmethod
    def _strip_gcode_comments(line):
        if not line:
            return ""

        text = line.split(';', 1)[0]
        return re.sub(r'\([^\)]*\)', ' ', text)

    def _index_runtime_switchkins_commands(self, fname):
        self._runtime_switchkins_cmd_lines = {}
        self._runtime_switchkins_logged_lines.clear()

        if not fname or not os.path.isfile(fname):
            return

        command_lines = {}
        try:
            with open(fname, 'r', encoding='utf-8', errors='ignore') as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    stripped = self._strip_gcode_comments(raw_line)
                    codes = re.findall(r'(?<!\d)M\s*(428|429|430)(?!\d)', stripped, flags=re.IGNORECASE)
                    if codes:
                        command_lines[line_number] = tuple("M{}".format(code) for code in codes)
        except Exception as exc:
            LOG.warning("VTK runtime switchkins index failed for %s: %s", fname, exc)
            return

        self._runtime_switchkins_cmd_lines = command_lines
        if command_lines:
            details = ', '.join(
                "L{}={}".format(line, '/'.join(codes)) for line, codes in sorted(command_lines.items())
            )
            LOG.warning("VTK runtime switchkins commands indexed: %s", details)

    def _log_runtime_switchkins_command_hit(self, current_switchkins_type, motion_line_value=None):
        if not self._runtime_switchkins_cmd_lines:
            return

        status_obj = getattr(self._datasource, '_status', None)
        stat_obj = getattr(status_obj, 'stat', None)
        if stat_obj is None:
            return

        motion_line = self._coerce_int(motion_line_value, None)
        if motion_line is None:
            motion_line = self._coerce_int(getattr(stat_obj, 'motion_line', None), None)
        if motion_line is None:
            return

        codes = self._runtime_switchkins_cmd_lines.get(motion_line)
        if not codes:
            return
        if motion_line in self._runtime_switchkins_logged_lines:
            return

        LOG.warning(
            "VTK runtime switchkins command reached: line=%s codes=%s switchkins_type=%s interp_state=%s",
            motion_line,
            '/'.join(codes),
            int(current_switchkins_type),
            getattr(stat_obj, 'interp_state', None),
        )
        self._runtime_switchkins_logged_lines.add(motion_line)

    def _graphics_diagnostics_enabled(self):
        inifile = getattr(self._datasource, '_inifile', None)
        inifile_find = getattr(inifile, 'find', None)
        if not callable(inifile_find):
            return False

        advanced_logging = str(inifile_find("DISPLAY", "ADVANCED_LOGGING") or "").strip().lower()
        return advanced_logging in ("1", "true", "yes", "on")

    @staticmethod
    def _extract_gl_version_pair(version_text):
        if not version_text:
            return None
        text = str(version_text)
        match = re.search(r"(\d+)\.(\d+)", text)
        if match is None:
            return None
        return int(match.group(1)), int(match.group(2))

    @staticmethod
    def _infer_glsl_from_opengl_version(version_text):
        version_pair = VTKBackPlot._extract_gl_version_pair(version_text)
        if version_pair is None:
            return "unknown"

        gl_to_glsl = {
            (2, 0): "1.10",
            (2, 1): "1.20",
            (3, 0): "1.30",
            (3, 1): "1.40",
            (3, 2): "1.50",
            (3, 3): "3.30",
            (4, 0): "4.00",
            (4, 1): "4.10",
            (4, 2): "4.20",
            (4, 3): "4.30",
            (4, 4): "4.40",
            (4, 5): "4.50",
            (4, 6): "4.60",
        }
        inferred = gl_to_glsl.get(version_pair)
        if inferred is None:
            return "unknown"
        return "{} (inferred from OpenGL {}.{})".format(inferred, version_pair[0], version_pair[1])

    def _log_graphics_diagnostics(self):
        ogl_info = {
            "vendor": "unknown",
            "renderer": "unknown",
            "version": "unknown",
            "glsl": "unknown",
        }

        ogl_window = vtk.vtkOpenGLRenderWindow.SafeDownCast(self.renderer_window)
        if ogl_window is not None:
            get_vendor = getattr(ogl_window, 'GetOpenGLVendor', None)
            get_renderer = getattr(ogl_window, 'GetOpenGLRenderer', None)
            get_major = getattr(ogl_window, 'GetOpenGLMajorVersion', None)
            get_minor = getattr(ogl_window, 'GetOpenGLMinorVersion', None)
            if callable(get_vendor):
                ogl_info["vendor"] = str(get_vendor() or "unknown")
            if callable(get_renderer):
                ogl_info["renderer"] = str(get_renderer() or "unknown")
            if callable(get_major) and callable(get_minor):
                major = self._coerce_int(get_major(), None)
                minor = self._coerce_int(get_minor(), None)
                if major is not None and minor is not None:
                    ogl_info["version"] = "{}.{}".format(major, minor)

        if ogl_info["glsl"].lower() == "unknown":
            ogl_info["glsl"] = self._infer_glsl_from_opengl_version(ogl_info["version"])

        lines = [
            "VTK graphics diagnostics:",
            "  - qt_api: {}".format(os.getenv('QT_API', 'unknown')),
            "  - qsg_rhi_backend: {}".format(os.getenv('QSG_RHI_BACKEND', 'default')),
            "  - vtk_version: {}".format(vtkVersion().GetVTKVersion()),
            "  - opengl_vendor: {}".format(ogl_info['vendor']),
            "  - opengl_renderer: {}".format(ogl_info['renderer']),
            "  - opengl_version: {}".format(ogl_info['version']),
            "  - glsl_version: {}".format(ogl_info['glsl']),
        ]
        LOG.debug("\n".join(lines))

        renderer_l = ogl_info["renderer"].lower()
        vendor_l = ogl_info["vendor"].lower()
        software_tokens = (
            "llvmpipe",
            "softpipe",
            "swrast",
            "software rasterizer",
            "lavapipe",
        )
        if any(token in renderer_l or token in vendor_l for token in software_tokens):
            LOG.warning(
                "VTK appears to be using software rendering (%s / %s). 3D backplot performance may be degraded.",
                ogl_info["vendor"],
                ogl_info["renderer"],
            )

    def _log_overlay_rotation_sources(self):
        axis_specs = [('A', 0), ('B', 1), ('C', 2)]
        active = []
        missing = []

        for axis_name, idx in axis_specs:
            if self.axis_motion_owner.get(axis_name, 'head') != 'table':
                continue

            angle = float(self.kinematics_overlay_rotation[idx])
            if abs(angle) <= 1e-12:
                continue

            origin = self.rotary_axis_origin.get(axis_name)
            if origin is None:
                missing.append(axis_name)
            else:
                active.append((axis_name, tuple(origin), angle))

        if active:
            log_key = ('active', tuple(active), tuple(missing))
            if self._overlay_pivot_log_cache != log_key:
                LOG.debug(
                    "VTK overlay pivots active: %s missing=%s overlay_rotation=%s",
                    active,
                    missing,
                    self.kinematics_overlay_rotation,
                )
                self._overlay_pivot_log_cache = log_key
            return

        table_axes = [axis for axis, _ in axis_specs if self.axis_motion_owner.get(axis, 'head') == 'table']
        fallback = []
        for axis_name in table_axes:
            origin = self.rotary_axis_origin.get(axis_name)
            if origin is not None:
                fallback.append((axis_name, tuple(origin)))

        if fallback:
            log_key = ('fallback', tuple(fallback))
            if self._overlay_pivot_log_cache != log_key:
                LOG.debug(
                    "VTK overlay pivots fallback: %s overlay_rotation=%s",
                    fallback,
                    self.kinematics_overlay_rotation,
                )
                self._overlay_pivot_log_cache = log_key
            return

        log_key = ('none', tuple(table_axes))
        if self._overlay_pivot_log_cache != log_key:
            LOG.debug(
                "VTK overlay pivots missing: table_axes=%s owners=%s origins=%s overlay_rotation=%s",
                table_axes,
                self.axis_motion_owner,
                self.rotary_axis_origin,
                self.kinematics_overlay_rotation,
            )
            self._overlay_pivot_log_cache = log_key

    @staticmethod
    def _apply_axis_rotation_about_pivot(transform, axis_name, angle_deg, pivot_local):
        transform.Translate(pivot_local[0], pivot_local[1], pivot_local[2])
        if axis_name == 'A':
            transform.RotateX(angle_deg)
        elif axis_name == 'B':
            transform.RotateY(angle_deg)
        elif axis_name == 'C':
            transform.RotateZ(angle_deg)
        transform.Translate(-pivot_local[0], -pivot_local[1], -pivot_local[2])

    def _overlay_rotary_pivot_absolute(self, axis_name):
        origin = self.rotary_axis_origin.get(axis_name)
        if origin is None:
            return None

        shift_x = self.kinematics_overlay_shift[0] if self.axis_motion_owner.get('X', 'head') == 'table' else 0.0
        shift_y = self.kinematics_overlay_shift[1] if self.axis_motion_owner.get('Y', 'head') == 'table' else 0.0
        shift_z = self.kinematics_overlay_shift[2] if self.axis_motion_owner.get('Z', 'head') == 'table' else 0.0

        return (
            float(origin[0] + shift_x),
            float(origin[1] + shift_y),
            float(origin[2] + shift_z),
        )

    def _overlay_rotary_axis_order(self):
        table_a = self.axis_motion_owner.get('A', 'head') == 'table'
        table_c = self.axis_motion_owner.get('C', 'head') == 'table'
        if table_a and table_c:
            return ('A', 'B', 'C')
        return ('A', 'B', 'C')

    def _transform_debug_enabled(self):
        return self._transform_debug and LOG.isEnabledFor(logging.DEBUG)

    def _compose_wcs_transform(self, x, y, z, rotation=0.0):
        wcs_x = float(x)
        wcs_y = float(y)
        wcs_z = float(z)

        base_x = wcs_x + self.kinematics_overlay_shift[0]
        base_y = wcs_y + self.kinematics_overlay_shift[1]
        base_z = wcs_z + self.kinematics_overlay_shift[2]

        if self._transform_debug_enabled():
            LOG.debug(
                "VTK compose_wcs start: wcs=(%.6f, %.6f, %.6f) base=(%.6f, %.6f, %.6f) "
                "overlay_shift=%s overlay_rotation=%s r_xy=%.6f",
                wcs_x,
                wcs_y,
                wcs_z,
                base_x,
                base_y,
                base_z,
                self.kinematics_overlay_shift,
                self.kinematics_overlay_rotation,
                float(rotation),
            )

        rx = float(self.kinematics_overlay_rotation[0])
        ry = float(self.kinematics_overlay_rotation[1])
        rz = float(self.kinematics_overlay_rotation[2])
        angles_by_axis = {
            'A': rx,
            'B': ry,
            'C': rz,
        }

        transform = vtk.vtkTransform()
        transform.Translate(base_x, base_y, base_z)

        self._log_overlay_rotation_sources()

        for axis_name in self._overlay_rotary_axis_order():
            angle = float(angles_by_axis.get(axis_name, 0.0))
            if abs(angle) <= 1e-12:
                continue

            pivot_abs = self._overlay_rotary_pivot_absolute(axis_name)
            if pivot_abs is None:
                self._apply_axis_rotation_about_pivot(transform, axis_name, angle, (0.0, 0.0, 0.0))
                continue

            pivot_local = (
                float(pivot_abs[0] - base_x),
                float(pivot_abs[1] - base_y),
                float(pivot_abs[2] - base_z),
            )
            if self._transform_debug_enabled():
                pivot_world_before = transform.TransformPoint(
                    float(pivot_local[0]),
                    float(pivot_local[1]),
                    float(pivot_local[2]),
                )
                LOG.debug(
                    "VTK compose_wcs rotate: axis=%s angle=%.6f pivot_abs=%s pivot_local=%s pivot_world_before=(%.6f, %.6f, %.6f)",
                    axis_name,
                    angle,
                    pivot_abs,
                    pivot_local,
                    float(pivot_world_before[0]),
                    float(pivot_world_before[1]),
                    float(pivot_world_before[2]),
                )
            self._apply_axis_rotation_about_pivot(transform, axis_name, angle, pivot_local)

            if self._transform_debug_enabled():
                pivot_world_after = transform.TransformPoint(
                    float(pivot_local[0]),
                    float(pivot_local[1]),
                    float(pivot_local[2]),
                )
                LOG.debug(
                    "VTK compose_wcs rotate result: axis=%s pivot_world_after=(%.6f, %.6f, %.6f)",
                    axis_name,
                    float(pivot_world_after[0]),
                    float(pivot_world_after[1]),
                    float(pivot_world_after[2]),
                )

        transform.RotateZ(float(rotation))
        if self._transform_debug_enabled():
            world_origin = transform.TransformPoint(0.0, 0.0, 0.0)
            LOG.debug(
                "VTK compose_wcs done: world_origin=(%.6f, %.6f, %.6f)",
                float(world_origin[0]),
                float(world_origin[1]),
                float(world_origin[2]),
            )
        return transform

    def _visual_spindle_position(self, machine_position, active_wcs_offset):
        x = machine_position[0]
        y = machine_position[1]
        z = machine_position[2]

        if self.axis_motion_owner.get('X', 'head') == 'table':
            x = 0.0

        if self.axis_motion_owner.get('Y', 'head') == 'table':
            y = 0.0

        if self.axis_motion_owner.get('Z', 'head') == 'table':
            z = 0.0

        return (x, y, z)

    def _current_switchkins_type(self):
        value = self._datasource.getSwitchkinsType()
        if value is None:
            return self._coerce_int(self._runtime_switchkins_type, 0)
        parsed = self._coerce_int(value, None)
        if parsed is None:
            return self._coerce_int(self._runtime_switchkins_type, 0)
        return parsed

    def _is_tcp_switchkins_active(self, switchkins_type=None):
        if switchkins_type is None:
            switchkins_type = self._current_switchkins_type()
        return int(switchkins_type) == 1

    def _has_table_owned_axes(self):
        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
            if self.axis_motion_owner.get(axis, 'head') == 'table':
                return True
        return False

    def _compute_kinematics_overlay_shift(self, machine_position, switchkins_type=None):
        if self._is_tcp_switchkins_active(switchkins_type) and (not self._has_table_owned_axes()):
            return (0.0, 0.0, 0.0)

        if all(self.axis_motion_owner.get(axis, 'head') == 'head' for axis in ['X', 'Y', 'Z']):
            return (0.0, 0.0, 0.0)

        sx = float(self.spindle_position[0] - machine_position[0])
        sy = float(self.spindle_position[1] - machine_position[1])
        sz = float(self.spindle_position[2] - machine_position[2])

        if self.axis_motion_owner.get('X', 'head') == 'table':
            sx = float(-machine_position[0])
        if self.axis_motion_owner.get('Y', 'head') == 'table':
            sy = float(-machine_position[1])
        if self.axis_motion_owner.get('Z', 'head') == 'table':
            sz = float(-machine_position[2])

        return (
            sx,
            sy,
            sz,
        )

    def _compute_kinematics_overlay_rotation(self, machine_rotation, switchkins_type=None):
        if self._is_tcp_switchkins_active(switchkins_type) and (not self._has_table_owned_axes()):
            return (0.0, 0.0, 0.0)

        if all(self.axis_motion_owner.get(axis, 'head') == 'head' for axis in ['A', 'B', 'C']):
            return (0.0, 0.0, 0.0)

        rx = 0.0
        ry = 0.0
        rz = 0.0

        if self.axis_motion_owner.get('A', 'head') == 'table':
            rx = -float(machine_rotation[0])
        if self.axis_motion_owner.get('B', 'head') == 'table':
            ry = -float(machine_rotation[1])
        if self.axis_motion_owner.get('C', 'head') == 'table':
            rz = -float(machine_rotation[2])

        return (rx, ry, rz)

    def _apply_machine_bounds_shift(self):
        if self._machine_bounds_base is None:
            return

        sx, sy, sz = self.kinematics_overlay_shift
        base = self._machine_bounds_base

        self.machine_actor.SetBounds(
            base[0] + sx,
            base[1] + sx,
            base[2] + sy,
            base[3] + sy,
            base[4] + sz,
            base[5] + sz,
        )

    def _apply_kinematics_overlay_shift(self):
        shift_transform = vtk.vtkTransform()
        sx, sy, sz = self.kinematics_overlay_shift
        shift_transform.Translate(sx, sy, sz)

        rx = float(self.kinematics_overlay_rotation[0])
        ry = float(self.kinematics_overlay_rotation[1])
        rz = float(self.kinematics_overlay_rotation[2])
        angles_by_axis = {
            'A': rx,
            'B': ry,
            'C': rz,
        }

        for axis_name in self._overlay_rotary_axis_order():
            angle = float(angles_by_axis.get(axis_name, 0.0))
            if abs(angle) <= 1e-12:
                continue

            origin = self._overlay_rotary_pivot_absolute(axis_name)
            if origin is None:
                self._apply_axis_rotation_about_pivot(shift_transform, axis_name, angle, (0.0, 0.0, 0.0))
                continue

            pivot_local = (
                float(origin[0] - sx),
                float(origin[1] - sy),
                float(origin[2] - sz),
            )
            self._apply_axis_rotation_about_pivot(shift_transform, axis_name, angle, pivot_local)
            if self._transform_debug_enabled():
                cache_pivot_after = shift_transform.TransformPoint(
                    float(pivot_local[0]),
                    float(pivot_local[1]),
                    float(pivot_local[2]),
                )
                LOG.debug(
                    "VTK cache overlay rotate: axis=%s angle=%.6f pivot_abs=%s pivot_local=%s pivot_world_after=(%.6f, %.6f, %.6f)",
                    axis_name,
                    angle,
                    origin,
                    pivot_local,
                    float(cache_pivot_after[0]),
                    float(cache_pivot_after[1]),
                    float(cache_pivot_after[2]),
                )

        if self._transform_debug_enabled():
            cache_origin = shift_transform.TransformPoint(0.0, 0.0, 0.0)
            LOG.debug(
                "VTK cache overlay transform: shift=%s rot=%s cache_origin=(%.6f, %.6f, %.6f)",
                self.kinematics_overlay_shift,
                self.kinematics_overlay_rotation,
                float(cache_origin[0]),
                float(cache_origin[1]),
                float(cache_origin[2]),
            )

        self._cache_overlay_transform = shift_transform

        self._apply_machine_bounds_shift()
        if (not self._breadcrumb_world_frame) and (self.path_cache_actor is not None):
            self.path_cache_actor.SetUserTransform(self._active_path_transform)

    def _world_tooltip_point(self, tooltip_local):
        point = self._point3_or_none(tooltip_local)
        if point is None:
            return (0.0, 0.0, 0.0)
        if self._active_path_transform is None:
            return point
        return self._active_path_transform.TransformPoint(point[0], point[1], point[2])

    def _active_path_local_point(self, world_point):
        point = self._point3_or_none(world_point)
        if point is None:
            return (0.0, 0.0, 0.0)
        if self._active_path_transform is None:
            return point

        inverse = vtk.vtkTransform()
        inverse.DeepCopy(self._active_path_transform)
        inverse.Inverse()
        return inverse.TransformPoint(point[0], point[1], point[2])

    def _current_tool_tip_world(self, tlo, machine_position, switchkins_type=None):
        if self._is_machine_jet:
            return (
                float(machine_position[0]),
                float(machine_position[1]),
                float(machine_position[2]),
            )
        return (
            float(self.spindle_position[0] + tlo[0]),
            float(self.spindle_position[1] + tlo[1]),
            float(self.spindle_position[2] - tlo[2]),
        )

    def _tooltip_point_in_path_frame(self, active_wcs_offset, tlo, machine_position):
        src_x = float(machine_position[0]) if self.axis_motion_owner.get('X', 'head') == 'table' else float(self.spindle_position[0])
        src_y = float(machine_position[1]) if self.axis_motion_owner.get('Y', 'head') == 'table' else float(self.spindle_position[1])
        src_z = float(machine_position[2]) if self.axis_motion_owner.get('Z', 'head') == 'table' else float(self.spindle_position[2])

        tx = float(src_x + tlo[0])
        ty = float(src_y + tlo[1])
        tz = float(src_z - tlo[2])

        x_col = self.offsetTableColumnsIndex.get('X') if self.offsetTableColumnsIndex else None
        y_col = self.offsetTableColumnsIndex.get('Y') if self.offsetTableColumnsIndex else None
        z_col = self.offsetTableColumnsIndex.get('Z') if self.offsetTableColumnsIndex else None

        if isinstance(active_wcs_offset, (list, tuple)):
            if x_col is not None and x_col < len(active_wcs_offset):
                tx -= float(active_wcs_offset[x_col])
            if y_col is not None and y_col < len(active_wcs_offset):
                ty -= float(active_wcs_offset[y_col])
            if z_col is not None and z_col < len(active_wcs_offset):
                tz -= float(active_wcs_offset[z_col])

        return [tx, ty, tz]

    def _machine_linear_axis_value(self, axis_name, axis_value):
        owner = self.axis_motion_owner.get(axis_name.upper(), 'head')
        if owner == 'table':
            return -float(axis_value)
        return float(axis_value)

    def _axis_joint_feedback(self, axis_name):
        axis_order = "XYZABCUVW"
        idx = axis_order.find(str(axis_name or '').upper())
        if idx < 0:
            return None

        if not isinstance(self.joints, (list, tuple)):
            return None
        if idx >= len(self.joints):
            return None

        joint_channel = self.joints[idx]
        if not hasattr(joint_channel, 'input'):
            return None

        input_channel = joint_channel.input
        if not hasattr(input_channel, 'value'):
            return None

        return self._coerce_float(input_channel.value, None)

    def _table_aware_linear_position(self, position):
        x = float(position[0])
        y = float(position[1])
        z = float(position[2])

        if self._is_tcp_switchkins_active():
            return (x, y, z)

        table_linear_active = any(
            self.axis_motion_owner.get(axis, 'head') == 'table'
            for axis in ['X', 'Y', 'Z']
        )

        if table_linear_active:
            xj = self._axis_joint_feedback('X')
            yj = self._axis_joint_feedback('Y')
            zj = self._axis_joint_feedback('Z')
            if xj is not None and yj is not None and zj is not None:
                return (xj, yj, zj)

        if self.axis_motion_owner.get('X', 'head') == 'table':
            xj = self._axis_joint_feedback('X')
            if xj is not None:
                x = xj
        if self.axis_motion_owner.get('Y', 'head') == 'table':
            yj = self._axis_joint_feedback('Y')
            if yj is not None:
                y = yj
        if self.axis_motion_owner.get('Z', 'head') == 'table':
            zj = self._axis_joint_feedback('Z')
            if zj is not None:
                z = zj

        return (x, y, z)

    def _machine_angular_axis_value(self, axis_name, axis_value):
        owner = self.axis_motion_owner.get(axis_name.upper(), 'head')
        if owner == 'table':
            return -float(axis_value)
        return float(axis_value)

    def _visual_tool_rotation(self, machine_rotation):
        rx = 0.0 if self.axis_motion_owner.get('A', 'head') == 'table' else float(machine_rotation[0])
        ry = 0.0 if self.axis_motion_owner.get('B', 'head') == 'table' else float(machine_rotation[1])
        rz = 0.0 if self.axis_motion_owner.get('C', 'head') == 'table' else float(machine_rotation[2])
        return (rx, ry, rz)

   
    def get_asm_parts(self, parts):
        # helper function to iterate over machine parts tree
        for part in parts.GetParts():
            # yield part
            if isinstance(part, vtk.vtkAssembly):
                yield part
                for p in self.get_asm_parts(part):
                    if isinstance(p, vtk.vtkAssembly):
                        yield p
                    # if isinstance(p, vtk.vtkActor):
                    #     yield p
            # elif isinstance(part, vtk.vtkActor):
            #     yield part
                    
    def update_position(self, position):  # the tool movement
        self.current_time = round(time.time() * 1000)

        if self.current_time - self.prev_plot_time >= self.plot_interval:
            self.prev_plot_time = self.current_time
        else:
            return

        active_wcs_offset = self._safe_get_offsets(self.active_wcs_index, self.offsetTableColumnsIndex)
        if self._is_machine_jet:
            list_pos = list(position)
            list_pos[2] = active_wcs_offset[2]
            position = tuple(list_pos)

        machine_position = self._table_aware_linear_position(position)
        self.machine_motion_position = machine_position
        self.spindle_position = self._visual_spindle_position(machine_position, active_wcs_offset)
        self.spindle_rotation = position[3:6]
        prev_switchkins_type = int(self._runtime_switchkins_type)
        current_switchkins_type = self._current_switchkins_type()
        if int(current_switchkins_type) != prev_switchkins_type:
            LOG.info(
                "VTK runtime switchkins-type changed: %s -> %s",
                prev_switchkins_type,
                int(current_switchkins_type),
            )
        self._runtime_switchkins_type = int(current_switchkins_type)
        self._log_runtime_switchkins_command_hit(current_switchkins_type)

        new_overlay_shift = self._compute_kinematics_overlay_shift(machine_position, current_switchkins_type)
        new_overlay_rotation = self._compute_kinematics_overlay_rotation(self.spindle_rotation, current_switchkins_type)
        if tuple(new_overlay_shift) != tuple(self.kinematics_overlay_shift) or tuple(new_overlay_rotation) != tuple(self.kinematics_overlay_rotation):
            self.kinematics_overlay_shift = tuple(new_overlay_shift)
            self.kinematics_overlay_rotation = tuple(new_overlay_rotation)
            self._apply_kinematics_overlay_shift()
            if len(self.path_actors) > 0:
                self.rotate_and_translate()

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)

        if self.spindle_model:
            self.spindle_actor.SetUserTransform(tool_transform)

        if self._plot_machine:
            if self.machine_parts:
                self.machine_parts_actor.InitPathTraversal()
                for part in self.get_asm_parts(self.machine_parts_actor):
                    if isinstance(part, vtk.vtkAssembly):
                        self.move_part(part)

        self.tool_actor.SetUserTransform(tool_transform)

        if self._is_machine_foam:
            self.tool_bit_actor.set_position(position)
        else:
            visual_position = list(position)
            visual_position[0] = self.spindle_position[0]
            visual_position[1] = self.spindle_position[1]
            visual_position[2] = self.spindle_position[2]

            tool_rotation = self._visual_tool_rotation(self.spindle_rotation)
            if len(visual_position) > 3:
                visual_position[3] = tool_rotation[0]
            if len(visual_position) > 4:
                visual_position[4] = tool_rotation[1]
            if len(visual_position) > 5:
                visual_position[5] = tool_rotation[2]

            self.tool_bit_actor.set_position_cnc(tuple(visual_position))

        tlo = self._datasource.getToolOffset()
        tool_tip_world = self._current_tool_tip_world(
            tlo[:3],
            machine_position,
            switchkins_type=current_switchkins_type,
        )
        if self._breadcrumb_world_frame:
            self.tooltip_position = tool_tip_world
        else:
            self.tooltip_position = self._active_path_local_point(tool_tip_world)

        if self.breadcrumbs_plotted and self._should_plot_breadcrumb_for_motion():
            current_tip = tuple(self.tooltip_position[:3])
            self.path_cache_actor.add_line_point(current_tip)
            self._path_cache_seeded = True
            self._last_breadcrumb_world = current_tip
        self._request_render()
        
    def move_part(self, part):
                
        position = part.GetPartPosition()
        pivot = part.GetPartOrigin() if hasattr(part, 'GetPartOrigin') else None
        if pivot is None:
            pivot = position
        machine_position = self.machine_motion_position
        
        part_axis = part.GetPartAxis()
        part_type = part.GetPartType()


        part_transform = vtk.vtkTransform()  
        
        if part_type == "linear":

            #part_position = self.joints[part_joint].input.value
            
            # if part_axis == "x":
            #     part.SetPosition(self.spindle_position[0], 0, 0)
            # elif part_axis == "y":
            #     part.SetPosition(0, self.spindle_position[1], 0)
            # elif part_axis == "z":
            #     part.SetPosition(0, 0, self.spindle_position[2])
            # elif part_axis == "-x":
            #     part.SetPosition(-self.spindle_position[0], 0, 0)
            # elif part_axis == "-y":
            #     part.SetPosition(0, -self.spindle_position[1], 0)
            # elif part_axis == "-z":
            #     part.SetPosition(0, 0, -self.spindle_position[2])
                
            x_delta = self._machine_linear_axis_value('X', machine_position[0])
            y_delta = self._machine_linear_axis_value('Y', machine_position[1])
            z_delta = self._machine_linear_axis_value('Z', machine_position[2])

            if part_axis == "x":
                part_transform.Translate(x_delta, 0, 0)
            elif part_axis == "y":
                part_transform.Translate(0, y_delta, 0)
            elif part_axis == "z":
                part_transform.Translate(0, 0, z_delta)
            elif part_axis == "-x":
                part_transform.Translate(-x_delta, 0, 0)
            elif part_axis == "-y":
                part_transform.Translate(0, -y_delta, 0)
            elif part_axis == "-z":
                part_transform.Translate(0, 0, -z_delta)
            

        elif part_type == "angular":
            
            # part_position = self.joints[part_joint].input.value
            
            # if part_axis == "a":
            #     part.SetOrientation(self.spindle_rotation[0], 0, 0)
            # elif part_axis== "b":
            #     part.SetOrientation(0, self.spindle_rotation[1], 0)
            # elif part_axis == "c":
            #     part.SetOrientation(0, 0, self.spindle_rotation[2])
            # elif part_axis == "-a":
            #     part.SetOrientation(-self.spindle_rotation[0], 0, 0)
            # elif part_axis == "-b":
            #     part.SetOrientation(0, -self.spindle_rotation[1], 0)
            # elif part_axis == "-c":
            #     part.SetOrientation(0, 0, -self.spindle_rotation[2])
 
            part_transform.Translate(pivot[0], pivot[1], pivot[2])

            a_delta = self._machine_angular_axis_value('A', self.spindle_rotation[0])
            b_delta = self._machine_angular_axis_value('B', self.spindle_rotation[1])
            c_delta = self._machine_angular_axis_value('C', self.spindle_rotation[2])
            
            if part_axis == "a":
                part_transform.RotateX(a_delta)
            elif part_axis== "b":
                part_transform.RotateY(b_delta)
            elif part_axis == "c":
                part_transform.RotateZ(c_delta)
            elif part_axis == "-a":
                part_transform.RotateX(-a_delta)
            elif part_axis == "-b":
                part_transform.RotateY(-b_delta)
            elif part_axis == "-c":
                part_transform.RotateZ(-c_delta)  
            
            part_transform.Translate(-pivot[0], -pivot[1], -pivot[2])

            if self._transform_debug_enabled():
                part_name = part.GetPartName() if hasattr(part, 'GetPartName') else '<unknown>'
                pivot_world = part_transform.TransformPoint(pivot[0], pivot[1], pivot[2])
                LOG.debug(
                    "VTK move_part angular: part=%s axis=%s pivot=%s deltas=(A=%.6f,B=%.6f,C=%.6f) "
                    "pivot_world_after=(%.6f, %.6f, %.6f)",
                    part_name,
                    part_axis,
                    pivot,
                    float(a_delta),
                    float(b_delta),
                    float(c_delta),
                    float(pivot_world[0]),
                    float(pivot_world[1]),
                    float(pivot_world[2]),
                )
            
        part.SetUserTransform(part_transform)
        

    def update_joints(self, joints):
        self.joints = joints

    def _set_wcs_offsets(self, offsets):
        if isinstance(offsets, dict):
            self.wcs_offsets = offsets
            return
        if isinstance(offsets, (list, tuple)):
            self.wcs_offsets = {idx: value for idx, value in enumerate(offsets)}
            return
        self.wcs_offsets = {}

    def _offsets_ready(self):
        return bool(self.wcs_offsets)

    def _safe_get_offsets(self, wcs_index, offset_columns=None):
        offsets = None
        if isinstance(self.wcs_offsets, dict):
            offsets = self.wcs_offsets.get(wcs_index)
            if offsets is None and wcs_index != 0:
                offsets = self.wcs_offsets.get(0)
        elif isinstance(self.wcs_offsets, (list, tuple)):
            if 0 <= wcs_index < len(self.wcs_offsets):
                offsets = self.wcs_offsets[wcs_index]

        if offsets is None:
            offsets = [0.0] * 9

        return list(offsets)
        
    def on_offset_table_changed(self, offset_table):
        self._set_wcs_offsets(offset_table)

        self.rotate_and_translate()
        
    def update_rotation_xy(self, rot):
        self.active_rotation = rot
        self.rotation_xy_table[self.active_wcs_index] = rot
        
        self.rotate_and_translate()
        
    def update_g5x_offset(self, offset):
        self.active_wcs_offset = offset
        
        self.rotate_and_translate()
        
        # Future optimization: add rapid-only recalculation path.
        
    def rotate_and_translate(self):
        # self.axes_actor.SetUserTransform(transform)

        for wcs_index, path_actor in self.path_actors.items():

            axes_actor = path_actor.get_axes_actor()

            current_offsets = self._safe_get_offsets(wcs_index, self.offsetTableColumnsIndex)

            x_column = self.offsetTableColumnsIndex.get('X')
            y_column = self.offsetTableColumnsIndex.get('Y')
            z_column = self.offsetTableColumnsIndex.get('Z')
            r_column = self.offsetTableColumnsIndex.get('R')

            if x_column is not None:
                x = current_offsets[x_column]
            else:
                x = 0.0

            if y_column is not None:
                y = current_offsets[y_column]
            else:
                y = 0.0

            if z_column is not None:
                z = current_offsets[z_column]
            else:
                z = 0.0

            if r_column is not None:
                rotation = current_offsets[r_column]
            else:
                rotation = 0.0

            actor_transform = self._compose_wcs_transform(x, y, z, rotation)
            axes_transform = self._compose_wcs_transform(x, y, z, rotation)
            
            # Scale up the axes for the active WCS to provide visual feedback
            if wcs_index == self.active_wcs_index:
                axes_transform.Scale(1.5, 1.5, 1.5)  # Make active WCS axes 50% larger
                self._active_path_transform.DeepCopy(actor_transform)
                if not self._breadcrumb_world_frame:
                    self.path_cache_actor.SetUserTransform(self._active_path_transform)

            axes_actor.SetUserTransform(axes_transform)
            path_actor.SetUserTransform(actor_transform)

            self._sync_program_bounds_actor(wcs_index, path_actor)
        
            xyz = self.active_wcs_offset[:3]
            rotation = self.active_rotation
            _ = xyz, rotation
                           

        if len(self.path_actors) > 1:
            self._update_transition_actors(self.offsetTableColumnsIndex)

        self._request_render()
        
    def update_g5x_index(self, index):
        self.active_wcs_index = index
    
    def update_active_wcs(self, wcs_index):
        self.active_wcs_index = wcs_index
        
        # Update the visual scale of axes to highlight the active WCS
        # This is done by calling rotate_and_translate which will rebuild
        # the scene with the proper scaling for the active WCS
        if len(self.path_actors) > 0:
            self.rotate_and_translate()

    def update_g92_offset(self, g92_offset):
        if self._datasource.isModeMdi() or self._datasource.isModeAuto():
            self.g92_offset = g92_offset

            path_offset = list(map(add, self.g92_offset, self.original_g92_offset))

            for wcs_index, actor in list(self.path_actors.items()):
                # determine change in g92 offset since path was drawn

                current_offsets = self._safe_get_offsets(wcs_index, self.offsetTableColumnsIndex)
                new_path_position = list(map(add, current_offsets[:9], path_offset))

                axes = actor.get_axes_actor()

                path_transform = self._compose_wcs_transform(
                    new_path_position[0],
                    new_path_position[1],
                    new_path_position[2],
                    0.0,
                )

                # self.axes_actor.SetUserTransform(path_transform)
                axes.SetUserTransform(path_transform)
                actor.SetUserTransform(path_transform)

                self._sync_program_bounds_actor(wcs_index, actor)

            self._request_render()

    def update_tool(self):
        self.renderer.RemoveActor(self.tool_actor)
        self.renderer.RemoveActor(self.tool_bit_actor)

        self.tool_actor = ToolActor(self._datasource)
        self.tool_bit_actor = ToolBitActor(self._datasource)

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)
        tool_transform.RotateX(-self.spindle_rotation[0])
        tool_transform.RotateY(-self.spindle_rotation[1])
        tool_transform.RotateZ(-self.spindle_rotation[2])

        self.tool_actor.SetUserTransform(tool_transform)

        if self._is_machine_foam:
            self.renderer.RemoveActor(self.tool_bit_actor)
            self.tool_bit_actor = ToolBitActor(self._datasource)
            self.tool_bit_actor.SetUserTransform(tool_transform)
        else:
            self.tool_bit_actor.SetUserTransform(tool_transform)

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.tool_bit_actor)

        tool_in_spindle = self._tool_in_spindle()
        if tool_in_spindle <= 0:
            self.tool_actor.SetVisibility(1)
            self.tool_bit_actor.SetVisibility(0)
        else:
            self.tool_actor.SetVisibility(1)
            self.tool_bit_actor.SetVisibility(1)

        self._request_render()

    @Slot(bool)
    @Slot(object)
    def viewPerspective(self, persp):
        if persp:
            self.setViewPersp()
        else:
            self.setViewOrtho()

    @Slot(bool)
    @Slot(object)
    def showSpindle(self, value):

        if self.spindle_model:
            self.spindle_actor.SetVisibility(value)
        self._request_render()

    @Slot()
    def setViewOrtho(self):
        self.camera.ParallelProjectionOn()
        self._request_render()

    @Slot()
    def setViewPersp(self):
        self.camera.ParallelProjectionOff()
        self._request_render()

    @Slot(int)
    @Slot(str)
    @Slot(object)
    def setView(self, view):

        if isinstance(view, int):            
            view_options_setting = getSetting("backplot.view").enum_options
            view_options = list()
            
            for option in view_options_setting:
                view_options.append(option.split(':')[0])
            
            view = view_options[view]


        view = view.upper()

        if view == 'X':
            self.setViewX()
        elif view == 'XZ':
            self.setViewXZ()
        elif view == 'XZ2':
            self.setViewXZ2()
        elif view == 'Y':
            self.setViewY()
        elif view == 'Z':
            self.setViewZ()
        elif view == 'Z2':
            self.setViewZ2()
        elif view == 'P':
            self.setViewP()
        elif view == 'M':
            self.setViewMachine()

    @Slot()
    def setViewP(self):
        self.active_view = 'P'

        position_x, position_y, position_z = self._get_active_wcs_xyz()

        self.camera.SetPosition(self.position_mult * self.view_x_vec, 
            self.position_mult * self.view_y_vec, 
            self.position_mult * self.view_z_vec)
        self.camera.SetFocalPoint(position_x, position_y, position_z)
        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewX(self):
        self.active_view = 'X'

        if self.active_wcs_index < 0:
            self.active_wcs_index = 0

        position = self._safe_get_offsets(self.active_wcs_index, self.offsetTableColumnsIndex)
        ot_columns_index = self.offsetTableColumnsIndex
        
        column_x = ot_columns_index.get('X')
        column_y = ot_columns_index.get('Y')
        column_z = ot_columns_index.get('Z')
        
        
        if column_x is not None:
            position_x = position[column_x]
        else:
            position_x = 0.0
            
        if column_y is not None:
            position_y = position[column_y]
        else:
            position_y = 0.0
            
        if column_z is not None:
            position_z = position[column_z]
        else:
            position_z = 0.0
        
        
        self.camera.SetPosition(position_x, position_y - self.position_mult, position_z)
        self.camera.SetFocalPoint((position_x, position_y, position_z))
        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewXZ(self):
        self.active_view = 'XZ'
        self._lathe_plan_view = 'XZ'

        position_x, position_y, position_z = self._get_active_wcs_xyz()

        self.camera.SetPosition(position_x, position_y + self.position_mult, position_z)
        self.camera.SetFocalPoint((position_x, position_y, position_z))
        self.camera.SetViewUp(1, 0, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewXZ2(self):
        self.active_view = 'XZ2'
        self._lathe_plan_view = 'XZ2'

        position_x, position_y, position_z = self._get_active_wcs_xyz()

        self.camera.SetPosition(position_x, position_y - self.position_mult, position_z)
        self.camera.SetFocalPoint((position_x, position_y, position_z))
        self.camera.SetViewUp(-1, 0, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewY(self):
        self.active_view = 'Y'

        position_x, position_y, position_z = self._get_active_wcs_xyz()

        self.camera.SetPosition(position_x + self.position_mult, position_y, position_z)
        self.camera.SetFocalPoint((position_x, position_y, position_z))
        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewZ(self):
        self.active_view = 'Z'

        position_x, position_y, position_z = self._get_active_wcs_xyz()

        self.camera.SetPosition(position_x, position_y, position_z + self.position_mult)
        self.camera.SetFocalPoint((position_x, position_y, position_z))
        self.camera.SetViewUp(0, 1, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewZ2(self):
        self.active_view = 'Z2'

        position_x, position_y, position_z = self._get_active_wcs_xyz()

        self.camera.SetPosition(position_x, position_y, position_z + self.position_mult)
        self.camera.SetFocalPoint((position_x, position_y, position_z))
        self.camera.SetViewUp(1, 0, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewMachine(self):
        previous_view = str(self.active_view).upper() if self.active_view else 'P'
        view_for_fit = previous_view if previous_view in ['X', 'Y', 'Z', 'Z2', 'XZ', 'XZ2'] else 'P'
        self.active_view = 'M'
        machine_bounds = self.machine_actor.GetBounds()
        machine_center = ((machine_bounds[0] + machine_bounds[1]) / 2,
                          (machine_bounds[2] + machine_bounds[3]) / 2,
                          (machine_bounds[4] + machine_bounds[5]) / 2
                          )

        self.camera = self.renderer.GetActiveCamera()

        self.camera.SetFocalPoint(machine_center[0],
                                  machine_center[1],
                                  machine_center[2])

        if self._lathe_mode:
            lathe_view = self._resolve_lathe_plan_view()
            if lathe_view == 'XZ2':
                self.camera.SetPosition(machine_center[0], machine_center[1] - self.position_mult, machine_center[2])
                self.camera.SetViewUp(-1, 0, 0)
            else:
                self.camera.SetPosition(machine_center[0], machine_center[1] + self.position_mult, machine_center[2])
                self.camera.SetViewUp(1, 0, 0)
        else:
            self._set_camera_pose_from_view(machine_center, view_for_fit)
        
        x_dist = abs(machine_bounds[0] - machine_bounds[1])
        y_dist = abs(machine_bounds[2] - machine_bounds[3])
        z_dist = abs(machine_bounds[4] - machine_bounds[5])

        if self._lathe_mode:
            new_scale = self._fit_parallel_scale_for_plane(
                vertical_span=x_dist,
                horizontal_span=z_dist,
                padding=EXTENTS_PADDING
            )
        else:
            new_scale = self._fit_parallel_scale_for_view(
                view_for_fit,
                x_dist,
                y_dist,
                z_dist,
                EXTENTS_PADDING
            )

        self.camera.SetParallelScale(new_scale)

        if not self.camera.GetParallelProjection():
            self._move_camera_to_perspective_fit(machine_center, x_dist, y_dist, z_dist)

        if not self._lathe_mode and view_for_fit == 'P':
            self.camera.SetViewUp(0, 0, 1)
        
        self.__doCommonSetViewWork()

    @Slot()
    def setViewProgram(self,view='p'):
        if not self._lathe_mode and str(view).lower() == 'p':
            current_view = str(self.active_view).upper() if self.active_view else 'P'
            if current_view in ['X', 'Y', 'Z', 'Z2', 'XZ', 'XZ2']:
                view = current_view.lower()

        if self._lathe_mode and str(view).lower() == 'p':
            view = self._resolve_lathe_plan_view().lower()
        
        if len(self.program_bounds_actors) == 0:
            return

        program_bounds_actor = self._get_active_program_bounds_actor()
        if program_bounds_actor is None:
            LOG.warning('-----setViewProgram skipped, no active wcs')
            return

        program_bounds = program_bounds_actor.GetBounds()
        resolved_index = self.active_wcs_index if self.active_wcs_index >= 0 else 0
        if self._is_program_bounds_outlier(resolved_index, program_bounds):
            shifted_bounds = self._get_shifted_reference_program_bounds(resolved_index)
            if shifted_bounds is not None:
                program_bounds = shifted_bounds

        program_center = ((program_bounds[0] + program_bounds[1]) / 2,
                          (program_bounds[2] + program_bounds[3]) / 2,
                          (program_bounds[4] + program_bounds[5]) / 2)

        self.camera = self.renderer.GetActiveCamera()
        self.camera.SetFocalPoint(program_center[0],
                                  program_center[1],
                                  program_center[2])

        # self.camera.SetPosition(program_center[0] + self.position_mult,
        #                         -(program_center[1] + self.position_mult),
        #                         program_center[2] + self.position_mult)


        self._set_camera_pose_from_view(program_center, view)

        x_dist = abs(program_bounds[0] - program_bounds[1])
        y_dist = abs(program_bounds[2] - program_bounds[3])
        z_dist = abs(program_bounds[4] - program_bounds[5])

        scale = self._fit_program_parallel_scale(view, x_dist, y_dist, z_dist)

        self.camera.SetParallelScale(scale)

        if not self.camera.GetParallelProjection():
            self._move_camera_to_perspective_fit(program_center, x_dist, y_dist, z_dist)
        self.__doCommonSetViewWork()
        self.clearLivePlot()



    @Slot()
    def setViewPath(self):
        position_x, position_y, position_z = self._get_active_wcs_xyz()

        if self._lathe_mode:
            lathe_view = self._resolve_lathe_plan_view()
            if lathe_view == 'XZ2':
                self.camera.SetPosition(position_x, position_y - self.position_mult, position_z)
                self.camera.SetViewUp(-1, 0, 0)
            else:
                self.camera.SetPosition(position_x, position_y + self.position_mult, position_z)
                self.camera.SetViewUp(1, 0, 0)
        else:
            self.camera.SetPosition((position_x + self.position_mult) * self.view_x_vec,
                                    (position_y + self.position_mult) * self.view_y_vec,
                                    (position_z + self.position_mult) * self.view_z_vec)

        self.camera.SetFocalPoint(position_x, position_y, position_z)
        if not self._lathe_mode:
            self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    def __doCommonSetViewWork(self):
        # This is common logic for all setView**** methods.
        self.camera.SetClippingRange(self.clipping_range_near, self.clipping_range_far)
        self._request_render()

    def _render_now(self):
        self._render_scheduled = False
        self.renderer_window.Render()

    def _request_render(self):
        if self._render_scheduled:
            return
        self._render_scheduled = True
        QTimer.singleShot(0, self._render_now)

    def _render_frame(self, interactive=False):
        if interactive:
            self._render_scheduled = False
            self.renderer_window.Render()
            return
        self._request_render()

    def _sync_program_bounds_actor(self, wcs_index, path_actor):
        program_bounds_actor = self.program_bounds_actors.get(wcs_index)

        if program_bounds_actor is None:
            program_bounds_actor = ProgramBoundsActor(self.camera, path_actor)
            self.program_bounds_actors[wcs_index] = program_bounds_actor
            self.renderer.AddActor(program_bounds_actor)
        else:
            x_min, x_max, y_min, y_max, z_min, z_max = path_actor.GetBounds()
            program_bounds_actor.SetCamera(self.camera)
            program_bounds_actor.SetBounds(x_min, x_max, y_min, y_max, z_min, z_max)
            program_bounds_actor.SetUseRanges(1)
            program_bounds_actor.SetRanges(0, x_max - x_min, 0, y_max - y_min, 0, z_max - z_min)

        program_bounds_actor.showProgramBounds(self.show_program_bounds)
        return program_bounds_actor

    def _make_wcs_transform(self, wcs_index, offset_columns):
        current_offsets = self._safe_get_offsets(wcs_index, offset_columns)

        x_column = offset_columns.get('X')
        y_column = offset_columns.get('Y')
        z_column = offset_columns.get('Z')
        r_column = offset_columns.get('R')

        x = current_offsets[x_column] if x_column is not None and x_column < len(current_offsets) else 0.0
        y = current_offsets[y_column] if y_column is not None and y_column < len(current_offsets) else 0.0
        z = current_offsets[z_column] if z_column is not None and z_column < len(current_offsets) else 0.0
        rotation = current_offsets[r_column] if r_column is not None and r_column < len(current_offsets) else 0.0

        return self._compose_wcs_transform(x, y, z, rotation)

    def _make_transition_point_actor(self, point_position, color_rgb, actor_transform):
        points = vtk.vtkPoints()
        vertices = vtk.vtkCellArray()

        point_id = [0]
        point_id[0] = points.InsertNextPoint(point_position)
        vertices.InsertNextCell(1, point_id)

        point_poly = vtk.vtkPolyData()
        point_poly.SetPoints(points)
        point_poly.SetVerts(vertices)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(point_poly)

        actor_point = vtk.vtkActor()
        actor_point.SetMapper(mapper)
        actor_point.GetProperty().SetColor(color_rgb)
        actor_point.GetProperty().SetPointSize(5)
        actor_point.SetUserTransform(actor_transform)
        return actor_point

    def _make_transition_line_actor(self, from_position, to_position):
        actor_p01_pos = [from_position[0], from_position[1], from_position[2]]
        actor_p02_pos = [to_position[0], to_position[1], to_position[2]]
        actor_p03_pos = [to_position[0], to_position[1], from_position[2]]

        pts = vtk.vtkPoints()
        pts.InsertNextPoint(*actor_p01_pos)
        pts.InsertNextPoint(*actor_p03_pos)
        pts.InsertNextPoint(*actor_p02_pos)

        line = vtk.vtkPolyData()
        line.SetPoints(pts)

        line0 = vtk.vtkLine()
        line0.GetPointIds().SetId(0, 0)
        line0.GetPointIds().SetId(1, 1)

        line1 = vtk.vtkLine()
        line1.GetPointIds().SetId(0, 1)
        line1.GetPointIds().SetId(1, 2)

        lines = vtk.vtkCellArray()
        lines.InsertNextCell(line0)
        lines.InsertNextCell(line1)
        line.SetLines(lines)

        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)
        colors.InsertNextTypedTuple(self.path_colors.get("traverse").getRgb()[0:3])
        colors.InsertNextTypedTuple(self.path_colors.get("traverse").getRgb()[0:3])
        line.GetCellData().SetScalars(colors)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(line)

        actor_line = vtk.vtkActor()
        actor_line.SetMapper(mapper)
        actor_line.GetProperty().SetLineWidth(1)
        return actor_line

    def _transform_transition_point(self, wcs_index, local_point, offset_columns):
        transform = self._make_wcs_transform(wcs_index, offset_columns)
        return transform.TransformPoint(local_point[0], local_point[1], local_point[2])

    def _rebuild_transition_actors(self, offset_columns):
        if len(self.offset_transitions) == 0:
            return

        for transition_index, transition in enumerate(self.offset_transitions):
            from_wcs = transition['from_wcs']
            to_wcs = transition['to_wcs']
            from_end = transition['from_end']
            to_start = transition['to_start']

            from_transform = self._make_wcs_transform(from_wcs, offset_columns)
            to_transform = self._make_wcs_transform(to_wcs, offset_columns)

            start_actor = self._make_transition_point_actor(
                to_start,
                self.path_colors.get("arcfeed").getRgb()[0:3],
                to_transform
            )
            end_actor = self._make_transition_point_actor(
                from_end,
                self.path_colors.get("user").getRgb()[0:3],
                from_transform
            )

            self.offset_change_start_actor[transition_index] = start_actor
            self.offset_change_end_actor[transition_index] = end_actor

            self.renderer.AddActor(start_actor)
            self.renderer.AddActor(end_actor)

            from_world = self._transform_transition_point(from_wcs, from_end, offset_columns)
            to_world = self._transform_transition_point(to_wcs, to_start, offset_columns)

            line_actor = self._make_transition_line_actor(from_world, to_world)
            self.offset_change_line_actor[transition_index] = line_actor
            self.renderer.AddActor(line_actor)

    def _update_transition_actors(self, offset_columns):
        if len(self.offset_transitions) == 0:
            return

        for line_actor in self.offset_change_line_actor.values():
            if line_actor:
                self.renderer.RemoveActor(line_actor)
        self.offset_change_line_actor.clear()

        for transition_index, transition in enumerate(self.offset_transitions):
            from_wcs = transition['from_wcs']
            to_wcs = transition['to_wcs']
            from_end = transition['from_end']
            to_start = transition['to_start']

            start_actor = self.offset_change_start_actor.get(transition_index)
            end_actor = self.offset_change_end_actor.get(transition_index)

            if start_actor is None or end_actor is None:
                continue

            start_actor.SetUserTransform(self._make_wcs_transform(to_wcs, offset_columns))
            end_actor.SetUserTransform(self._make_wcs_transform(from_wcs, offset_columns))

            from_world = self._transform_transition_point(from_wcs, from_end, offset_columns)
            to_world = self._transform_transition_point(to_wcs, to_start, offset_columns)

            new_line_actor = self._make_transition_line_actor(from_world, to_world)
            self.offset_change_line_actor[transition_index] = new_line_actor
            self.renderer.AddActor(new_line_actor)

    def _get_wcs_offset_xyz(self, wcs_index):
        offsets = self._safe_get_offsets(wcs_index, self.offsetTableColumnsIndex)
        if not offsets or len(offsets) < 3:
            return None
        return offsets[0], offsets[1], offsets[2]

    @staticmethod
    def _bounds_size(bounds):
        return (
            abs(bounds[1] - bounds[0]),
            abs(bounds[3] - bounds[2]),
            abs(bounds[5] - bounds[4]),
        )

    @staticmethod
    def _median(values):
        ordered = sorted(values)
        size = len(ordered)
        if size == 0:
            return 0.0
        mid = size // 2
        if size % 2 == 1:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2.0

    def _is_program_bounds_outlier(self, active_index, active_bounds):
        if len(self.program_bounds_actors) < 2:
            return False

        reference_sizes = []
        for wcs_index, bounds_actor in self.program_bounds_actors.items():
            if wcs_index == active_index:
                continue
            bounds = bounds_actor.GetBounds()
            sx, sy, sz = self._bounds_size(bounds)
            if sx > 0.0 and sy > 0.0 and sz > 0.0:
                reference_sizes.append((sx, sy, sz))

        if not reference_sizes:
            return False

        median_x = self._median([size[0] for size in reference_sizes])
        median_y = self._median([size[1] for size in reference_sizes])
        median_z = self._median([size[2] for size in reference_sizes])

        active_x, active_y, active_z = self._bounds_size(active_bounds)

        enlarged_axes = 0
        if median_x > 0.0 and active_x > (median_x * 1.6):
            enlarged_axes += 1
        if median_y > 0.0 and active_y > (median_y * 1.6):
            enlarged_axes += 1
        if median_z > 0.0 and active_z > (median_z * 1.6):
            enlarged_axes += 1

        return enlarged_axes >= 2

    def _get_shifted_reference_program_bounds(self, active_index):
        active_offset = self._get_wcs_offset_xyz(active_index)
        if active_offset is None:
            return None

        best_choice = None

        for wcs_index, bounds_actor in self.program_bounds_actors.items():
            if wcs_index == active_index:
                continue

            reference_offset = self._get_wcs_offset_xyz(wcs_index)
            if reference_offset is None:
                continue

            bounds = bounds_actor.GetBounds()
            sx, sy, sz = self._bounds_size(bounds)
            if sx <= 0.0 or sy <= 0.0 or sz <= 0.0:
                continue

            dx = active_offset[0] - reference_offset[0]
            dy = active_offset[1] - reference_offset[1]
            dz = active_offset[2] - reference_offset[2]
            offset_distance_sq = (dx * dx) + (dy * dy) + (dz * dz)

            if best_choice is None or offset_distance_sq < best_choice[0]:
                best_choice = (offset_distance_sq, bounds, dx, dy, dz)

        if best_choice is None:
            return None

        _, bounds, dx, dy, dz = best_choice
        return (
            bounds[0] + dx,
            bounds[1] + dx,
            bounds[2] + dy,
            bounds[3] + dy,
            bounds[4] + dz,
            bounds[5] + dz,
        )

    def _get_active_program_bounds_actor(self):
        if len(self.program_bounds_actors) == 0:
            return None

        active_index = self.active_wcs_index
        if active_index < 0:
            active_index = 0

        if active_index in self.program_bounds_actors:
            return self.program_bounds_actors[active_index]

        if active_index + 1 in self.program_bounds_actors and 0 not in self.program_bounds_actors:
            return self.program_bounds_actors[active_index + 1]

        if 0 in self.program_bounds_actors:
            return self.program_bounds_actors[0]

        fallback_key = min(self.program_bounds_actors.keys())
        return self.program_bounds_actors[fallback_key]

    def _get_active_wcs_xyz(self):
        if self.active_wcs_index < 0:
            self.active_wcs_index = 0

        position = self._safe_get_offsets(self.active_wcs_index, self.offsetTableColumnsIndex)
        ot_columns_index = self.offsetTableColumnsIndex

        column_x = ot_columns_index.get('X') if ot_columns_index else None
        column_y = ot_columns_index.get('Y') if ot_columns_index else None
        column_z = ot_columns_index.get('Z') if ot_columns_index else None

        position_x = position[column_x] if column_x is not None and column_x < len(position) else 0.0
        position_y = position[column_y] if column_y is not None and column_y < len(position) else 0.0
        position_z = position[column_z] if column_z is not None and column_z < len(position) else 0.0
        return position_x, position_y, position_z

    def _set_camera_pose_from_view(self, center, view):
        cx, cy, cz = center
        view_name = str(view).lower()

        if view_name == 'x':
            self.camera.SetPosition(cx, cy - self.position_mult, cz)
            self.camera.SetViewUp(0, 0, 1)
        elif view_name == 'y':
            self.camera.SetPosition(cx + self.position_mult, cy, cz)
            self.camera.SetViewUp(0, 0, 1)
        elif view_name == 'z':
            self.camera.SetPosition(cx, cy, cz + self.position_mult)
            self.camera.SetViewUp(0, 1, 0)
        elif view_name == 'z2':
            self.camera.SetPosition(cx, cy, cz + self.position_mult)
            self.camera.SetViewUp(1, 0, 0)
        elif view_name == 'xz':
            self.camera.SetPosition(cx, cy + self.position_mult, cz)
            self.camera.SetViewUp(1, 0, 0)
        elif view_name == 'xz2':
            self.camera.SetPosition(cx, cy - self.position_mult, cz)
            self.camera.SetViewUp(-1, 0, 0)
        else:
            self.camera.SetPosition((cx + self.position_mult) * self.view_x_vec,
                                    (cy + self.position_mult) * self.view_y_vec,
                                    (cz + self.position_mult) * self.view_z_vec)
            self.camera.SetViewUp(0, 0, 1)

    def _resolve_lathe_plan_view(self):
        return self._lathe_plan_view if self._lathe_plan_view in ['XZ', 'XZ2'] else ('XZ' if self._back_tool_lathe else 'XZ2')

    def _move_camera_to_perspective_fit(self, center, x_span, y_span, z_span):
        distance = self._fit_perspective_distance_for_bounds(
            x_span=x_span,
            y_span=y_span,
            z_span=z_span,
            padding=EXTENTS_PADDING
        )

        cx, cy, cz = center
        px, py, pz = self.camera.GetPosition()
        dx = px - cx
        dy = py - cy
        dz = pz - cz
        mag = math.sqrt(dx * dx + dy * dy + dz * dz)
        if mag < 1e-9:
            dx, dy, dz = self.view_x_vec, self.view_y_vec, self.view_z_vec
            mag = math.sqrt(dx * dx + dy * dy + dz * dz)
        ux, uy, uz = dx / mag, dy / mag, dz / mag
        self.camera.SetPosition(cx + ux * distance, cy + uy * distance, cz + uz * distance)

    def _fit_program_parallel_scale(self, view, x_span, y_span, z_span):
        view_name = str(view).lower()

        if self._lathe_mode:
            if view_name in ['x', 'xz', 'xz2']:
                return self._fit_parallel_scale_for_plane(
                    vertical_span=x_span,
                    horizontal_span=z_span,
                    padding=EXTENTS_PADDING
                )
            if view_name == 'y':
                return self._fit_parallel_scale_for_plane(
                    vertical_span=z_span,
                    horizontal_span=y_span,
                    padding=EXTENTS_PADDING
                )
            if view_name in ['z', 'z2']:
                return self._fit_parallel_scale_for_plane(
                    vertical_span=x_span,
                    horizontal_span=y_span,
                    padding=EXTENTS_PADDING
                )

        return self._fit_parallel_scale_for_view(view_name, x_span, y_span, z_span, EXTENTS_PADDING)

    def _fit_parallel_scale_for_plane(self, vertical_span, horizontal_span, padding=EXTENTS_PADDING):

        size = self.renderer_window.GetSize()
        width = float(size[0]) if size and size[0] else 1.0
        height = float(size[1]) if size and size[1] else 1.0
        aspect = width / height if height > 0.0 else 1.0

        half_vertical = max(float(vertical_span), 0.0) * 0.5
        half_horizontal = max(float(horizontal_span), 0.0) * 0.5
        required = max(half_vertical, half_horizontal / max(aspect, 1e-6))

        return required * max(float(padding), 1.0)

    def _fit_parallel_scale_for_view(self, view, x_span, y_span, z_span, padding=EXTENTS_PADDING):

        view_name = str(view).lower()
        if view_name == 'x':
            return self._fit_parallel_scale_for_plane(z_span, x_span, padding)
        if view_name == 'y':
            return self._fit_parallel_scale_for_plane(z_span, y_span, padding)
        if view_name == 'z':
            return self._fit_parallel_scale_for_plane(y_span, x_span, padding)
        if view_name == 'z2':
            return self._fit_parallel_scale_for_plane(x_span, y_span, padding)
        if view_name in ['xz', 'xz2']:
            return self._fit_parallel_scale_for_plane(x_span, z_span, padding)

        return self._fit_parallel_scale_for_isometric(x_span, y_span, z_span, padding)

    def _fit_parallel_scale_for_isometric(self, x_span, y_span, z_span, padding=EXTENTS_PADDING):
        focal = self.camera.GetFocalPoint()
        position = self.camera.GetPosition()
        view_up = self.camera.GetViewUp()

        view_dir_x = focal[0] - position[0]
        view_dir_y = focal[1] - position[1]
        view_dir_z = focal[2] - position[2]
        view_dir_mag = math.sqrt((view_dir_x * view_dir_x) + (view_dir_y * view_dir_y) + (view_dir_z * view_dir_z))
        if view_dir_mag <= 1e-9:
            view_dir_x, view_dir_y, view_dir_z = self.view_x_vec, self.view_y_vec, self.view_z_vec
            view_dir_mag = math.sqrt((view_dir_x * view_dir_x) + (view_dir_y * view_dir_y) + (view_dir_z * view_dir_z))

        view_dir_x /= view_dir_mag
        view_dir_y /= view_dir_mag
        view_dir_z /= view_dir_mag

        up_x, up_y, up_z = view_up
        up_mag = math.sqrt((up_x * up_x) + (up_y * up_y) + (up_z * up_z))
        if up_mag <= 1e-9:
            up_x, up_y, up_z = 0.0, 0.0, 1.0
            up_mag = 1.0

        up_x /= up_mag
        up_y /= up_mag
        up_z /= up_mag

        right_x = (view_dir_y * up_z) - (view_dir_z * up_y)
        right_y = (view_dir_z * up_x) - (view_dir_x * up_z)
        right_z = (view_dir_x * up_y) - (view_dir_y * up_x)
        right_mag = math.sqrt((right_x * right_x) + (right_y * right_y) + (right_z * right_z))
        if right_mag <= 1e-9:
            return max(float(x_span), float(y_span), float(z_span)) * 0.5 * max(float(padding), 1.0)

        right_x /= right_mag
        right_y /= right_mag
        right_z /= right_mag

        up_x = (right_y * view_dir_z) - (right_z * view_dir_y)
        up_y = (right_z * view_dir_x) - (right_x * view_dir_z)
        up_z = (right_x * view_dir_y) - (right_y * view_dir_x)
        up_mag = math.sqrt((up_x * up_x) + (up_y * up_y) + (up_z * up_z))
        if up_mag > 1e-9:
            up_x /= up_mag
            up_y /= up_mag
            up_z /= up_mag

        vertical_span = (
            abs(up_x) * float(x_span)
            + abs(up_y) * float(y_span)
            + abs(up_z) * float(z_span)
        )
        horizontal_span = (
            abs(right_x) * float(x_span)
            + abs(right_y) * float(y_span)
            + abs(right_z) * float(z_span)
        )

        projection_safety = 1.01
        vertical_span *= projection_safety
        horizontal_span *= projection_safety

        return self._fit_parallel_scale_for_plane(vertical_span, horizontal_span, padding)

    def _fit_perspective_distance_for_bounds(self, x_span, y_span, z_span, padding=EXTENTS_PADDING):

        x_span = max(float(x_span), 0.0)
        y_span = max(float(y_span), 0.0)
        z_span = max(float(z_span), 0.0)

        half_diagonal = 0.5 * math.sqrt(x_span * x_span + y_span * y_span + z_span * z_span)
        if half_diagonal <= 0.0:
            return self.position_mult

        size = self.renderer_window.GetSize()
        width = float(size[0]) if size and size[0] else 1.0
        height = float(size[1]) if size and size[1] else 1.0
        aspect = width / height if height > 0.0 else 1.0

        fov_deg = max(float(self.camera.GetViewAngle()), 1.0)
        half_vfov = math.radians(fov_deg) * 0.5
        half_hfov = math.atan(math.tan(half_vfov) * max(aspect, 1e-6))
        limiting_half_fov = min(half_vfov, half_hfov)

        distance = half_diagonal / max(math.sin(limiting_half_fov), 1e-6)
        return distance * max(float(padding), 1.0)

    @Slot()
    def printView(self):
        pass

    @Slot()
    def clearLivePlot(self):
        self.renderer.RemoveActor(self.path_cache_actor)
        self.path_cache_actor = PathCacheActor(tuple(self.tooltip_position[:3]))
        if not self._breadcrumb_world_frame:
            self.path_cache_actor.SetUserTransform(self._active_path_transform)
        self.renderer.AddActor(self.path_cache_actor)
        self._breadcrumbs_armed = False
        self._path_cache_seeded = False
        self._last_breadcrumb_world = tuple(self.tooltip_position[:3])
        self._request_render()

    @Slot(bool)
    def enableBreadcrumbs(self, enable):
        self.breadcrumbs_plotted = enable

    @Slot(bool)
    def enable_panning(self, enabled):
        self.pan_mode = enabled

    @Slot(bool)
    def enableMultiTouch(self, enabled):
        self.touch_enabled = enabled

    @Slot(bool)
    def setProgramViewWhenLoadingProgram(self, enabled, view='p'):
        self.program_view_when_loading_program = enabled
        self.program_view_when_loading_program_view = view

    @Slot()
    def zoomIn(self):
        if self.camera.GetParallelProjection():
            parallelScale = self.camera.GetParallelScale() * 0.9
            self.camera.SetParallelScale(parallelScale)
        else:
            self.renderer.ResetCameraClippingRange()
            self.camera.Zoom(1.1)

        self._render_frame(interactive=True)

    @Slot()
    def zoomOut(self):
        if self.camera.GetParallelProjection():
            parallelScale = self.camera.GetParallelScale() * 1.1
            self.camera.SetParallelScale(parallelScale)
        else:
            self.renderer.ResetCameraClippingRange()
            self.camera.Zoom(0.9)

        self._render_frame(interactive=True)

    @Slot(bool)
    def alphaBlend(self, alpha):
        pass

    @Slot(bool)
    @Slot(object)
    def showSurface(self, surface):
        self.points_surface_actor.showSurface(surface)
        self._request_render()

    @Slot(bool)
    @Slot(object)
    def showGrid(self, grid):
        self.machine_actor.showGridlines(grid)
        self._request_render()

    @Slot(bool)
    @Slot(object)
    def showProgramBounds(self, show):
        self.show_program_bounds = show
        for wcs_index, actor in list(self.path_actors.items()):
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            if program_bounds_actor is not None:
                program_bounds_actor.showProgramBounds(self.show_program_bounds)
        self._request_render()

    @Slot()
    def toggleProgramBounds(self):
        for wcs_index, actor in list(self.path_actors.items()):
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            self.showProgramBounds(not program_bounds_actor.GetXAxisVisibility())

    @Slot(bool)
    @Slot(object)
    def showMachineBounds(self, bounds):
        self.machine_actor.showMachineBounds(bounds)
        self._request_render()

    @Slot()
    def toggleMachineBounds(self):
        self.showMachineBounds(not self.machine_actor.GetXAxisVisibility())

    @Slot(bool)
    @Slot(object)
    def showMachineTicks(self, ticks):
        self.machine_actor.showMachineTicks(ticks)
        self._request_render()

    @Slot()
    def toggleMachineTicks(self):
        self.showMachineTicks(not self.machine_actor.GetXAxisTickVisibility())

    @Slot(bool)
    @Slot(object)
    def showMachineLabels(self, labels):
        self.machine_actor.showMachineLabels(labels)
        self._request_render()

    @Slot()
    def toggleMachineLabels(self):
        self.showMachineLabels(not self.machine_actor.GetXAxisLabelVisibility())

    @Slot(bool)
    @Slot(object)
    def showMultiColorPath(self, color):
        pass

    @Slot()
    def toggleMultiColorPath(self):
        pass

    # Function to hide all parts of an assembly
    def hide_all_parts(self, assembly):
        parts = assembly.GetParts()
        parts.InitTraversal()
        part = parts.GetNextProp3D()
        while part:
            if isinstance(part, vtk.vtkActor):
                part.VisibilityOff()
            elif isinstance(part, vtk.vtkAssembly):
                self.hide_all_parts(part)
            part = parts.GetNextProp3D()

    def show_all_parts(self, assembly):
        parts = assembly.GetParts()
        parts.InitTraversal()
        part = parts.GetNextProp3D()
        while part:
            if isinstance(part, vtk.vtkActor):
                part.VisibilityOn()
            elif isinstance(part, vtk.vtkAssembly):
                self.show_all_parts(part)
            part = parts.GetNextProp3D()

    @Slot(bool)
    @Slot(object)
    def showMachine(self, value):
        if value:
            self.show_all_parts(self.machine_parts_actor)
        else:
            self.hide_all_parts(self.machine_parts_actor)

        self._request_render()


    @Property(QColor)
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self._background_color = color

        self.renderer.SetBackground(color.getRgbF()[:3])
        self._request_render()

    @backgroundColor.reset
    def backgroundColor(self):
        self._background_color = QColor(0, 0, 0)

        self.renderer.GradientBackgroundOff()
        self._request_render()


    @Property(QColor)
    def backgroundColor2(self):
        return self._background_color2

    @backgroundColor2.setter
    def backgroundColor2(self, color2):
        self._background_color2 = color2

        self.renderer.GradientBackgroundOn()
        self.renderer.SetBackground2(color2.getRgbF()[:3])
        self._request_render()

    @backgroundColor2.reset
    def backgroundColor2(self):
        self._background_color2 = QColor(0, 0, 0)

        self.renderer.GradientBackgroundOff()
        self._request_render()

    @Property(bool)
    def enableProgramTicks(self):
        return self._enableProgramTicks

    @enableProgramTicks.setter
    def enableProgramTicks(self, enable):
        self._enableProgramTicks = enable

    # Traverse color property

    @Property(QColor)
    def traverseColor(self):
        return self._traverse_color

    @traverseColor.setter
    def traverseColor(self, color):
        self._traverse_color = color

    @traverseColor.reset
    def traverseColor(self):
        self._traverse_color = self._default_traverse_color

    # Arcfeed color property

    @Property(QColor)
    def arcfeedColor(self):
        return self._arcfeed_color

    @arcfeedColor.setter
    def arcfeedColor(self, color):
        self._arcfeed_color = color

    @arcfeedColor.reset
    def arcfeedColor(self):
        self._arcfeed_color = self._default_arcfeed_color

    # Feed color property

    @Property(QColor)
    def feedColor(self):
        return self._feed_color

    @feedColor.setter
    def feedColor(self, color):
        self._feed_color = color

    @feedColor.reset
    def feedColor(self):
        self._feed_color = self._default_feed_color

    # Dwell color property

    @Property(QColor)
    def dwellColor(self):
        return self._dwel_color

    @dwellColor.setter
    def dwellColor(self, color):
        self._dwel_color = color

    @dwellColor.reset
    def dwellColor(self):
        self._dwel_color = self._default_dwell_color

    # User color property

    @Property(QColor)
    def userColor(self):
        return self._user_color

    @userColor.setter
    def userColor(self, color):
        self._user_color = color

    @userColor.reset
    def userColor(self):
        self._user_color = self._default_user_color
