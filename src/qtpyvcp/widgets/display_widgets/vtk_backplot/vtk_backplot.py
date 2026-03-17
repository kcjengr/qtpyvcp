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

import math
import os
import time
import logging
import shutil
from collections import OrderedDict

import gcode
import linuxcnc
import vtk
import yaml
from PySide6.QtCore import QObject, Property, QEvent, Qt, QTimer, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget
from vtkmodules.vtkCommonCore import VTK_VERSION_NUMBER, vtkVersion

IN_DESIGNER = os.getenv("DESIGNER", False)

# Qt6-friendly VTK widget setup: use QWidget base for the interactor
if not IN_DESIGNER:
    import vtkmodules.qt as vtk_qt

    vtk_qt.QVTKRWIBase = "QWidget"
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    from vtkmodules.vtkInteractionWidgets import vtkCameraOrientationWidget
else:
    QVTKRenderWindowInteractor = QWidget

from qtpyvcp import actions
from qtpyvcp.native.backplot_cpp import build_backplot_from_file
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.load_perf_summary import PROGRAM_LOAD_PERF_SUMMARY
from qtpyvcp.utilities.settings import connectSetting, getSetting
from qtpyvcp.widgets import VCPWidget

from .axes_actor import AxesActor
from .base_backplot import BaseBackPlot
from .linuxcnc_datasource import LinuxCncDataSource
from .machine_actor import MachineCubeActor, MachineLineActor, MachinePartsASM
from .path_cache_actor import PathCacheActor
from .points_surface import PointsSurfaceActor
from .program_bounds_actor import ProgramBoundsActor
from .spindle_actor import SpindleActor
from .table_actor import TableActor
from .tool_actor import ToolActor, ToolBitActor
from .vtk_canon import COLOR_MAP, VTKCanon

LOG = logger.getLogger(__name__)

NUMBER_OF_WCS = 9
EXTENTS_PADDING = 1.1

KINEMATICS_GANTRY_XYZ = "gantry_xyz"
KINEMATICS_GANTRY_FIXED_Y = "gantry_fixed_y"
KINEMATICS_VMC_TABLE_XY = "vmc_table_xy"

KINEMATICS_ALIASES = {
    "gantry_xyz": KINEMATICS_GANTRY_XYZ,
    "3_axis_gantry": KINEMATICS_GANTRY_XYZ,
    "gantry": KINEMATICS_GANTRY_XYZ,
    "gantry_fixed_y": KINEMATICS_GANTRY_FIXED_Y,
    "3_axis_gantry_fixed_y": KINEMATICS_GANTRY_FIXED_Y,
    "vmc_table_xy": KINEMATICS_VMC_TABLE_XY,
    "3_axis_vmc": KINEMATICS_VMC_TABLE_XY,
    "vmc": KINEMATICS_VMC_TABLE_XY,
}

# TODO: check this with PySide6

