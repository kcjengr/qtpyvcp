import yaml

import linuxcnc
import os
from collections import OrderedDict
from operator import add
import time

import vtk
import vtk.qt
from vtkmodules.vtkCommonCore import (
    VTK_VERSION_NUMBER,
    vtkVersion
)
from qtpy.QtCore import Qt, Property, Slot, QObject, QEvent, QTimer
from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QColor

# Fix poligons not drawing correctly on some GPU
# https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1

vtk.qt.QVTKRWIBase = "QGLWidget"

# Fix end

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp import actions
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import connectSetting, getSetting


from .base_backplot import BaseBackPlot
from .axes_actor import AxesActor
from .tool_actor import ToolActor, ToolBitActor
from .table_actor import TableActor
from .spindle_actor import SpindleActor
from .machine_actor import MachineCubeActor, MachineLineActor, MachinePartsASM
from .path_cache_actor import PathCacheActor
from .program_bounds_actor import ProgramBoundsActor
from .vtk_canon import VTKCanon, COLOR_MAP
from .linuxcnc_datasource import LinuxCncDataSource

LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER', False)
NUMBER_OF_WCS = 9


# turn on antialiasing
from qtpy.QtOpenGL import QGLFormat
f = QGLFormat()
f.setSampleBuffers(True)
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
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.isAutoRepeat():
                return super().eventFilter(obj, event)

            speed = actions.machine.MAX_JOG_SPEED / 60.0 if event.modifiers() & Qt.ShiftModifier else None
            if event.key() == Qt.Key_Up:
                actions.machine.jog.axis('Y', 1, speed=speed)
            elif event.key() == Qt.Key_Down:
                actions.machine.jog.axis('Y', -1, speed=speed)
            elif event.key() == Qt.Key_Left:
                actions.machine.jog.axis('X', -1, speed=speed)
            elif event.key() == Qt.Key_Right:
                actions.machine.jog.axis('X', 1, speed=speed)
            elif event.key() == Qt.Key_PageUp:
                actions.machine.jog.axis('Z', 1, speed=speed)
            elif event.key() == Qt.Key_PageDown:
                actions.machine.jog.axis('Z', -1, speed=speed)
            #else:
                #print('Unhandled key press event')
        elif event.type() == QEvent.KeyRelease:
            if event.isAutoRepeat():
                return super().eventFilter(obj, event)

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
            #else:
            #print('Unhandled key release event')

        return super().eventFilter(obj, event)

