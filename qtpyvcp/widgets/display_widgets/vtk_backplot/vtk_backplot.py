import linuxcnc
import os
from collections import OrderedDict
from operator import add
import time

import vtk
import vtk.qt
from qtpy.QtCore import Property, Slot
from qtpy.QtGui import QColor

# Fix poligons not drawing correctly on some GPU
# https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1

vtk.qt.QVTKRWIBase = "QGLWidget"

# Fix end

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import connectSetting

from base_backplot import BaseBackPlot
from axes_actor import AxesActor
from machine_actor import MachineActor
from tool_actor import ToolActor
from path_cache_actor import PathCacheActor
from program_bounds_actor import ProgramBoundsActor
from vtk_cannon import VTKCanon
from linuxcnc_datasource import LinuxCncDataSource

LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER', False)
NUMBER_OF_WCS = 9

# turn on antialiasing
from PyQt5.QtOpenGL import QGLFormat
f = QGLFormat()
f.setSampleBuffers(True)
QGLFormat.setDefaultFormat(f)

class VTKBackPlot(QVTKRenderWindowInteractor, VCPWidget, BaseBackPlot):
    def __init__(self, parent=None):
        super(VTKBackPlot, self).__init__(parent)
        LOG.debug("---------using refactored vtk code")
        self._datasource = LinuxCncDataSource()
        self.canon_class = VTKCanon

        self.parent = parent
        self.ploter_enabled = True
        self.touch_enabled = False
        self.pan_mode = False
        self.line = None
        self._last_filename = str()
        self.rotating = 0
        self.panning = 0
        self.zooming = 0

        # assume that we are standing upright and compute azimuth around that axis
        self.natural_view_up = (0, 0, 1)

        # properties
        self._background_color = QColor(0, 0, 0)
        self._background_color2 = QColor(0, 0, 0)
        self._enableProgramTicks = True

        self.active_wcs_index = self._datasource.getActiveWcsIndex()
        self.wcs_offsets = self._datasource.getWcsOffsets()
        self.active_wcs_offset = self._datasource.getActiveWcsOffsets()
        self.g92_offset = self._datasource.getG92_offset()

        LOG.debug("---------active_wcs_index {}".format(self.active_wcs_index))
        LOG.debug("---------active_wcs_offset {}".format(self.active_wcs_offset))
        LOG.debug("---------wcs_offsets {}".format(self.wcs_offsets))

        self.original_g5x_offset = [0.0] * NUMBER_OF_WCS
        self.original_g92_offset = [0.0] * NUMBER_OF_WCS

        self.spindle_position = (0.0, 0.0, 0.0)
        self.spindle_rotation = (0.0, 0.0, 0.0)
        self.tooltip_position = (0.0, 0.0, 0.0)

        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()

        if self._datasource.isMachineMetric():
            self.position_mult = 1000 #500 here works for me
            self.clipping_range_near = 0.01
            self.clipping_range_far = 10000.0 #TODO: check this value
        else:
            self.position_mult = 100
            self.clipping_range_near = 0.001
            self.clipping_range_far = 1000.0 #TODO: check this value

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

        self.machine_actor = MachineActor(self._datasource)
        self.machine_actor.SetCamera(self.camera)

        self.axes_actor = AxesActor(self._datasource)

        LOG.debug("---------translate1: {}".format(self.active_wcs_offset[:3]))
        LOG.debug("---------active_wcs_offset: {}".format(self.active_wcs_offset))

        transform = vtk.vtkTransform()
        transform.Translate(*self.active_wcs_offset[:3])
        transform.RotateZ(self.active_wcs_offset[9])
        self.axes_actor.SetUserTransform(transform)

        self.path_cache_actor = PathCacheActor(self.tooltip_position)
        self.tool_actor = ToolActor(self._datasource)

        self.offset_axes = OrderedDict()
        self.program_bounds_actors = OrderedDict()
        self.show_program_bounds = bool()

        if not IN_DESIGNER:
            self.canon = self.canon_class()
            self.path_actors = self.canon.get_path_actors()

            for wcs_index, path_actor in self.path_actors.items():
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

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.machine_actor)
        self.renderer.AddActor(self.axes_actor)
        self.renderer.AddActor(self.path_cache_actor)

        self.renderer.ResetCamera()

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
        self._datasource.g5xOffsetChanged.connect(self.update_g5x_offset)
        self._datasource.g92OffsetChanged.connect(self.update_g92_offset)
        self._datasource.offsetTableChanged.connect(self.on_offset_table_changed)
        self._datasource.activeOffsetChanged.connect(self.update_active_wcs)
        self._datasource.toolTableChanged.connect(self.update_tool)
        self._datasource.toolOffsetChanged.connect(self.update_tool)
        # self.status.g5x_index.notify(self.update_g5x_index)

        # view settings
        connectSetting('backplot.show-grid', self.showGrid)
        connectSetting('backplot.show-program-bounds', self.showProgramBounds)
        connectSetting('backplot.show-program-labels', self.showProgramLabels)
        connectSetting('backplot.show-program-ticks', self.showProgramTicks)
        connectSetting('backplot.show-machine-bounds', self.showMachineBounds)
        connectSetting('backplot.show-machine-labels', self.showMachineLabels)
        connectSetting('backplot.show-machine-ticks', self.showMachineTicks)
        connectSetting('backplot.perspective-view', self.viewPerspective)
        connectSetting('backplot.view', self.setView)
        connectSetting('backplot.multitool-colors', self.showMultiColorPath)

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
            if self._datasource.isMachineLathe():
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

        # Cleanup the scene, remove any previous actors if any
        for wcs_index, actor in self.path_actors.items():
            LOG.debug("-------load_program wcs_index: {}".format(wcs_index))
            axes_actor = actor.get_axes_actor()
            program_bounds_actor = self.program_bounds_actors[wcs_index]

            self.renderer.RemoveActor(axes_actor)
            self.renderer.RemoveActor(actor)
            self.renderer.RemoveActor(program_bounds_actor)

        self.path_actors.clear()
        self.offset_axes.clear()
        self.program_bounds_actors.clear()

        start_time = time.time()

        if fname:
            self.load(fname)

        if self.canon is None:
            return

        LOG.debug("-------Load time %s seconds ---" % (time.time() - start_time))

        self.canon.draw_lines()

        LOG.debug("-------Draw time %s seconds ---" % (time.time() - start_time))
        self.path_actors = self.canon.get_path_actors()

        for wcs_index, actor in self.path_actors.items():
            current_offsets = self.wcs_offsets[wcs_index]

            LOG.debug("---------wcs_offsets: {}".format(self.wcs_offsets))
            LOG.debug("---------wcs_index: {}".format(wcs_index))
            LOG.debug("---------current_offsets: {}".format(current_offsets))

            actor_transform = vtk.vtkTransform()
            actor_transform.Translate(*current_offsets[:3])
            actor_transform.RotateZ(current_offsets[9])

            actor.SetUserTransform(actor_transform)
            #actor.SetPosition(path_position[:3])

            LOG.debug("---------current_position: {}".format(*current_offsets[:3]))

            program_bounds_actor = ProgramBoundsActor(self.camera, actor)
            program_bounds_actor.showProgramBounds(self.show_program_bounds)

            axes = actor.get_axes_actor()

            self.offset_axes[wcs_index] = axes
            self.program_bounds_actors[wcs_index] = program_bounds_actor

            axes.SetUserTransform(actor_transform) #TODO: not sure if this is needed

            self.renderer.AddActor(axes)
            self.renderer.AddActor(program_bounds_actor)
            self.renderer.AddActor(actor)

        self.renderer.AddActor(self.axes_actor)
        self.renderer_window.Render()

    def motion_type(self, value):
        LOG.debug("-----motion_type is: {}".format(value))
        if value == linuxcnc.MOTION_TYPE_TOOLCHANGE:
            self.update_tool()

    def update_position(self, position):  # the tool movement

        self.spindle_position = position[:3]
        self.spindle_rotation = position[3:6]

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)
        tool_transform.RotateX(-self.spindle_rotation[0])
        tool_transform.RotateY(-self.spindle_rotation[1])
        tool_transform.RotateZ(-self.spindle_rotation[2])

        self.tool_actor.SetUserTransform(tool_transform)

        tlo = self._datasource.getToolOffset()
        self.tooltip_position = [pos - tlo for pos, tlo in zip(self.spindle_position, tlo[:3])]

        # self.spindle_actor.SetPosition(self.spindle_position)
        # self.tool_actor.SetPosition(self.spindle_position)
        self.path_cache_actor.add_line_point(self.tooltip_position)
        self.renderer_window.Render()

    def on_offset_table_changed(self, table):
        LOG.debug("on_offset_table_changed")
        self.wcs_offsets = table

    def update_g5x_offset(self, offset):
        LOG.debug("--------update_g5x_offset {}".format(offset))

        transform = vtk.vtkTransform()
        transform.Translate(*offset[:3])
        transform.RotateZ(offset[9])

        self.axes_actor.SetUserTransform(transform)

        for wcs_index, path_actor in self.path_actors.items():

            old_program_bounds_actor = self.program_bounds_actors[wcs_index]
            self.renderer.RemoveActor(old_program_bounds_actor)

            axes = path_actor.get_axes_actor()

            LOG.debug("--------wcs_index: {}, active_wcs_index: {}".format(wcs_index, self.active_wcs_index))

            if wcs_index == self.active_wcs_index:
                path_transform = vtk.vtkTransform()
                path_transform.Translate(*offset[:3])
                path_transform.RotateZ(offset[9])

                axes.SetUserTransform(path_transform)
                path_actor.SetUserTransform(path_transform)

            program_bounds_actor = ProgramBoundsActor(self.camera, path_actor)
            program_bounds_actor.showProgramBounds(self.show_program_bounds)

            self.renderer.AddActor(program_bounds_actor)

            self.program_bounds_actors[wcs_index] = program_bounds_actor

        self.interactor.ReInitialize()
        self.renderer_window.Render()

    def update_active_wcs(self, wcs_index):
        self.active_wcs_index = wcs_index
        LOG.debug("--------update_active_wcs index: {}".format(wcs_index))
        LOG.debug("--------self.wcs_offsets: {}".format(self.wcs_offsets))

        position = self.wcs_offsets[wcs_index]
        LOG.debug("--------position: {}".format(position))

        transform = vtk.vtkTransform()
        transform.Translate(*position[:3])
        transform.RotateZ(position[9])

        self.axes_actor.SetUserTransform(transform)

        self.interactor.ReInitialize()
        self.renderer_window.Render()

    def update_g92_offset(self, g92_offset):
        LOG.debug("---------update_g92_offset: {}".format(g92_offset))
        if self._datasource.isModeMdi() or self._datasource.isModeAuto():
            self.g92_offset = g92_offset

            path_offset = list(map(add, self.g92_offset, self.original_g92_offset))
            LOG.debug("---------path_offset: {}".format(path_offset))

            for wcs_index, actor in self.path_actors.items():

                old_program_bounds_actor = self.program_bounds_actors[wcs_index]
                self.renderer.RemoveActor(old_program_bounds_actor)
                # determine change in g92 offset since path was drawn

                new_path_position = list(map(add, self.wcs_offsets[wcs_index][:9], path_offset))
                LOG.debug("---------new_path_position: {}".format(path_offset))

                axes = actor.get_axes_actor()

                path_transform = vtk.vtkTransform()
                path_transform.Translate(*new_path_position[:3])

                self.axes_actor.SetUserTransform(path_transform)
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

        self.tool_actor = ToolActor(self._datasource)

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)
        tool_transform.RotateX(-self.spindle_rotation[0])
        tool_transform.RotateY(-self.spindle_rotation[1])
        tool_transform.RotateZ(-self.spindle_rotation[2])

        self.tool_actor.SetUserTransform(tool_transform)

        self.renderer.AddActor(self.tool_actor)

        self.renderer_window.Render()

    @Slot(bool)
    @Slot(object)
    def viewPerspective(self, persp):
        if persp:
            self.setViewPersp()
        else:
            self.setViewOrtho()

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

        self.camera.SetViewUp(0, 0, 1)
        self.__doCommonSetViewWork()

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
        print('position {}'.format(p))
        # dist = math.sqrt( (p[0]-fp[0])**2 + (p[1]-fp[1])**2 + (p[2]-fp[2])**2 )
        # print(dist)
        # self.camera.SetPosition(10, -40, -1)
        # self.setViewUp(0.0, 1.0, 0.0)
        # self.renderer.ResetCamera()
        vu = self.camera.GetViewUp()
        LOG.debug('view up {}'.format(vu))
        d = self.camera.GetDistance()
        print('distance {}'.format(d))
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
        for wcs_index, actor in self.path_actors.items():
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            if program_bounds_actor is not None:
                program_bounds_actor.showProgramBounds(self.show_program_bounds)
                self.renderer_window.Render()

    @Slot()
    def toggleProgramBounds(self):
        for wcs_index, actor in self.path_actors.items():
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            self.showProgramBounds(not program_bounds_actor.GetXAxisVisibility())

    @Slot(bool)
    @Slot(object)
    def showProgramTicks(self, ticks):
        for wcs_index, actor in self.path_actors.items():
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            if program_bounds_actor is not None:
                program_bounds_actor.showProgramTicks(ticks)
        self.renderer_window.Render()

    @Slot()
    def toggleProgramTicks(self):
        for wcs_index, actor in self.path_actors.items():
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            self.showProgramTicks(not program_bounds_actor.GetXAxisTickVisibility())

    @Slot(bool)
    @Slot(object)
    def showProgramLabels(self, labels):
        for wcs_index, actor in self.path_actors.items():
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            if program_bounds_actor is not None:
                program_bounds_actor.showProgramLabels(labels)
        self.renderer_window.Render()

    @Slot()
    def toggleProgramLabels(self):
        for wcs_index, actor in self.path_actors.items():
            program_bounds_actor = self.program_bounds_actors[wcs_index]
            self.showProgramLabels(not program_bounds_actor.GetXAxisLabelVisibility())

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

    @Property(QColor)
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self._background_color = color

        self.renderer.SetBackground(color.getRgbF()[:3])
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