# turn on antialiasing
# from PySide6.QtOpenGL import Forma
# f = QGLFormat()
# f.setSampleBuffers(True)
# f.setSamples(8)  # Request 8x antialiasing (adjustable)
# QGLFormat.setDefaultFormat(f)


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
        super().__init__(parent)
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
        if event is not None and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
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

            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
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
        
        # Disable VTK debug warnings (only if VTK is available)
        if not IN_DESIGNER:
            vtk.vtkObject.GlobalWarningDisplayOff()

        self._datasource = LinuxCncDataSource()

        self._is_machine_lathe = self._datasource.isMachineLathe()
        self._is_machine_foam = self._datasource.isMachineFoam()
        self._is_machine_jet = self._datasource.isMachineJet()

        self.kinematics_type = self._resolve_kinematics_type(self._datasource.getKinematicsType())
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

        cpp_backplot_val = str(inifile.find("VTK", "CPP_BACKPLOT") or "1").strip().lower()
        cpp_backplot_requested = cpp_backplot_val in ("1", "true", "yes", "on")
        has_table_rotary = any(self.axis_motion_owner.get(axis, 'tool') == 'table' for axis in ('A', 'B', 'C'))
        # Prefer Python backplot for table-rotary kinematics so program paths
        # can include kinematics-aware shaping during load, not only at runtime.
        self._use_cpp_backplot = bool(cpp_backplot_requested and not has_table_rotary)

        self._lathe_mode = (lathe_val not in ["0", "false", "no", "n", ""]) or (back_tool_val not in ["0", "false", "no", "n", ""])
        self._back_tool_lathe = back_tool_val not in ["0", "false", "no", "n", ""]
        
        # Keyboard jogging is handled at the global level.
        if self._datasource.getKeyboardJog().lower() in ['true', '1', 't', 'y', 'yes']:
            jog_safety_off = self._datasource.getKeyboardJogLock().lower() in ['true', '1', 't', 'y', 'yes']
            event_filter = InteractorEventFilter(self, jog_safety_off)
            self.installEventFilter(event_filter)
            # Ensure this widget does not keep focus after mouse clicks
            self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.current_time = round(time.time() * 1000)
        self.plot_interval = 1000/self._datasource.getFPS()  # 1 second / 30 fps
        self.prev_plot_time = 0
        
        self.parent = parent
        self.ploter_enabled = True
        self.touch_enabled = False
        # provide a control to UI builders to suppress when line "breadcrumbs" are plotted
        self.breadcrumbs_plotted = True

        try:
            self.machine_ext_scale = getSetting("backplot.machine-ext-scale").value
        except Exception:
            self.machine_ext_scale = 1.0
        
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
        self.joints = self._datasource._status.joint

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
        
        if not IN_DESIGNER:
            self.joints = self._datasource._status.joint

        self.foam_offset = [0.0, 0.0]

        if not IN_DESIGNER:
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
            # Cache live points in path-local coordinates and transform the
            # actor with the same active WCS/table transform as program paths.
            self.path_cache_actor = PathCacheActor(tuple(self.tooltip_position[:3]))
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
                        inferred_origins = self._extract_rotary_axis_origins(self.machine_parts_data)
                        for axis_name, origin in inferred_origins.items():
                            if self.rotary_axis_origin.get(axis_name) is None:
                                self.rotary_axis_origin[axis_name] = origin

                        LOG.debug(
                            "VTK rotary setup: owners=%s origins=%s inferred_machine_part_origins=%s",
                            self.axis_motion_owner,
                            self.rotary_axis_origin,
                            inferred_origins,
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

            diagnostics_enabled = False
            try:
                display_log_level = str(self._datasource._inifile.find("DISPLAY", "LOG_LEVEL") or "").strip().upper()
                diagnostics_enabled = display_log_level == "DEBUG"
            except Exception:
                diagnostics_enabled = False

            if not diagnostics_enabled:
                try:
                    diagnostics_enabled = LOG.isEnabledFor(10)
                except Exception:
                    diagnostics_enabled = False

            if diagnostics_enabled:
                try:
                    def _extract_gl_version_pair(version_text):
                        if not version_text:
                            return None
                        text = str(version_text)
                        for token in text.replace("(", " ").replace(")", " ").split():
                            parts = token.split(".")
                            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                                return int(parts[0]), int(parts[1])
                        return None

                    def _infer_glsl_from_opengl_version(version_text):
                        version_pair = _extract_gl_version_pair(version_text)
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
                        return f"{inferred} (inferred from OpenGL {version_pair[0]}.{version_pair[1]})"

                    ogl_info = {
                        "vendor": "unknown",
                        "renderer": "unknown",
                        "version": "unknown",
                        "glsl": "unknown",
                        "glsl_source": "unknown",
                        "direct_rendering": "unknown",
                        "direct_rendering_source": "unknown",
                        "glx_server_vendor": "unknown",
                        "glx_client_vendor": "unknown",
                    }

                    ogl_window = vtk.vtkOpenGLRenderWindow.SafeDownCast(self.renderer_window)
                    if ogl_window is not None:
                        try:
                            ogl_info["vendor"] = str(ogl_window.GetOpenGLVendor() or "unknown")
                        except Exception:
                            pass
                        try:
                            ogl_info["renderer"] = str(ogl_window.GetOpenGLRenderer() or "unknown")
                        except Exception:
                            pass
                        try:
                            ogl_info["version"] = str(ogl_window.GetOpenGLVersion() or "unknown")
                        except Exception:
                            pass

                    capabilities = ""
                    if hasattr(self.renderer_window, "ReportCapabilities"):
                        try:
                            capabilities = str(self.renderer_window.ReportCapabilities() or "")
                        except Exception:
                            capabilities = ""

                    if capabilities:
                        for raw_line in capabilities.splitlines():
                            line = raw_line.strip()
                            lower = line.lower()

                            if lower.startswith("opengl vendor string:"):
                                ogl_info["vendor"] = line.split(":", 1)[1].strip() or ogl_info["vendor"]
                            elif lower.startswith("opengl renderer string:"):
                                ogl_info["renderer"] = line.split(":", 1)[1].strip() or ogl_info["renderer"]
                            elif lower.startswith("opengl version string:"):
                                ogl_info["version"] = line.split(":", 1)[1].strip() or ogl_info["version"]
                            elif lower.startswith("opengl shading language version string:"):
                                parsed_glsl = line.split(":", 1)[1].strip()
                                if parsed_glsl:
                                    ogl_info["glsl"] = parsed_glsl
                                    ogl_info["glsl_source"] = "reported"
                            elif lower.startswith("direct rendering:"):
                                parsed_direct = line.split(":", 1)[1].strip()
                                if parsed_direct:
                                    ogl_info["direct_rendering"] = parsed_direct
                                    ogl_info["direct_rendering_source"] = "reported"
                            elif lower.startswith("server glx vendor string:"):
                                ogl_info["glx_server_vendor"] = line.split(":", 1)[1].strip() or ogl_info["glx_server_vendor"]
                            elif lower.startswith("client glx vendor string:"):
                                ogl_info["glx_client_vendor"] = line.split(":", 1)[1].strip() or ogl_info["glx_client_vendor"]

                    if ogl_info["glsl"].lower() == "unknown":
                        ogl_info["glsl"] = _infer_glsl_from_opengl_version(ogl_info["version"])
                        if ogl_info["glsl"].lower() == "unknown":
                            ogl_info["glsl_source"] = "unknown"
                        else:
                            ogl_info["glsl_source"] = "inferred"

                    lines = [
                        "VTK graphics diagnostics:",
                        f"  - qt_api: {os.getenv('QT_API', 'unknown')}",
                        f"  - qsg_rhi_backend: {os.getenv('QSG_RHI_BACKEND', 'default')}",
                        f"  - vtk_version: {vtkVersion().GetVTKVersion()}",
                        f"  - opengl_vendor: {ogl_info['vendor']}",
                        f"  - opengl_renderer: {ogl_info['renderer']}",
                        f"  - opengl_version: {ogl_info['version']}",
                        f"  - glsl_version: {ogl_info['glsl']}",
                    ]
                    if ogl_info["direct_rendering"].lower() != "unknown":
                        lines.append(f"  - direct_rendering: {ogl_info['direct_rendering']}")
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
                except Exception as exc:
                    LOG.warning("Failed to gather VTK graphics diagnostics: %s", exc)

            self.interactor.Start()

            # Add the observers to watch for particular events. These invoke Python functions.
            self._datasource.programLoaded.connect(self.load_program)
            
            self._datasource.positionChanged.connect(self.update_position)
            self._datasource.motionTypeChanged.connect(self.motion_type)
            
            # self._datasource.rotationXYChanged.connect(self.update_rotation_xy)
            self._datasource.g5xIndexChanged.connect(self.update_g5x_index)
            self._datasource.g5xOffsetChanged.connect(self.update_g5x_offset)
            self._datasource.g92OffsetChanged.connect(self.update_g92_offset)
            
            self._datasource.offsetTableChanged.connect(self.on_offset_table_changed)
            self._datasource.activeOffsetChanged.connect(self.update_active_wcs)
            
            self._datasource.toolTableChanged.connect(self.update_tool)
            self._datasource.toolOffsetChanged.connect(self.update_tool)
            self._datasource.toolInSpindleChanged.connect(self.update_tool)
            # self.status.g5x_index.notify(self.update_g5x_index)
            
            self.offsetTableColumnsIndex = self._datasource.getOffsetColumns()
            
            self.canon = VTKCanon(colors=self.path_colors)

            self.path_actors = self.canon.get_path_actors()

            for wcs_index, path_actor in list(self.path_actors.items()):
                current_offsets = self._safe_get_offsets(wcs_index, self.offsetTableColumnsIndex)
                r_column = self.offsetTableColumnsIndex.get('R') if self.offsetTableColumnsIndex else None
                rotation = current_offsets[r_column] if r_column is not None and r_column < len(current_offsets) else 0.0

                actor_transform = vtk.vtkTransform()
                actor_transform.Translate(*current_offsets[:3])
                actor_transform.RotateZ(rotation)

                path_actor.SetUserTransform(actor_transform)
                # Keep actor position at origin; WCS offset is already applied by UserTransform.
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
            try:
                tool_in_spindle = int(getattr(self._datasource._status.stat, 'tool_in_spindle', 0))
            except Exception:
                tool_in_spindle = 0

            # If no tool is loaded, show cone placeholder and hide tool-bit geometry.
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
                print("NAV 2")
                # Enable the widget.
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
        LOG.debug("VTK - keypress for w or s")
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
        perf_start = time.perf_counter()
        pre_backplot_interp_ms = PROGRAM_LOAD_PERF_SUMMARY.elapsed_since_start_ms(fname)
        parse_done_elapsed_ms = None
        draw_done_elapsed_ms = None
        actor_done_elapsed_ms = None
        backplot_done_elapsed_ms = None
        parse_ms = 0.0
        draw_ms = 0.0
        actor_build_ms = 0.0
        cpp_backplot_used = False
        try:
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

            if not fname:
                return

            # Keep VTKCanon instance for downstream state consumers and perf accounting.
            self.canon = VTKCanon(colors=self.path_colors, cpp_mode=self._use_cpp_backplot)

            unitcode = "G%d" % (20 + (self.stat.linear_units == 1))
            initcode = self.ini.find("RS274NGC", "RS274NGC_STARTUP_CODE") or ""

            if self._use_cpp_backplot:
                draw_start = time.perf_counter()
                cpp_result = build_backplot_from_file(
                    fname,
                    self._datasource,
                    path_colors=self.path_colors,
                    unitcode=unitcode,
                    initcode=initcode,
                    parameter_file=self.parameter_file,
                    temp_parameter_file=self.temp_parameter_file,
                )
                if cpp_result is None:
                    raise RuntimeError("C++ backplot builder returned no result in cpp-only mode")

                parse_ms = float(cpp_result.parse_ms)

                self.path_actors = cpp_result.path_actors
                self.offset_transitions = cpp_result.offset_transitions or list()
                self.canon.added_segments = int(cpp_result.added_segments)
                draw_ms = float(cpp_result.draw_ms)
                if draw_ms <= 0.0:
                    draw_ms = (time.perf_counter() - draw_start) * 1000.0
                draw_done_elapsed_ms = PROGRAM_LOAD_PERF_SUMMARY.elapsed_since_start_ms(fname)
                # Parse and draw both complete inside the same native call. We only get one
                # wall-clock checkpoint on return, so estimate parse completion by subtracting
                # measured native draw time from the draw completion checkpoint.
                if draw_done_elapsed_ms is not None:
                    parse_done_elapsed_ms = max(0.0, float(draw_done_elapsed_ms) - float(draw_ms))
                cpp_backplot_used = True
            else:
                parse_start = time.perf_counter()
                try:
                    if os.path.exists(self.parameter_file):
                        shutil.copy(self.parameter_file, self.temp_parameter_file)
                    self.canon.parameter_file = self.temp_parameter_file
                    result, seq = gcode.parse(fname, self.canon, unitcode, initcode)
                    if result > gcode.MIN_ERROR:
                        msg = gcode.strerror(result)
                        LOG.warning("Python backplot parse error in %s line %s: %s", fname, seq - 1, msg)
                        return
                finally:
                    try:
                        os.unlink(self.temp_parameter_file)
                    except Exception:
                        pass
                    try:
                        os.unlink(self.temp_parameter_file + '.bak')
                    except Exception:
                        pass

                parse_ms = (time.perf_counter() - parse_start) * 1000.0
                parse_done_elapsed_ms = PROGRAM_LOAD_PERF_SUMMARY.elapsed_since_start_ms(fname)

                draw_start = time.perf_counter()
                self.canon.draw_lines()
                draw_ms = (time.perf_counter() - draw_start) * 1000.0
                draw_done_elapsed_ms = PROGRAM_LOAD_PERF_SUMMARY.elapsed_since_start_ms(fname)

                self.path_actors = self.canon.get_path_actors()
                self.offset_transitions = self.canon.get_offset_transitions() or list()

            # Refresh WCS offsets and active index in case they changed since init.
            # This makes sure newly loaded paths honor the current work offset.
            self._set_wcs_offsets(self._datasource.getWcsOffsets())
            self.active_wcs_index = self._datasource.getActiveWcsIndex()

            if not self._offsets_ready():
                LOG.warning(
                    "VTKBackPlot load_program: offset table not ready; skipping draw to avoid G53 placement"
                )
                return

            active_offsets = self._safe_get_offsets(self.active_wcs_index, self._datasource.getOffsetColumns())
            try:
                offsets_len = len(self.wcs_offsets)
            except Exception:
                offsets_len = 'n/a'

            LOG.debug(
                "VTKBackPlot load_program context: active_wcs=%s offsets_len=%s active_offsets=%s",
                self.active_wcs_index,
                offsets_len,
                active_offsets,
            )

            if self._is_machine_foam:

                self.foam_offset = self.canon.get_foam()
                LOG.warning(self.foam_offset)
                z = self.foam_offset[0]
                w = self.foam_offset[1]

                self.tool_bit_actor.set_foam_offsets(z, w)

            offset_columns = self._datasource.getOffsetColumns()

            actor_start = time.perf_counter()
            for wcs_index, actor in self.path_actors.items():
                current_offsets = self._safe_get_offsets(wcs_index, offset_columns)
                x, y, z, rotation = self._resolve_wcs_components(
                    wcs_index,
                    current_offsets,
                    offset_columns,
                )

                if 0 <= wcs_index < len(self.rotation_xy_table):
                    self.rotation_xy_table[wcs_index] = rotation

                actor_transform = self._compose_wcs_transform(x, y, z, rotation)
                axes_transform = self._compose_wcs_transform(x, y, z, rotation)

                if wcs_index == self.active_wcs_index:
                    self._active_path_transform = actor_transform

                # Scale up the axes for the active WCS to provide visual feedback
                if wcs_index == self.active_wcs_index:
                    axes_transform.Scale(1.5, 1.5, 1.5)  # Make active WCS axes 50% larger


                actor.SetUserTransform(actor_transform)

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
            actor_build_ms = (time.perf_counter() - actor_start) * 1000.0
            actor_done_elapsed_ms = PROGRAM_LOAD_PERF_SUMMARY.elapsed_since_start_ms(fname)

            total_ms = (time.perf_counter() - perf_start) * 1000.0
            backplot_done_elapsed_ms = PROGRAM_LOAD_PERF_SUMMARY.elapsed_since_start_ms(fname)
            LOG.debug(
                "[backplot-perf] file=%s parse_ms=%.2f draw_ms=%.2f actor_build_ms=%.2f total_ms=%.2f cpp_requested=%s cpp_used=%s",
                fname,
                parse_ms,
                draw_ms,
                actor_build_ms,
                total_ms,
                True,
                cpp_backplot_used,
            )
            PROGRAM_LOAD_PERF_SUMMARY.update_backplot(
                fname,
                added_segments=getattr(self.canon, 'added_segments', 0),
                interp_ms=parse_ms,
                draw_ms=draw_ms,
                actor_build_ms=actor_build_ms,
                cpp_mode=cpp_backplot_used,
                pre_backplot_interp_ms=pre_backplot_interp_ms,
                parse_done_elapsed_ms=parse_done_elapsed_ms,
                draw_done_elapsed_ms=draw_done_elapsed_ms,
                actor_done_elapsed_ms=actor_done_elapsed_ms,
                backplot_done_elapsed_ms=backplot_done_elapsed_ms,
            )
        except Exception:
            LOG.exception("VTKBackPlot load_program failed")
        finally:
            if self.program_view_when_loading_program:
                self.setViewProgram(self.program_view_when_loading_program_view)

            QTimer.singleShot(300, self._datasource._status.removeLock)

    def motion_type(self, value):
        self.current_motion_type = value
        if value == linuxcnc.MOTION_TYPE_TOOLCHANGE:
            self.update_tool()

    def _should_plot_breadcrumb_for_motion(self):
        try:
            mt = self.current_motion_type
            if mt is None:
                mt = self._datasource._status.stat.motion_type

            if mt == linuxcnc.MOTION_TYPE_TOOLCHANGE:
                return False

            # Avoid startup rapid breadcrumbs before cutting begins.
            if not self._breadcrumbs_armed:
                if mt == linuxcnc.MOTION_TYPE_TRAVERSE:
                    return False
                self._breadcrumbs_armed = True
        except Exception:
            # Fallback to plotting if motion type is unavailable.
            return True

        return True

    def _resolve_kinematics_type(self, value):
        normalized = str(value or "").strip().lower()
        return KINEMATICS_ALIASES.get(normalized, KINEMATICS_GANTRY_XYZ)

    def _extract_rotary_axis_origins(self, machine_parts_data):
        origins = {}

        def walk(node):
            if not isinstance(node, dict):
                return

            axis = node.get('axis')
            part_type = str(node.get('type', '')).lower()
            origin = node.get('origin')

            if isinstance(axis, str) and part_type == 'angular' and isinstance(origin, (list, tuple)) and len(origin) >= 3:
                try:
                    origins[axis.upper()] = (float(origin[0]), float(origin[1]), float(origin[2]))
                except Exception:
                    pass

            for value in node.values():
                if isinstance(value, dict):
                    walk(value)

        walk(machine_parts_data)
        return origins

    def _log_overlay_rotation_sources(self):
        axis_specs = [('A', 0), ('B', 1), ('C', 2)]
        active = []
        missing = []

        for axis_name, idx in axis_specs:
            if self.axis_motion_owner.get(axis_name, 'tool') != 'table':
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

        table_axes = [axis for axis, _ in axis_specs if self.axis_motion_owner.get(axis, 'tool') == 'table']
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

        shift_x = self.kinematics_overlay_shift[0] if self.axis_motion_owner.get('X', 'tool') == 'table' else 0.0
        shift_y = self.kinematics_overlay_shift[1] if self.axis_motion_owner.get('Y', 'tool') == 'table' else 0.0
        shift_z = self.kinematics_overlay_shift[2] if self.axis_motion_owner.get('Z', 'tool') == 'table' else 0.0

        return (
            float(origin[0] + shift_x),
            float(origin[1] + shift_y),
            float(origin[2] + shift_z),
        )

    def _overlay_rotary_axis_order(self):
        # Apply rotary transforms parent-to-child so downstream axes inherit
        # upstream tilt (e.g. C riding on A in xyzac machine assemblies).
        table_a = self.axis_motion_owner.get('A', 'tool') == 'table'
        table_c = self.axis_motion_owner.get('C', 'tool') == 'table'
        if table_a and table_c:
            return ('A', 'B', 'C')
        return ('A', 'B', 'C')

    def _transform_debug_enabled(self):
        return self._transform_debug and LOG.isEnabledFor(logging.DEBUG)

    def _compose_wcs_transform(self, x, y, z, rotation=0.0):
        # LinuxCNC-style chain for table machines:
        # 1) place WCS, 2) apply table linear shift, 3) apply table rotary axes
        # about configured pivots.
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

        # Match machine-part transform style: place base first, then rotate
        # about local pivots relative to that base placement.
        transform.Translate(base_x, base_y, base_z)

        self._log_overlay_rotation_sources()
        for axis_name in self._overlay_rotary_axis_order():
            angle = float(angles_by_axis.get(axis_name, 0.0))
            if abs(angle) <= 1e-12:
                continue

            origin = self._overlay_rotary_pivot_absolute(axis_name)
            if origin is None:
                # Missing pivot: rotate around local origin as a safe fallback.
                self._apply_axis_rotation_about_pivot(transform, axis_name, angle, (0.0, 0.0, 0.0))
                continue

            pivot_local = (
                float(origin[0] - base_x),
                float(origin[1] - base_y),
                float(origin[2] - base_z),
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
                    origin,
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

        transform.RotateZ(rotation)
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

        if self.axis_motion_owner.get('X', 'tool') == 'table':
            x = 0.0

        if self.axis_motion_owner.get('Y', 'tool') == 'table':
            y = 0.0

        if self.axis_motion_owner.get('Z', 'tool') == 'table':
            z = 0.0

        return (x, y, z)

    def _current_switchkins_type(self):
        try:
            value = self._datasource.getSwitchkinsType()
            if value is None:
                return int(self._runtime_switchkins_type)
            return int(value)
        except Exception:
            return int(self._runtime_switchkins_type)

    def _is_tcp_switchkins_active(self, switchkins_type=None):
        if switchkins_type is None:
            switchkins_type = self._current_switchkins_type()
        return int(switchkins_type) == 1

    def _has_table_owned_axes(self):
        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
            if self.axis_motion_owner.get(axis, 'tool') == 'table':
                return True
        return False

    def _compute_kinematics_overlay_shift(self, machine_position, switchkins_type=None):
        # In TCP switchkins mode, status position is already in the controlled
        # tool-point/world frame, so applying table overlay shift again causes
        # backplot/cache actor drift.
        if self._is_tcp_switchkins_active(switchkins_type) and (not self._has_table_owned_axes()):
            return (0.0, 0.0, 0.0)

        if all(self.axis_motion_owner.get(axis, 'tool') == 'tool' for axis in ['X', 'Y', 'Z']):
            return (0.0, 0.0, 0.0)

        sx = float(self.spindle_position[0] - machine_position[0])
        sy = float(self.spindle_position[1] - machine_position[1])
        sz = float(self.spindle_position[2] - machine_position[2])

        # Table-owned axes should not drift when only WCS origin changes.
        if self.axis_motion_owner.get('X', 'tool') == 'table':
            sx = float(-machine_position[0])
        if self.axis_motion_owner.get('Y', 'tool') == 'table':
            sy = float(-machine_position[1])
        if self.axis_motion_owner.get('Z', 'tool') == 'table':
            sz = float(-machine_position[2])

        return (
            sx,
            sy,
            sz,
        )

    def _compute_kinematics_overlay_rotation(self, machine_rotation, switchkins_type=None):
        # In TCP switchkins mode, tool-point coordinates are already solved in
        # world space, so applying table overlay rotation here doubles rotary
        # motion in loaded/active path transforms.
        if self._is_tcp_switchkins_active(switchkins_type) and (not self._has_table_owned_axes()):
            return (0.0, 0.0, 0.0)

        if all(self.axis_motion_owner.get(axis, 'tool') == 'tool' for axis in ['A', 'B', 'C']):
            return (0.0, 0.0, 0.0)

        rx = 0.0
        ry = 0.0
        rz = 0.0

        if self.axis_motion_owner.get('A', 'tool') == 'table':
            rx = -float(machine_rotation[0])
        if self.axis_motion_owner.get('B', 'tool') == 'table':
            ry = -float(machine_rotation[1])
        if self.axis_motion_owner.get('C', 'tool') == 'table':
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
        # Keep breadcrumbs in the same moving frame as the active path actor.
        self.path_cache_actor.SetUserTransform(self._active_path_transform)

    def _world_tooltip_point(self, tooltip_local):
        try:
            x, y, z = tooltip_local[:3]
            return self._active_path_transform.TransformPoint(float(x), float(y), float(z))
        except Exception:
            return tuple(tooltip_local[:3])

    def _active_path_local_point(self, world_point):
        try:
            inverse = vtk.vtkTransform()
            inverse.DeepCopy(self._active_path_transform)
            inverse.Inverse()
            x, y, z = world_point[:3]
            return inverse.TransformPoint(float(x), float(y), float(z))
        except Exception:
            return tuple(world_point[:3])

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
        # Build tooltip sample in the same local frame as path actor points.
        # For table-owned linear axes, spindle_position is intentionally pinned,
        # so use machine_position to preserve XY breadcrumb motion.
        src_x = float(machine_position[0]) if self.axis_motion_owner.get('X', 'tool') == 'table' else float(self.spindle_position[0])
        src_y = float(machine_position[1]) if self.axis_motion_owner.get('Y', 'tool') == 'table' else float(self.spindle_position[1])
        src_z = float(machine_position[2]) if self.axis_motion_owner.get('Z', 'tool') == 'table' else float(self.spindle_position[2])

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
        owner = self.axis_motion_owner.get(axis_name.upper(), 'tool')
        if owner == 'table':
            return -float(axis_value)
        return float(axis_value)

    def _axis_joint_feedback(self, axis_name):
        # Fallback mapping for common XYZABC<->joint index layouts.
        # When table-owned linear axes are present, joint feedback reflects
        # real table motion more reliably than Cartesian status.position.
        axis_order = "XYZABCUVW"
        idx = axis_order.find(str(axis_name or '').upper())
        if idx < 0:
            return None

        try:
            joint_channel = self.joints[idx]
            return float(joint_channel.input.value)
        except Exception:
            return None

    def _table_aware_linear_position(self, position):
        x = float(position[0])
        y = float(position[1])
        z = float(position[2])

        # In TCP switchkins mode, status position is already in the controlled
        # world/tool-point frame. Rebuilding XYZ from raw joints introduces a
        # small but visible offset against the loaded path.
        if self._is_tcp_switchkins_active():
            return (x, y, z)

        table_linear_active = any(
            self.axis_motion_owner.get(axis, 'tool') == 'table'
            for axis in ['X', 'Y', 'Z']
        )

        # Keep XYZ from one timing domain when table kinematics is active.
        # Mixing joint-backed X/Y with status-backed Z can introduce slight
        # breadcrumb offsets on vertical-plane arcs (G18/G19).
        if table_linear_active:
            xj = self._axis_joint_feedback('X')
            yj = self._axis_joint_feedback('Y')
            zj = self._axis_joint_feedback('Z')
            if xj is not None and yj is not None and zj is not None:
                return (xj, yj, zj)

        if self.axis_motion_owner.get('X', 'tool') == 'table':
            xj = self._axis_joint_feedback('X')
            if xj is not None:
                x = xj
        if self.axis_motion_owner.get('Y', 'tool') == 'table':
            yj = self._axis_joint_feedback('Y')
            if yj is not None:
                y = yj
        if self.axis_motion_owner.get('Z', 'tool') == 'table':
            zj = self._axis_joint_feedback('Z')
            if zj is not None:
                z = zj

        return (x, y, z)

    def _machine_angular_axis_value(self, axis_name, axis_value):
        owner = self.axis_motion_owner.get(axis_name.upper(), 'tool')
        if owner == 'table':
            return -float(axis_value)
        return float(axis_value)

    def _visual_tool_rotation(self, machine_rotation):
        rx = 0.0 if self.axis_motion_owner.get('A', 'tool') == 'table' else float(machine_rotation[0])
        ry = 0.0 if self.axis_motion_owner.get('B', 'tool') == 'table' else float(machine_rotation[1])
        rz = 0.0 if self.axis_motion_owner.get('C', 'tool') == 'table' else float(machine_rotation[2])
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
        
        
        # Plots the movement of the tool and leaves a trace line
        
        active_wcs_offset = self._safe_get_offsets(self.active_wcs_index, self.offsetTableColumnsIndex)
        if self._is_machine_jet:
            # update the position for JET machines so spindle/tool is
            # aligned to active WCS
            list_pos = list(position)
            list_pos[2] = active_wcs_offset[2]
            position = tuple(list_pos)
            
        machine_position = self._table_aware_linear_position(position)
        self.machine_motion_position = machine_position
        self.spindle_position = self._visual_spindle_position(machine_position, active_wcs_offset)
        self.spindle_rotation = position[3:6]
        current_switchkins_type = self._current_switchkins_type()
        self._runtime_switchkins_type = int(current_switchkins_type)

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
        #tool_transform.RotateX(-self.spindle_rotation[0])
        #tool_transform.RotateY(-self.spindle_rotation[1])
        #tool_transform.RotateZ(-self.spindle_rotation[2])
        

        if self.spindle_model:
            self.spindle_actor.SetUserTransform(tool_transform)

        if self._plot_machine:
            if self.machine_parts:


                # self.machine_parts_actor.InitPathTraversal()
                # parts = self.machine_parts_actor.GetParts()
                
                self.machine_parts_actor.InitPathTraversal()
                for part in self.get_asm_parts(self.machine_parts_actor):
                    # part_prop = path.GetViewProp()
                    # if isinstance(part, vtk.vtkActor):
                    #    self.move_part(part)
                    if isinstance(part, vtk.vtkAssembly):
                        self.move_part(part)
                    #

                        # for p in part.GetParts():
                        #     if isinstance(p, vtk.vtkActor):
                        #         self.move_part(p)
                        #     # if isinstance(p, vtk.vtkAssembly):
                            #     self.move_part(p)

        self.tool_actor.SetUserTransform(tool_transform)

        if self._is_machine_foam:
            self.tool_bit_actor.set_position(position)
        else:
            visual_position = list(position)
            visual_position[0] = self.spindle_position[0]
            visual_position[1] = self.spindle_position[1]
            visual_position[2] = self.spindle_position[2]

            # Keep tool orientation aligned to spindle axes; table-owned rotary
            # axes (e.g. A/C on trunnion/table machines) should not tilt tool.
            tool_rotation = self._visual_tool_rotation(self.spindle_rotation)
            if len(visual_position) > 3:
                visual_position[3] = tool_rotation[0]
            if len(visual_position) > 4:
                visual_position[4] = tool_rotation[1]
            if len(visual_position) > 5:
                visual_position[5] = tool_rotation[2]

            self.tool_bit_actor.set_position_cnc(tuple(visual_position))

        tlo = self._datasource.getToolOffset()
        tool_tip_world = self._current_tool_tip_world(tlo[:3], machine_position, current_switchkins_type)
        self.tooltip_position = self._active_path_local_point(tool_tip_world)
            

        # self.spindle_actor.SetPosition(self.spindle_position)
        # self.tool_actor.SetPosition(self.spindle_position)

        if self.breadcrumbs_plotted and self._should_plot_breadcrumb_for_motion():
            if not self._path_cache_seeded:
                self.renderer.RemoveActor(self.path_cache_actor)
                self.path_cache_actor = PathCacheActor(tuple(self.tooltip_position[:3]))
                self.path_cache_actor.SetUserTransform(self._active_path_transform)
                self.renderer.AddActor(self.path_cache_actor)
                self._path_cache_seeded = True
            else:
                self.path_cache_actor.add_line_point(tuple(self.tooltip_position[:3]))
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
        
    def on_offset_table_changed(self, offset_table):
        if offset_table is None:
            LOG.warning("VTKBackPlot: received None offset table; keeping existing offsets")
            return

        # Accept whatever came in (including empty), matching PyQt5 flow.
        self._set_wcs_offsets(offset_table)

        self.rotate_and_translate()

    def _offsets_ready(self):
        """Return True when we have any WCS offsets; mirrors old guard to avoid G53 placement."""

        if self.wcs_offsets:
            return True

        LOG.warning("VTKBackPlot: offsets not ready; skipping draw to avoid G53 placement")
        return False

    def _set_wcs_offsets(self, offsets):
        """Normalize incoming WCS offsets so lookups work regardless of key type."""

        if isinstance(offsets, dict):
            try:
                self.wcs_offsets = {int(k): v for k, v in offsets.items()}
            except Exception:
                self.wcs_offsets = dict(offsets)
        else:
            self.wcs_offsets = offsets

    def _safe_get_offsets(self, wcs_index, offset_columns=None):
        """Return offsets for a WCS index, defaulting to zeros when missing."""

        offsets = None

        if isinstance(self.wcs_offsets, dict):
            offsets = self.wcs_offsets.get(wcs_index)
        elif isinstance(self.wcs_offsets, (list, tuple)):
            if 0 <= wcs_index < len(self.wcs_offsets):
                offsets = self.wcs_offsets[wcs_index]

        if offsets is None:
            column_count = 9
            if offset_columns:
                try:
                    column_count = max(offset_columns.values()) + 1
                except ValueError:
                    pass

            offsets = [0.0] * column_count
            LOG.warning("Missing WCS offsets for index %s, defaulting to zeros", wcs_index)

        return offsets

    def _resolve_wcs_components(self, wcs_index, current_offsets, offset_columns):
        x_column = offset_columns.get('X') if offset_columns else None
        y_column = offset_columns.get('Y') if offset_columns else None
        z_column = offset_columns.get('Z') if offset_columns else None
        r_column = offset_columns.get('R') if offset_columns else None

        x = current_offsets[x_column] if x_column is not None and x_column < len(current_offsets) else 0.0
        y = current_offsets[y_column] if y_column is not None and y_column < len(current_offsets) else 0.0
        z = current_offsets[z_column] if z_column is not None and z_column < len(current_offsets) else 0.0
        rotation = current_offsets[r_column] if r_column is not None and r_column < len(current_offsets) else 0.0

        # For active WCS, use live status values to avoid stale offset-table snapshots.
        if wcs_index == self.active_wcs_index and isinstance(self.active_wcs_offset, (list, tuple)):
            live = self.active_wcs_offset
            if x_column is not None and x_column < len(live):
                x = live[x_column]
            if y_column is not None and y_column < len(live):
                y = live[y_column]
            if z_column is not None and z_column < len(live):
                z = live[z_column]
            rotation = float(self.active_rotation or 0.0)

        return x, y, z, rotation

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
            x, y, z, rotation = self._resolve_wcs_components(
                wcs_index,
                current_offsets,
                self.offsetTableColumnsIndex,
            )

            actor_transform = self._compose_wcs_transform(x, y, z, rotation)
            axes_transform = self._compose_wcs_transform(x, y, z, rotation)

            if wcs_index == self.active_wcs_index:
                self._active_path_transform = actor_transform

            if self._transform_debug_enabled():
                actor_origin = actor_transform.TransformPoint(0.0, 0.0, 0.0)
                LOG.debug(
                    "VTK rotate_and_translate: wcs=%s resolved_xyzr=(%.6f, %.6f, %.6f, %.6f) "
                    "actor_origin=(%.6f, %.6f, %.6f)",
                    wcs_index,
                    float(x),
                    float(y),
                    float(z),
                    float(rotation),
                    float(actor_origin[0]),
                    float(actor_origin[1]),
                    float(actor_origin[2]),
                )
            
            # Scale up the axes for the active WCS to provide visual feedback
            if wcs_index == self.active_wcs_index:
                axes_transform.Scale(1.5, 1.5, 1.5)  # Make active WCS axes 50% larger

            axes_actor.SetUserTransform(axes_transform)
            #LOG.debug(f"-------- Path Actor Matrix BEFORE User transform:  {path_actor.GetMatrix()}")
            #LOG.debug(f"-------- Path Actor User transform BEFORE apply new:  {path_actor.GetUserTransform()}")
            path_actor.SetUserTransform(actor_transform)
            #LOG.debug(f"-------- Path Actor Matrix AFTER User transform:  {path_actor.GetMatrix()}")
            #LOG.debug(f"-------- Path Actor User transform AFTER apply new:  {path_actor.GetUserTransform()}")

            self._sync_program_bounds_actor(wcs_index, path_actor)
        
            xyz = self.active_wcs_offset[:3]
            rotation = self.active_rotation
            _ = xyz, rotation
                           

        if len(self.path_actors) > 1:
            self._update_transition_actors(self.offsetTableColumnsIndex)

        # Keep breadcrumbs aligned to the same transform as the active path.
        if self.path_cache_actor is not None:
            self.path_cache_actor.SetUserTransform(self._active_path_transform)

        self._request_render()
        
    def update_g5x_index(self, index):
        self.active_wcs_index = index
        if len(self.path_actors) > 0:
            self.rotate_and_translate()
        # Refresh offsets in case the table changed with the new active WCS.
        self._set_wcs_offsets(self._datasource.getWcsOffsets())
    
    def update_active_wcs(self, wcs_index):
        self.active_wcs_index = wcs_index
        # Keep offsets fresh when the active WCS changes.
        self._set_wcs_offsets(self._datasource.getWcsOffsets())
        
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
                x, y, z, rotation = self._resolve_wcs_components(
                    wcs_index,
                    current_offsets,
                    self.offsetTableColumnsIndex,
                )

                if len(path_offset) > 0:
                    x += float(path_offset[0])
                if len(path_offset) > 1:
                    y += float(path_offset[1])
                if len(path_offset) > 2:
                    z += float(path_offset[2])

                axes = actor.get_axes_actor()

                path_transform = self._compose_wcs_transform(
                    x,
                    y,
                    z,
                    rotation,
                )

                if wcs_index == self.active_wcs_index:
                    self._active_path_transform = path_transform

                # self.axes_actor.SetUserTransform(path_transform)
                axes.SetUserTransform(path_transform)
                actor.SetUserTransform(path_transform)

                self._sync_program_bounds_actor(wcs_index, actor)

            if self.path_cache_actor is not None:
                self.path_cache_actor.SetUserTransform(self._active_path_transform)

            self._request_render()

    def update_tool(self, *_args):
        self.renderer.RemoveActor(self.tool_actor)
        self.renderer.RemoveActor(self.tool_bit_actor)

        self.tool_actor = ToolActor(self._datasource)
        self.tool_bit_actor = ToolBitActor(self._datasource)

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)
        tool_rotation = self._visual_tool_rotation(self.spindle_rotation)
        tool_transform.RotateX(-tool_rotation[0])
        tool_transform.RotateY(-tool_rotation[1])
        tool_transform.RotateZ(-tool_rotation[2])

        self.tool_actor.SetUserTransform(tool_transform)

        if self._is_machine_foam:
            self.renderer.RemoveActor(self.tool_bit_actor)
            self.tool_bit_actor = ToolBitActor(self._datasource)
            self.tool_bit_actor.SetUserTransform(tool_transform)
        else:
            self.tool_bit_actor.SetUserTransform(tool_transform)

        try:
            tool_in_spindle = int(getattr(self._datasource._status.stat, 'tool_in_spindle', 0))
        except Exception:
            tool_in_spindle = 0

        if tool_in_spindle <= 0:
            self.tool_actor.SetVisibility(1)
            self.tool_bit_actor.SetVisibility(0)
        else:
            self.tool_actor.SetVisibility(1)
            self.tool_bit_actor.SetVisibility(1)

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.tool_bit_actor)

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
        
        if not (0 <= self.active_wcs_index < len(self.wcs_offsets)):
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
        current_offsets = self.wcs_offsets.get(wcs_index, [])
        x, y, z, rotation = self._resolve_wcs_components(wcs_index, current_offsets, offset_columns)

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
        offsets = self.wcs_offsets.get(wcs_index)
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
        if not (0 <= self.active_wcs_index < len(self.wcs_offsets)):
            self.active_wcs_index = 0

        position = self._safe_get_offsets(self.active_wcs_index, self.offsetTableColumnsIndex)
        ot_columns_index = self.offsetTableColumnsIndex

        column_x = ot_columns_index.get('X')
        column_y = ot_columns_index.get('Y')
        column_z = ot_columns_index.get('Z')

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
        self.path_cache_actor.SetUserTransform(self._active_path_transform)
        self.renderer.AddActor(self.path_cache_actor)
        self._breadcrumbs_armed = False
        self._path_cache_seeded = False
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
    def showSurface(self, surface):
        LOG.debug('show surface')
        self.points_surface_actor.showSurface(surface)
        self.renderer_window.Render()

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

    # @backgroundColor.reset
    # def backgroundColor(self):
    #     self._background_color = QColor(0, 0, 0)
    #
    #     self.renderer.GradientBackgroundOff()
    #     self._request_render()


    @Property(QColor)
    def backgroundColor2(self):
        return self._background_color2

    @backgroundColor2.setter
    def backgroundColor2(self, color2):
        self._background_color2 = color2

        self.renderer.GradientBackgroundOn()
        self.renderer.SetBackground2(color2.getRgbF()[:3])
        self._request_render()

    # @backgroundColor2.reset
    # def backgroundColor2(self):
    #     self._background_color2 = QColor(0, 0, 0)
    #
    #     self.renderer.GradientBackgroundOff()
    #     self._request_render()

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

    # PySide6.QtCore.Property has no reset attribute
    # @traverseColor.reset
    # def traverseColor(self):
    #     self._traverse_color = self._default_traverse_color

    # Arcfeed color property

    @Property(QColor)
    def arcfeedColor(self):
        return self._arcfeed_color

    @arcfeedColor.setter
    def arcfeedColor(self, color):
        self._arcfeed_color = color

    # PySide6.QtCore.Property has no reset attribute
    # @arcfeedColor.reset
    # def arcfeedColor(self):
    #     self._arcfeed_color = self._default_arcfeed_color

    # Feed color property

    @Property(QColor)
    def feedColor(self):
        return self._feed_color

    @feedColor.setter
    def feedColor(self, color):
        self._feed_color = color

    # PySide6.QtCore.Property has no reset attribute
    # @feedColor.reset
    # def feedColor(self):
    #     self._feed_color = self._default_feed_color

    # Dwell color property

    @Property(QColor)
    def dwellColor(self):
        return self._dwel_color

    @dwellColor.setter
    def dwellColor(self, color):
        self._dwel_color = color

    # PySide6.QtCore.Property has no reset attribute
    # @dwellColor.reset
    # def dwellColor(self):
    #     self._dwel_color = self._default_dwell_color

    # User color property

    @Property(QColor)
    def userColor(self):
        return self._user_color

    @userColor.setter
    def userColor(self, color):
        self._user_color = color

    # PySide6.QtCore.Property has no reset attribute
    # @userColor.reset
    # def userColor(self):
    #     self._user_color = self._default_user_color