class VTKBackPlot(QVTKRenderWindowInteractor, VCPWidget, BaseBackPlot):
    def __init__(self, parent=None):
        super(VTKBackPlot, self).__init__(parent)


        # LOG.debug("---------using refactored vtk code")

        self._datasource = LinuxCncDataSource()

        # TODO: for some reason, we need to multiply for metric, find out why!
        self.multiplication_factor = 25.4 if self._datasource.isMachineMetric() else 1

        # print(self._datasource.getKeyboardJog())
        
        if self._datasource.getKeyboardJog().lower() in ['true', '1', 't', 'y', 'yes']:
            event_filter = InteractorEventFilter(self)
            self.installEventFilter(event_filter)

        self.current_time = round(time.time() * 1000)
        self.plot_interval = 1000/30  # 1 second / 30 fps
        self.prev_plot_time = 0
        
        self.parent = parent
        self.ploter_enabled = True
        self.touch_enabled = False
        self.program_view_when_loading_program = False
        self.program_view_when_loading_program_view = 'p'
        self.pan_mode = False
        self.line = None
        self._last_filename = str()
        self.rotating = 0
        self.panning = 0
        self.zooming = 0
        
        self.machine_parts = None
        self.machine_parts_data = None
        
        # assume that we are standing upright and compute azimuth around that axis
        self.natural_view_up = (0, 0, 1)

        self._plot_machine = True
        
        self._background_color = QColor(0, 0, 0)
        self._background_color2 = QColor(0, 0, 0)
        self._enableProgramTicks = True
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

        self.active_wcs_index = self._datasource.getActiveWcsIndex()
        self.wcs_offsets = self._datasource.getWcsOffsets()
        self.active_wcs_offset = self._datasource.getActiveWcsOffsets()
        self.g92_offset = self._datasource.getG92_offset()
        self.active_rotation = self._datasource.getRotationOfActiveWcs()
        
        self.rotation_xy_table = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        LOG.debug("---------active_wcs_index {}".format(self.active_wcs_index))
        LOG.debug("---------active_wcs_offset {}".format(self.active_wcs_offset))
        LOG.debug("---------wcs_offsets {}".format(self.wcs_offsets))

        self.original_g5x_offset = [0.0] * NUMBER_OF_WCS
        self.original_g92_offset = [0.0] * NUMBER_OF_WCS

        self.spindle_position = (0.0, 0.0, 0.0)
        self.spindle_rotation = (0.0, 0.0, 0.0)
        self.tooltip_position = (0.0, 0.0, 0.0)
        
        self.joints = self._datasource._status.joint

        self.foam_offset = [0.0, 0.0]

        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()
        
        self.path_actors = OrderedDict()

        self.path_end_point = OrderedDict()
        self.path_angle_point = OrderedDict()
        self.path_start_point = OrderedDict()

        self.path_offset_start_point = OrderedDict()
        self.path_offset_angle_points = OrderedDict()
        self.path_offset_end_point = OrderedDict()

        self.offset_change_start_actor = OrderedDict()
        self.offset_change_end_actor = OrderedDict()
        self.offset_change_line_actor = OrderedDict()

        self.path_offset_start_point = OrderedDict()
        self.path_offset_angle_point = OrderedDict
        self.path_offset_end_point = OrderedDict()
        
        if self._datasource.isMachineMetric():
            self.position_mult = 1000  # 500 here works for me
            self.clipping_range_near = 0.01
            self.clipping_range_far = 10000.0  # TODO: check this value
        else:
            self.position_mult = 100
            self.clipping_range_near = 0.001
            self.clipping_range_far = 1000.0  # TODO: check this value

        self.camera.SetClippingRange(self.clipping_range_near, self.clipping_range_far)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetActiveCamera(self.camera)

        self.renderer_window = self.GetRenderWindow()
        self.renderer_window.AddRenderer(self.renderer)

        # self.nav_style = vtk.vtkInteractorStyleTrackballCamera()
        self.nav_style = vtk.vtkInteractorStyleMultiTouchCamera() if self.touch_enabled else None

        self.interactor = self.renderer_window.GetInteractor()
        self.interactor.SetInteractorStyle(self.nav_style)
        self.interactor.SetRenderWindow(self.renderer_window)

        if not IN_DESIGNER:
            
            bounds_type = self._datasource.getMachineBounds()
            if bounds_type == "line":
                self.machine_actor = MachineLineActor(self._datasource)
            else:
                self.machine_actor = MachineCubeActor(self._datasource)
            
            self.machine_actor.SetCamera(self.camera)

            self.axes_actor = AxesActor(self._datasource)

            LOG.debug("---------translate: {}".format(self.active_wcs_offset[:3]))
            LOG.debug("---------active_wcs_offset: {}".format(self.active_wcs_offset))

            transform = vtk.vtkTransform()
            transform.Translate(*self.active_wcs_offset[:3])
            transform.RotateZ(self._datasource.getRotationOfActiveWcs())
            
            
            # FIXME: need machine coords
            # self.axes_actor.SetUserTransform(transform)
            self.path_actors = OrderedDict()
            self.path_cache_actor = PathCacheActor(self.tooltip_position)


            self.table_model = self._datasource._inifile.find("VTK", "TABLE")
            if self.table_model is not None:
                self.table_actor = TableActor(self.table_model)



            self.spindle_model = self._datasource._inifile.find("VTK", "SPINDLE")

            if self.spindle_model is not None:
                self.spindle_actor = SpindleActor(self._datasource, self.spindle_model)
            
            
            if self.plotMachine == True:
                
                self.machine_parts = self._datasource._inifile.find("VTK", "MACHINE_PARTS")
            
                if self.machine_parts:
                    with open(self.machine_parts, 'r') as f:
                        self.machine_parts_data = yaml.load(f, Loader=yaml.SafeLoader)
                        
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
            connectSetting('backplot.perspective-view', self.viewPerspective)
            connectSetting('backplot.view', self.setView)
            connectSetting('backplot.multitool-colors', self.showMultiColorPath)


    def initialize(self):
        self.path_colors = {'traverse': self._traverse_color,
                       'arcfeed': self._arcfeed_color,
                       'feed': self._feed_color,
                       'dwell': QColor(0, 0, 255, 255),
                       'user': QColor(0, 100, 255, 255)
                       }

        if not IN_DESIGNER:
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
            
            self._datasource.offsetTableChanged.connect(self.on_offset_table_changed)
            self._datasource.activeOffsetChanged.connect(self.update_active_wcs)
            
            self._datasource.toolTableChanged.connect(self.update_tool)
            self._datasource.toolOffsetChanged.connect(self.update_tool)
            # self.status.g5x_index.notify(self.update_g5x_index)

            self.canon = VTKCanon(colors=self.path_colors)

            self.path_actors = self.canon.get_path_actors()

            for wcs_index, path_actor in list(self.path_actors.items()):
                current_offsets = self.wcs_offsets[wcs_index]

                LOG.debug("---------wcs_offsets: {}".format(self.wcs_offsets))
                LOG.debug("---------wcs_index: {}".format(wcs_index))
                LOG.debug("---------current_offsets: {}".format(current_offsets))

                actor_transform = vtk.vtkTransform()
                actor_transform.Translate(*current_offsets[:3])
                actor_transform.RotateZ(current_offsets[9])

                path_actor.SetUserTransform(actor_transform)
                path_actor.SetPosition(*current_offsets[:3])

                LOG.debug("---------current_position: {}".format(*current_offsets[:3]))

                program_bounds_actor = ProgramBoundsActor(self.camera, path_actor)

                axes = path_actor.get_axes_actor()

                self.offset_axes[wcs_index] = axes
                self.program_bounds_actors[wcs_index] = program_bounds_actor

                self.renderer.AddActor(axes)
                self.renderer.AddActor(program_bounds_actor)
                self.renderer.AddActor(path_actor)

            if self.plotMachine == True:
                if self.machine_parts:
                    self.renderer.AddActor(self.machine_parts_actor)
                
                if self.table_model is not None:
                    self.renderer.AddActor(self.table_actor)

            if self.spindle_model is not None:
                self.renderer.AddActor(self.spindle_actor)


            self.renderer.AddActor(self.tool_actor)
            self.renderer.AddActor(self.tool_bit_actor)
            self.renderer.AddActor(self.machine_actor)
            self.renderer.AddActor(self.axes_actor)
            self.renderer.AddActor(self.path_cache_actor)

            self.interactor.ReInitialize()
            self.renderer_window.Render()

            # self.setViewP()
            # self.renderer.ResetCamera()


    # Handle the mouse button events.
    def button_event(self, obj, event):
        LOG.debug("button event {}".format(event))

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
            if self._datasource.isMachineLathe() and False:
                self.pan(self.renderer, self.camera, x, y, lastX, lastY, centerX, centerY)
            else:
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
        self.renderer_window.Render()
        # self.renderer.ResetCamera()
        self.interactor.ReInitialize()

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

        self.renderer_window.Render()

    # Dolly converts y-motion into a camera dolly commands.
    def dolly(self, renderer, camera, x, y, lastX, lastY, centerX, centerY):
        dollyFactor = pow(1.02, (0.5 * (y - lastY)))
        if camera.GetParallelProjection():
            parallelScale = camera.GetParallelScale() * dollyFactor
            camera.SetParallelScale(parallelScale)
        else:
            camera.Dolly(dollyFactor)
            renderer.ResetCameraClippingRange()

        self.renderer_window.Render()

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
        self.renderer_window.Render()

    def tlo(self, tlo):
        LOG.debug(tlo)

    @Slot()
    def reload_program(self, *args, **kwargs):
        LOG.debug("reload_program")
        self.load_program(self._last_filename)

    def load_program(self, fname=None):
        LOG.debug("-------load_program")

        self._datasource._status.addLock()

        # Cleanup the scene, remove any previous actors if any
        for wcs_index, actor in self.path_actors.items():
            LOG.debug("-------load_program wcs_index: {}".format(wcs_index))
            axes_actor = actor.get_axes_actor()
            program_bounds_actor = self.program_bounds_actors[wcs_index]

            # if wcs_index == self.active_wcs_index:

            self.renderer.RemoveActor(axes_actor)
            
            self.renderer.RemoveActor(actor)
            self.renderer.RemoveActor(program_bounds_actor)

            start_actor = self.offset_change_start_actor.get(wcs_index)
            end_actor = self.offset_change_end_actor.get(wcs_index)
            line_actor = self.offset_change_line_actor.get(wcs_index)

            if start_actor:
                self.renderer.RemoveActor(start_actor)
            if end_actor:
                self.renderer.RemoveActor(end_actor)
            if line_actor:
                self.renderer.RemoveActor(line_actor)


        self.path_actors.clear()
        self.offset_axes.clear()
        self.program_bounds_actors.clear()

        start_time = time.time()

        if fname:
            # create the object which handles the canonical motion callbacks
            # (straight_feed, straight_traverse, arc_feed, rigid_tap, etc.)
            self.canon = VTKCanon(colors=self.path_colors)
            self.load(fname)
        else:
            self._datasource._status.removeLock()
            return

        LOG.debug("-------Load time %s seconds ---" % (time.time() - start_time))

        self.canon.draw_lines()

        LOG.debug("-------Draw time %s seconds ---" % (time.time() - start_time))

        self.path_actors = self.canon.get_path_actors()

        self.path_offset_start_point = self.canon.get_offsets_start_point()
        self.path_offset_end_point = self.canon.get_offsets_end_point()

        if self._datasource.isMachineFoam():

            self.foam_offset = self.canon.get_foam()
            LOG.warn(self.foam_offset)
            z = self.foam_offset[0]
            w = self.foam_offset[1]

            self.tool_bit_actor.set_foam_offsets(z, w)

        prev_wcs_index = 0
        path_count = 0
        prev_x_position = 0.0
        prev_y_position = 0.0
        prev_z_position = 0.0

        for wcs_index, actor in self.path_actors.items():
            LOG.debug("---------wcs_offsets: {}".format(self.wcs_offsets))
            LOG.debug("---------wcs_index: {}".format(wcs_index))

            current_offsets = self.wcs_offsets[wcs_index]
            # rotation = self._datasource.getRotationOfActiveWcs()
            LOG.debug("---------current_offsets: {}".format(current_offsets))

            x = current_offsets[self._datasource.getOffsetCoumns().get('X')]
            y = current_offsets[self._datasource.getOffsetCoumns().get('Y')]
            z = current_offsets[self._datasource.getOffsetCoumns().get('Z')]
            
            rotation = current_offsets[self._datasource.getOffsetCoumns().get('R')]
            
            self.rotation_xy_table.insert(wcs_index-1, rotation)
            
            actor_transform = vtk.vtkTransform()
            axes_transform = vtk.vtkTransform()
                
            actor_transform.Translate(x, y, z)
            actor_transform.RotateZ(rotation)
            
            axes_transform.Translate(x, y, z)
            axes_transform.RotateZ(rotation)

            actor.SetUserTransform(actor_transform)

            LOG.debug("---------current_position: {}".format(*current_offsets[:3]))

            program_bounds_actor = ProgramBoundsActor(self.camera, actor)
            program_bounds_actor.showProgramBounds(self.show_program_bounds)

            axes = actor.get_axes_actor()

            self.offset_axes[wcs_index] = axes
            self.program_bounds_actors[wcs_index] = program_bounds_actor

            axes.SetUserTransform(axes_transform)  # TODO: not sure if this is needed

            self.renderer.AddActor(axes)

            self.renderer.AddActor(program_bounds_actor)

            self.renderer.AddActor(actor)
            QApplication.processEvents()

            if len(self.path_actors) > 1:
                # Load the start point of rapid from the next offset paths
                point_01_pos = self.path_offset_start_point[prev_wcs_index]

                points = vtk.vtkPoints()
                vertices = vtk.vtkCellArray()

                point_01_id = [0]
                point_01_id[0] = points.InsertNextPoint(point_01_pos)
                vertices.InsertNextCell(1, point_01_id)

                point = vtk.vtkPolyData()
                point.SetPoints(points)
                point.SetVerts(vertices)

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputData(point)

                actor_point_1 = vtk.vtkActor()
                actor_point_1.SetMapper(mapper)
                actor_point_1.GetProperty().SetColor(self.path_colors.get("arcfeed").getRgb()[0:3])
                actor_point_1.GetProperty().SetPointSize(5)
                actor_point_1.SetUserTransform(actor_transform)
                # actor_point_1.SetPosition(*xyz)

                self.offset_change_start_actor[wcs_index] = actor_point_1
                self.renderer.AddActor(actor_point_1)

                # Load the end point of the rapid from the first offset path
                points = vtk.vtkPoints()
                vertices = vtk.vtkCellArray()

                point_02_pos = self.path_offset_end_point[prev_wcs_index]
                point_02_id = [0]
                point_02_id[0] = points.InsertNextPoint(point_02_pos)
                vertices.InsertNextCell(1, point_02_id)

                point = vtk.vtkPolyData()
                point.SetPoints(points)
                point.SetVerts(vertices)
                
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputData(point)

                actor_point_2 = vtk.vtkActor()
                actor_point_2.SetMapper(mapper)
                actor_point_2.GetProperty().SetColor(self.path_colors.get("user").getRgb()[0:3])
                actor_point_2.GetProperty().SetPointSize(5)
                actor_point_2.SetUserTransform(actor_transform)
                # actor_point_2.SetPosition(*xyz)

                self.offset_change_end_actor[wcs_index] = actor_point_2
                self.renderer.AddActor(actor_point_2)

                if path_count > 0:
                    
                    p1_position = self.offset_change_end_actor[prev_wcs_index].GetCenter()
                    # p1_rotation = self.offset_change_end_actor[prev_wcs_index].GetUserTransform().GetOrientation()[2]
                    
                    p2_position = self.offset_change_start_actor[wcs_index].GetCenter()
                    # p2_rotation = self.offset_change_end_actor[wcs_index].GetUserTransform().GetOrientation()[2]
                    
                    # print(p1_position, p1_rotation)
                    # print(p2_position, p2_rotation)
                    
                    
                    actor_p01_pos = [*p1_position]

                    actor_p02_pos = [*p2_position]

                    actor_p03_pos = [p2_position[0],
                                     p2_position[1],
                                     p1_position[2]]

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
                    # actor_line.SetUserTransform(actor_transform)

                    self.offset_change_line_actor[wcs_index] = actor_line

                    self.renderer.AddActor(actor_line)

            prev_x_position = x
            prev_y_position = y
            prev_y_position = z
            
            path_count += 1
            prev_wcs_index = wcs_index
        # self.renderer.AddActor(self.axes_actor)
        self.renderer_window.Render()

        if self.program_view_when_loading_program:
            self.setViewProgram(self.program_view_when_loading_program_view)

        QTimer.singleShot(300, self._datasource._status.removeLock)

    def motion_type(self, value):
        
        LOG.debug("-----motion_type is: {}".format(value))
        
        if value == linuxcnc.MOTION_TYPE_TOOLCHANGE:
            self.update_tool()

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
        
        active_wcs_offset = self._datasource.getWcsOffsets()[self._datasource.getActiveWcsIndex()]
        if self._datasource.isMachineJet():
            # update the position for JET machines so spindle/tool is
            # aligned to active WCS
            list_pos = list(position)
            list_pos[2] = active_wcs_offset[2]
            position = tuple(list_pos)
            
        self.spindle_position = position[:3]
        self.spindle_rotation = position[3:6]

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)
        tool_transform.RotateX(-self.spindle_rotation[0])
        tool_transform.RotateY(-self.spindle_rotation[1])
        tool_transform.RotateZ(-self.spindle_rotation[2])

        if self.spindle_model is not None:
            self.spindle_actor.SetUserTransform(tool_transform)

        if self.plotMachine == True:
            if self.machine_parts:

                print(f"Machine : {self.machine_parts_actor}")

                # self.machine_parts_actor.InitPathTraversal()
                # parts = self.machine_parts_actor.GetParts()
                
                self.machine_parts_actor.InitPathTraversal()
                for part in self.get_asm_parts(self.machine_parts_actor):
                    print(f"PATH: {part}")
                    # part_prop = path.GetViewProp()
                    # if isinstance(part, vtk.vtkActor):
                    #    print(f"Actor FOUND: ")
                    #    self.move_part(part)
                    if isinstance(part, vtk.vtkAssembly):
                        print(f"ASM FOUND: ")
                        self.move_part(part)
                    #

                        # for p in part.GetParts():
                        #     if isinstance(p, vtk.vtkActor):
                        #         print(f"Actor FOUND: ")
                        #         self.move_part(p)
                        #     # if isinstance(p, vtk.vtkAssembly):
                            #     self.move_part(p)

        self.tool_actor.SetUserTransform(tool_transform)

        if self._datasource.isMachineFoam():
            self.tool_bit_actor.set_position(position)
        else:
            self.tool_bit_actor.SetUserTransform(tool_transform)

        tlo = self._datasource.getToolOffset()
        self.tooltip_position = [pos - tlo for pos, tlo in zip(self.spindle_position, tlo[:3])]

        if self._datasource.isMachineJet():
            # if a jet based machine (plasma, water jet, laser) suppress
            # plotting the Z movements
            self.tooltip_position = self.spindle_position
        else:
            self.tooltip_position = [pos - tlo for pos, tlo in zip(self.spindle_position, tlo[:3])]
            

        # self.spindle_actor.SetPosition(self.spindle_position)
        # self.tool_actor.SetPosition(self.spindle_position)

        #print(f"Update tool tip position {time.time()}")
        self.path_cache_actor.add_line_point(self.tooltip_position)
        self.renderer_window.Render()
        
    def move_part(self, part):
                   
        part_axis = part.GetPartAxis()
        part_type = part.GetPartType()

        print(part_axis)
        print(part_type)

        part_transform = vtk.vtkTransform()  
        
        if part_type == "linear":

            #part_position = self.joints[part_joint].input.value
            
            if part_axis == "x":
                part.SetPosition(self.spindle_position[0], 0, 0)
            elif part_axis == "y":
                part.SetPosition(0, self.spindle_position[1], 0)
            elif part_axis == "z":
                part.SetPosition(0, 0, self.spindle_position[2])
            elif part_axis == "-x":
                part.SetPosition(-self.spindle_position[0], 0, 0)
            elif part_axis == "-y":
                part.SetPosition(0, -self.spindle_position[1], 0)
            elif part_axis == "-z":
                part.SetPosition(0, 0, -self.spindle_position[2])
                
            # if part_axis == "x":
            #     part_transform.Translate(self.spindle_position[0], 0, 0)
            # elif part_axis == "y":
            #     part_transform.Translate(0, self.spindle_position[1], 0)
            # elif part_axis == "z":
            #     part_transform.Translate(0, 0, self.spindle_position[2])
            # elif part_axis == "-x":
            #     part_transform.Translate(-self.spindle_position[0], 0, 0)
            # elif part_axis == "-y":
            #     part_transform.Translate(0, -self.spindle_position[1], 0)
            # elif part_axis == "-z":
            #     part_transform.Translate(0, 0, -self.spindle_position[2])
            #
            # part.SetUserTransform(part_transform)

        elif part_type == "angular":
            # part_position = self.joints[part_joint].input.value
            
            if part_axis == "a":
                part.SetOrientation(self.spindle_rotation[0], 0, 0)
            elif part_axis== "b":
                part.SetOrientation(0, self.spindle_rotation[1], 0)
            elif part_axis == "c":
                part.SetOrientation(0, 0, self.spindle_rotation[2])
            elif part_axis == "-a":
                part.SetOrientation(-self.spindle_rotation[0], 0, 0)
            elif part_axis == "-b":
                part.SetOrientation(0, -self.spindle_rotation[1], 0)
            elif part_axis == "-c":
                part.SetOrientation(0, 0, -self.spindle_rotation[2])
 
            # if part_axis == "a":
            #     part_transform.RotateX(-self.spindle_rotation[0])
            # elif part_axis== "b":
            #     part_transform.RotateY(-self.spindle_rotation[1])
            # elif part_axis == "c":
            #     part_transform.RotateZ(-self.spindle_rotation[2])
            # elif part_axis == "-a":
            #     part_transform.RotateX(self.spindle_rotation[0])
            # elif part_axis == "-b":
            #     part_transform.RotateY(self.spindle_rotation[1])
            # elif part_axis == "-c":
            #     part_transform.RotateZ(self.spindle_rotation[2])  
            #
            # part.SetUserTransform(part_transform)

    def update_joints(self, joints):
        self.joints = joints
        
    def on_offset_table_changed(self, offset_table):
        LOG.debug("on_offset_table_changed")
        
        self.wcs_offsets = offset_table

        self.rotate_and_translate()
        
    def update_rotation_xy(self, rot):
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        LOG.debug("@@@@@@@@@@  ROTATION SIGNAL  @@@@@@@@@")
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        
        self.active_rotation = rot
        self.rotation_xy_table[self.active_wcs_index] = rot
        
        self.rotate_and_translate()
        
    def update_g5x_offset(self, offset):
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        LOG.debug("@@@@@@@@@@  OFFSET   SIGNAL  @@@@@@@@@")
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        
        self.active_wcs_offset = offset
        
        self.rotate_and_translate()
        
        # TODO implement rapid recalculation
        
    def rotate_and_translate(self):
        
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        LOG.debug("@@@@@@@@@ ROTATE & TRANSLATE @@@@@@@@@")
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        
        # self.axes_actor.SetUserTransform(transform)

        path_count = 0
        prev_wcs_index = 0
        prev_offset_x = 0.0
        prev_offset_y = 0.0
        prev_offset_z = 0.0

        for wcs_index, path_actor in self.path_actors.items():
            
            axes_actor = path_actor.get_axes_actor()
            if axes_actor:
                self.renderer.RemoveActor(axes_actor)
                
            offset_change_actor = self.offset_change_line_actor.get(wcs_index)
            if offset_change_actor:
                self.renderer.RemoveActor(offset_change_actor)
                
            program_bounds_actor = self.program_bounds_actors.get(wcs_index)
            if program_bounds_actor:
                self.renderer.RemoveActor(program_bounds_actor)
        
            
            current_offsets = self.wcs_offsets[wcs_index]

            x = current_offsets[self._datasource.getOffsetCoumns().get('X')]
            y = current_offsets[self._datasource.getOffsetCoumns().get('Y')]
            z = current_offsets[self._datasource.getOffsetCoumns().get('Z')]
            
            rotation = current_offsets[self._datasource.getOffsetCoumns().get('R')]
            
            LOG.debug("--------wcs_index: {}, active_wcs_index: {}".format(wcs_index, self.active_wcs_index))

            actor_transform = vtk.vtkTransform()
            axes_transform = vtk.vtkTransform()

            actor_transform.Translate(x, y, z)
            actor_transform.RotateZ(rotation)

            axes_transform.Translate(x, y, z)
            axes_transform.RotateZ(rotation)

            axes_actor.SetUserTransform(axes_transform)
            path_actor.SetUserTransform(actor_transform)

            program_bounds_actor = ProgramBoundsActor(self.camera, path_actor)
            program_bounds_actor.showProgramBounds(self.show_program_bounds)

            self.renderer.AddActor(axes_actor)
            self.renderer.AddActor(program_bounds_actor)

            self.program_bounds_actors[wcs_index] = program_bounds_actor
        

            if len(self.path_actors) > 1:

                self.offset_change_start_actor[wcs_index].SetUserTransform(actor_transform)
                self.offset_change_end_actor[wcs_index].SetUserTransform(actor_transform)
            
                                                
                if path_count > 0:
                    
                    point_01 = self.offset_change_end_actor.get(prev_wcs_index)
                    point_02 = self.offset_change_start_actor.get(wcs_index)
                    
                    
                    point_01_pos = point_01.GetCenter()
                    point_02_pos = point_02.GetCenter()
                    
                    actor_p01_pos = [point_01_pos[0],
                                     point_01_pos[1],
                                     point_01_pos[2]]
    
                    actor_p02_pos = [point_02_pos[0],
                                     point_02_pos[1],
                                     point_02_pos[2]]
    
                    actor_p03_pos = [point_02_pos[0],
                                     point_02_pos[1],
                                     point_01_pos[2]]
    
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
    
                    self.offset_change_line_actor[wcs_index] = actor_line
    
                    self.renderer.AddActor(actor_line)

                prev_wcs_index = wcs_index
                
                prev_offset_x = x
                prev_offset_y = y
                prev_offset_z = z
                
                path_count += 1

        self.interactor.ReInitialize()
        self.renderer_window.Render()
        
    def update_g5x_index(self, index):
        
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        LOG.debug("@@@@@@@@@ OFFSET INDEX SIGNAL @@@@@@@@")
        LOG.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        
        LOG.debug("--------update_g5x_index {}".format(index))
        
        self.active_wcs_index = index
        
        # self.rotate_and_translate()
        #
        # transform = vtk.vtkTransform()
        # transform.Translate(self.active_wcs_offset[:3])
        # transform.RotateZ(self.active_rotation)
        #
        # # self.axes_actor.SetUserTransform(transform)
        #
        # for wcs_index, path_actor in list(self.path_actors.items()):
        #
        #     #old_program_bounds_actor = self.program_bounds_actors[wcs_index]
        #     #self.renderer.RemoveActor(old_program_bounds_actor)
        #
        #     axes = path_actor.get_axes_actor()
        #
        #     LOG.debug("--------wcs_index: {}, active_wcs_index: {}".format(wcs_index, self.active_wcs_index))
        #
        #     axes.SetUserTransform(transform)
        #
        #     # if wcs_index == self.active_wcs_index:
        #     #     path_transform = vtk.vtkTransform()
        #     #     path_transform.Translate(*offset[:3])
        #     #     path_transform.RotateZ(self.active_rotation)
        #     #
        #     #     path_actor.SetUserTransform(transform)
        #
        #     program_bounds_actor = ProgramBoundsActor(self.camera, path_actor)
        #     program_bounds_actor.showProgramBounds(self.show_program_bounds)
        #
        #     # self.renderer.AddActor(program_bounds_actor)
        #
        #     # self.program_bounds_actors[wcs_index] = program_bounds_actor
        #
        # self.interactor.ReInitialize()
        # self.renderer_window.Render()
    
    def update_active_wcs(self, wcs_index):
        
        self.active_wcs_index = wcs_index
        
        # LOG.debug("--------update_active_wcs index: {}".format(wcs_index))
        # LOG.debug("--------self.wcs_offsets: {}".format(self.wcs_offsets))
        #
        # position = self.wcs_offsets[wcs_index]
        # rotation = self.active_rotation
        #
        # LOG.debug("--------position: {}".format(position))
        # LOG.debug("--------rotation: {}".format(rotation))
        #
        # transform = vtk.vtkTransform()
        #
        # transform.Translate(*position[:3])
        # transform.RotateZ(rotation)
        #
        # for wcs_index, path_actor in list(self.path_actors.items()):
        #     LOG.debug("--------wcs_index: {}, active_wcs_index: {}".format(wcs_index, self.active_wcs_index))
        #
        #     if wcs_index == self.active_wcs_index:
        #         axes = path_actor.get_axes_actor()
        #         axes.SetUserTransform(transform)
        #
        #
        # self.interactor.ReInitialize()
        # self.renderer_window.Render()

    def update_g92_offset(self, g92_offset):
        LOG.debug("---------update_g92_offset: {}".format(g92_offset))
        if self._datasource.isModeMdi() or self._datasource.isModeAuto():
            self.g92_offset = g92_offset

            path_offset = list(map(add, self.g92_offset, self.original_g92_offset))
            LOG.debug("---------path_offset: {}".format(path_offset))

            for wcs_index, actor in list(self.path_actors.items()):

                old_program_bounds_actor = self.program_bounds_actors[wcs_index]
                self.renderer.RemoveActor(old_program_bounds_actor)
                # determine change in g92 offset since path was drawn

                new_path_position = list(map(add, self.wcs_offsets[wcs_index][:9], path_offset))
                LOG.debug("---------new_path_position: {}".format(path_offset))

                axes = actor.get_axes_actor()

                path_transform = vtk.vtkTransform()
                path_transform.Translate(*new_path_position[:3])

                # self.axes_actor.SetUserTransform(path_transform)
                axes.SetUserTransform(path_transform)
                actor.SetUserTransform(path_transform)

                program_bounds_actor = ProgramBoundsActor(self.camera, actor)
                program_bounds_actor.showProgramBounds(self.show_program_bounds)

                self.renderer.AddActor(program_bounds_actor)

                self.program_bounds_actors[wcs_index] = program_bounds_actor

            self.interactor.ReInitialize()
            self.renderer_window.Render()

    def update_tool(self):

        LOG.debug("update_tool")

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

        if self._datasource.isMachineFoam():
            self.renderer.RemoveActor(self.tool_bit_actor)
            self.tool_bit_actor = ToolBitActor(self._datasource)
            self.tool_bit_actor.SetUserTransform(tool_transform)
        else:
            self.tool_bit_actor.SetUserTransform(tool_transform)

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.tool_bit_actor)

        self.renderer_window.Render()

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

        self.spindle_actor.SetVisibility(value)

        # self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewOrtho(self):
        self.camera.ParallelProjectionOn()
        # self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewPersp(self):
        self.camera.ParallelProjectionOff()
        # self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot(int)
    @Slot(str)
    @Slot(object)
    def setView(self, view):
        if isinstance(view, int):
            view = ['X', 'XZ', 'XZ2', 'Y', 'Z', 'Z2', 'P'][view]

        view = view.upper()
        LOG.debug("Setting view to: %s", view)

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

    @Slot()
    def setViewP(self):
        self.active_view = 'P'
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(self.position_mult, -self.position_mult, self.position_mult)
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewX(self):
        self.active_view = 'X'
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(position[0], position[1] - self.position_mult, position[2])
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewXZ(self):
        self.active_view = 'XZ'
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(position[0], position[1] + self.position_mult, position[2])
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(1, 0, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewXZ2(self):
        self.active_view = 'XZ2'
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(position[0], position[1] - self.position_mult, position[2])
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(-1, 0, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewY(self):
        self.active_view = 'Y'
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(position[0] + self.position_mult, position[1], position[2])
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewZ(self):
        self.active_view = 'Z'
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(position[0], position[1], position[2] + self.position_mult)
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(0, 1, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewZ2(self):
        self.active_view = 'Z2'
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(position[0], position[1], position[2] + self.position_mult)
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(1, 0, 0)
        self.__doCommonSetViewWork()

    @Slot()
    def setViewMachine(self):
        LOG.debug('-----setViewMachine')
        machine_bounds = self.machine_actor.GetBounds()
        LOG.debug('-----machine_bounds: {}'.format(machine_bounds))

        machine_bounds = self.machine_actor.GetBounds()
        machine_center = ((machine_bounds[0] + machine_bounds[1]) / 2,
                          (machine_bounds[2] + machine_bounds[3]) / 2,
                          (machine_bounds[4] + machine_bounds[5]) / 2
                          )

        LOG.debug('-----machine_center: {}'.format(machine_center))

        self.camera = self.renderer.GetActiveCamera()

        self.camera.SetFocalPoint(machine_center[0],
                                  machine_center[1],
                                  machine_center[2])

        self.camera.SetPosition(machine_center[0] + self.position_mult,
                                -(machine_center[1] + self.position_mult),
                                machine_center[2] + self.position_mult)
        
        x_dist = abs(machine_bounds[0] - machine_bounds[1])
        y_dist = abs(machine_bounds[2] - machine_bounds[3])
        z_dist = abs(machine_bounds[4] - machine_bounds[5])

        LOG.debug('-----x_dist: {}'.format(x_dist))
        LOG.debug('-----y_dist: {}'.format(y_dist))
        LOG.debug('-----z_dist: {}'.format(z_dist))

        scale = max(x_dist, y_dist, z_dist)
        new_scale = scale * 0.65
        
        self.camera.SetParallelScale(new_scale)
        self.camera.SetViewUp(0, 0, 1)
        
        self.__doCommonSetViewWork()

    @Slot()
    def setViewProgram(self,view='p'):
        LOG.debug('-----setViewProgram')
        
        if len(self.program_bounds_actors) == 0:
            LOG.debug('-----setViewProgram skiped, no program loaded')
            return
        
        try:
            program_bounds = self.program_bounds_actors[self.active_wcs_index].GetBounds()
        except KeyError:
            LOG.warn('-----setViewProgram skiped, no active wcs')
            return
        
        LOG.debug('-----program_bounds: {}'.format(program_bounds))

        program_center = ((program_bounds[0] + program_bounds[1]) / 2,
                          (program_bounds[2] + program_bounds[3]) / 2,
                          (program_bounds[4] + program_bounds[5]) / 2)

        LOG.debug('-----program_center: {}'.format(program_center))

        self.camera = self.renderer.GetActiveCamera()
        self.camera.SetFocalPoint(program_center[0],
                                  program_center[1],
                                  program_center[2])

        # self.camera.SetPosition(program_center[0] + self.position_mult,
        #                         -(program_center[1] + self.position_mult),
        #                         program_center[2] + self.position_mult)


        x_up = 0
        y_up = 0
        z_up = 0
        pc_x = program_center[0]
        pc_y = program_center[1]
        pc_z = program_center[2]
        if view.lower() == 'x':
            pc_y = program_center[1] - self.position_mult
            z_up = 1
        elif view.lower() == 'y':
            pc_x = program_center[0] + self.position_mult
            z_up = 1
        elif view.lower() == 'xz':
            pc_y = program_center[1] + self.position_mult
            x_up = 1
        elif view.lower() == 'xz2':
            pc_y = program_center[1] - self.position_mult
            x_up = -1
        elif view.lower() == 'z':
            pc_z = program_center[2] + self.position_mult
            y_up = 1
        elif view.lower() == 'z2':
            pc_z = program_center[2] + self.position_mult
            x_up = 1
        else:
            # treat as P
            pc_x = program_center[0] + self.position_mult
            pc_y = -(program_center[1] + self.position_mult)
            pc_z = program_center[2] + self.position_mult
            z_up = 1

        self.camera.SetPosition(pc_x, pc_y, pc_z)

        x_dist = abs(program_bounds[0] - program_bounds[1])
        y_dist = abs(program_bounds[2] - program_bounds[3])
        z_dist = abs(program_bounds[4] - program_bounds[5])

        LOG.debug('-----x_dist: {}'.format(x_dist))
        LOG.debug('-----y_dist: {}'.format(y_dist))
        LOG.debug('-----z_dist: {}'.format(z_dist))

        scale = max(x_dist, y_dist, z_dist)

        self.camera.SetParallelScale(scale)
        self.camera.SetViewUp(x_up, y_up, z_up)
        self.__doCommonSetViewWork()
        self.clearLivePlot()



    @Slot()
    def setViewPath(self):
        LOG.debug('-----setViewPath')
        position = self.wcs_offsets[self.active_wcs_index]
        self.camera.SetPosition(position[0] + self.position_mult,
                                -(position[1] + self.position_mult),
                                position[2] + self.position_mult)
        self.camera.SetFocalPoint(position[:3])
        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

    def __doCommonSetViewWork(self):
        # This is common logic for all setView**** methods.
        self.camera.SetClippingRange(self.clipping_range_near, self.clipping_range_far)
        self.renderer_window.Render()
        self.interactor.ReInitialize()

    @Slot()
    def printView(self):
        LOG.debug('LOG.debug view stats')
        fp = self.camera.GetFocalPoint()
        LOG.debug('focal point {}'.format(fp))
        p = self.camera.GetPosition()
        LOG.debug(('position {}'.format(p)))
        # dist = math.sqrt( (p[0]-fp[0])**2 + (p[1]-fp[1])**2 + (p[2]-fp[2])**2 )
        # print(dist)
        # self.camera.SetPosition(10, -40, -1)
        # self.setViewUp(0.0, 1.0, 0.0)
        # self.renderer.ResetCamera()
        vu = self.camera.GetViewUp()
        LOG.debug('view up {}'.format(vu))
        d = self.camera.GetDistance()
        LOG.debug(('distance {}'.format(d)))
        # self.interactor.ReInitialize()

    @Slot()
    def clearLivePlot(self):
        LOG.debug('clear live plot')
        self.renderer.RemoveActor(self.path_cache_actor)
        self.path_cache_actor = PathCacheActor(self.tooltip_position)
        self.renderer.AddActor(self.path_cache_actor)
        self.renderer_window.Render()

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
            LOG.debug("---camera parallel projection {}".format(parallelScale))
        else:
            self.renderer.ResetCameraClippingRange()
            self.camera.Zoom(1.1)
            LOG.debug("---camera clipping range")

        self.renderer_window.Render()

    @Slot()
    def zoomOut(self):
        if self.camera.GetParallelProjection():
            parallelScale = self.camera.GetParallelScale() * 1.1
            self.camera.SetParallelScale(parallelScale)
        else:
            self.renderer.ResetCameraClippingRange()
            self.camera.Zoom(0.9)

        self.renderer_window.Render()

    @Slot(bool)
    def alphaBlend(self, alpha):
        LOG.debug('alpha blend')

    @Slot(bool)
    @Slot(object)
    def showGrid(self, grid):
        LOG.debug('show grid')
        self.machine_actor.showGridlines(grid)
        self.renderer_window.Render()

    @Slot(bool)
    @Slot(object)
    def showProgramBounds(self, show):
        self.show_program_bounds = show
        for wcs_index, actor in list(self.path_actors.items()):
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            if program_bounds_actor is not None:
                program_bounds_actor.showProgramBounds(self.show_program_bounds)
                self.renderer_window.Render()

    @Slot()
    def toggleProgramBounds(self):
        for wcs_index, actor in list(self.path_actors.items()):
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            self.showProgramBounds(not program_bounds_actor.GetXAxisVisibility())

    #
    # @Slot(bool)
    # @Slot(object)
    # def showProgramTicks(self, ticks):
    #     for wcs_index, actor in list(self.path_actors.items()):
    #         program_bounds_actor = self.program_bounds_actors[wcs_index]
    #         if program_bounds_actor is not None:
    #             program_bounds_actor.showProgramTicks(ticks)
    #     self.renderer_window.Render()
    #
    # @Slot()
    # def toggleProgramTicks(self):
    #     for wcs_index, actor in list(self.path_actors.items()):
    #         program_bounds_actor = self.program_bounds_actors[wcs_index]
    #         self.showProgramTicks(not program_bounds_actor.GetXAxisTickVisibility())
    #
    # @Slot(bool)
    # @Slot(object)
    # def showProgramLabels(self, labels):
    #     for wcs_index, actor in list(self.path_actors.items()):
    #         program_bounds_actor = self.program_bounds_actors[wcs_index]
    #         if program_bounds_actor is not None:
    #             program_bounds_actor.showProgramLabels(labels)
    #     self.renderer_window.Render()
    #
    # @Slot()
    # def toggleProgramLabels(self):
    #     for wcs_index, actor in list(self.path_actors.items()):
    #         program_bounds_actor = self.program_bounds_actors[wcs_index]
    #         self.showProgramLabels(not program_bounds_actor.GetXAxisLabelVisibility())

    @Slot(bool)
    @Slot(object)
    def showMachineBounds(self, bounds):
        self.machine_actor.showMachineBounds(bounds)
        self.renderer_window.Render()

    @Slot()
    def toggleMachineBounds(self):
        self.showMachineBounds(not self.machine_actor.GetXAxisVisibility())

    @Slot(bool)
    @Slot(object)
    def showMachineTicks(self, ticks):
        self.machine_actor.showMachineTicks(ticks)
        self.renderer_window.Render()

    @Slot()
    def toggleMachineTicks(self):
        self.showMachineTicks(not self.machine_actor.GetXAxisTickVisibility())

    @Slot(bool)
    @Slot(object)
    def showMachineLabels(self, labels):
        self.machine_actor.showMachineLabels(labels)
        self.renderer_window.Render()

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
    
    
    @Property(bool)
    def plotMachine(self):
        return self._plot_machine

    @plotMachine.setter
    def plotMachine(self, value):
        self._plot_machine = value

    @plotMachine.reset
    def plotMachine(self):
        self.plotMachine = False


    @Property(QColor)
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self._background_color = color

        self.renderer.SetBackground(color.getRgbF()[:3])
        self.renderer_window.Render()

    @backgroundColor.reset
    def backgroundColor(self):
        self._background_color = QColor(0, 0, 0)

        self.renderer.GradientBackgroundOff()
        self.renderer_window.Render()


    @Property(QColor)
    def backgroundColor2(self):
        return self._background_color2

    @backgroundColor2.setter
    def backgroundColor2(self, color2):
        self._background_color2 = color2

        self.renderer.GradientBackgroundOn()
        self.renderer.SetBackground2(color2.getRgbF()[:3])
        self.renderer_window.Render()

    @backgroundColor2.reset
    def backgroundColor2(self):
        self._background_color2 = QColor(0, 0, 0)

        self.renderer.GradientBackgroundOff()
        self.renderer_window.Render()

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
