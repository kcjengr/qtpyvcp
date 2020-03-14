import os

from operator import add
from collections import OrderedDict

import linuxcnc

from qtpy.QtCore import Property, Signal, Slot, QTimer
from qtpy.QtGui import QColor

import vtk

# Fix poligons not drawing correctly on some GPU
# https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1

import vtk.qt
vtk.qt.QVTKRWIBase = "QGLWidget"

# Fix end

from vtk.util.colors import tomato, yellow, mint
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.info import Info

from base_canon import StatCanon
from base_backplot import BaseBackPlot

INFO = Info()

LOG = logger.getLogger(__name__)
STATUS = getPlugin('status')
TOOLTABLE = getPlugin('tooltable')
OFFSETTABLE = getPlugin('offsettable')
IN_DESIGNER = os.getenv('DESIGNER', False)
INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
MACHINE_UNITS = 2 if INFO.getIsMachineMetric() else 1

COLOR_MAP = {
    'traverse': (188, 252, 201, 75),
    'arcfeed': (255, 255, 255, 128),
    'feed': (255, 255, 255, 128),
    'dwell': (100, 100, 100, 255),
    'user': (100, 100, 100, 255),
}


class PathActor(vtk.vtkActor):
    def __init__(self):
        super(PathActor, self).__init__()
        self.origin_index = None
        self.origin_cords = None
        self.units = MACHINE_UNITS

        if self.units == 2:
            self.length = 5.0
        else:
            self.length = 0.5

        self.axes = Axes()
        self.axes_actor = self.axes.get_actor()
        self.axes_actor.SetTotalLength(self.length, self.length, self.length)

        # Create a vtkUnsignedCharArray container and store the colors in it
        self.colors = vtk.vtkUnsignedCharArray()
        self.colors.SetNumberOfComponents(4)

        self.points = vtk.vtkPoints()
        self.lines = vtk.vtkCellArray()

        self.poly_data = vtk.vtkPolyData()
        self.data_mapper = vtk.vtkPolyDataMapper()

    def set_origin_index(self, index):
        self.origin_index = index

    def get_origin_index(self):
        return self.origin_index

    def set_orgin_coords(self, *cords):
        self.origin_cords = cords

    def get_origin_coords(self):
        return self.origin_cords

    def get_axes(self):
        return self.axes_actor


class VTKCanon(StatCanon):
    def __init__(self, colors=COLOR_MAP, *args, **kwargs):
        super(VTKCanon, self).__init__(*args, **kwargs)

        self.units = MACHINE_UNITS

        self.index_map = dict()

        self.index_map[1] = 540
        self.index_map[2] = 550
        self.index_map[3] = 560
        self.index_map[4] = 570
        self.index_map[5] = 580
        self.index_map[6] = 590
        self.index_map[7] = 591
        self.index_map[8] = 592
        self.index_map[9] = 593

        self.path_colors = colors
        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()

        origin = 540

        self.path_actors[origin] = PathActor()
        self.path_points[origin] = list()

        self.origin = origin
        self.previous_origin = origin

        self.ignore_next = False  # hacky way to ignore the second point next to a offset change

    def rotate_and_translate(self, x, y, z, a, b, c, u, v, w):
        # override function to handle it in vtk back plot
        return x, y, z, a, b, c, u, v, w

    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):

        origin = self.index_map[index]
        if origin not in self.path_actors.keys():
            self.path_actors[origin] = PathActor()
            self.path_points[origin] = list()

            self.previous_origin = self.origin
            self.origin = origin


    def add_path_point(self, line_type, start_point, end_point):

        if self.ignore_next is True:
            self.ignore_next = False
            return

        if self.previous_origin != self.origin:
            self.previous_origin = self.origin
            self.ignore_next = True
            return

        path_points = self.path_points.get(self.origin)

        if self.units == 2:
            start_point_list = list()
            for point in end_point:
                point *= 25.4
                start_point_list.append(point)

            end_point_list = list()
            for point in end_point:
                point *= 25.4
                end_point_list.append(point)

            line = list()
            line.append(start_point_list)
            line.append(end_point_list)

            path_points.append((line_type, line))

        else:
            line = list()
            line.append(start_point)
            line.append(end_point)

            path_points.append((line_type, line))

    def draw_lines(self):

        for origin, data in self.path_points.items():

            path_actor = self.path_actors.get(origin)

            index = 0

            end_point = None
            last_line_type = None

            for line_type, line_data in data:
                # LOG.debug(line_type, end_point)

                start_point = line_data[0]
                end_point = line_data[1]
                last_line_type = line_type

                path_actor.points.InsertNextPoint(start_point[:3])
                path_actor.colors.InsertNextTypedTuple(self.path_colors[line_type])

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, index)
                line.GetPointIds().SetId(1, index + 1)

                path_actor.lines.InsertNextCell(line)

                index += 1

            if end_point:
                path_actor.points.InsertNextPoint(end_point[:3])
                path_actor.colors.InsertNextTypedTuple(self.path_colors[last_line_type])

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, index - 1)
                line.GetPointIds().SetId(1, index)

                path_actor.lines.InsertNextCell(line)

            # free up memory, lots of it for big files

            self.path_points[self.origin] = list()

            path_actor.poly_data.SetPoints(path_actor.points)
            path_actor.poly_data.SetLines(path_actor.lines)
            path_actor.poly_data.GetCellData().SetScalars(path_actor.colors)
            path_actor.data_mapper.SetInputData(path_actor.poly_data)
            path_actor.data_mapper.Update()
            path_actor.SetMapper(path_actor.data_mapper)

    def get_path_actors(self):
        return self.path_actors


class VTKBackPlot(QVTKRenderWindowInteractor, VCPWidget, BaseBackPlot):
    def __init__(self, parent=None):
        super(VTKBackPlot, self).__init__(parent)

        self.parent = parent
        self.status = STATUS
        self.stat = STATUS.stat

        self.canon_class = VTKCanon

        # properties
        self._background_color = QColor(0, 0, 0)
        self._background_color2 = QColor(0, 0, 0)
        self._enableProgramTicks = True

        # Todo: get active part

        self.g5x_index = self.stat.g5x_index
        self.path_position_table = OFFSETTABLE.getOffsetTable()

        self.index_map = dict()
        self.index_map[1] = 540
        self.index_map[2] = 550
        self.index_map[3] = 560
        self.index_map[4] = 570
        self.index_map[5] = 580
        self.index_map[6] = 590
        self.index_map[7] = 591
        self.index_map[8] = 592
        self.index_map[9] = 593

        self.origin_map = dict()

        for k, v in self.index_map.items():
            self.origin_map[v] = k

        self.g5x_offset = self.stat.g5x_offset
        self.g92_offset = self.stat.g92_offset
        self.rotation_offset = self.stat.rotation_xy

        self.original_g5x_offset = [0.0] * 9
        self.original_g92_offset = [0.0] * 9
        self.original_rotation_offset = 0.0

        self.spindle_position = (0.0, 0.0, 0.0)
        self.spindle_rotation = (0.0, 0.0, 0.0)
        self.tooltip_position = (0.0, 0.0, 0.0)

        self.units = MACHINE_UNITS

        self.axis = self.stat.axis


        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetActiveCamera(self.camera)

        self.renderer_window = self.GetRenderWindow()
        self.renderer_window.AddRenderer(self.renderer)

        # self.nav_style = vtk.vtkInteractorStyleTrackballCamera()
        # self.SetInteractorStyle(self.nav_style)

        self.interactor = self.renderer_window.GetInteractor()
        self.interactor.SetInteractorStyle(None)
        self.interactor.SetRenderWindow(self.renderer_window)


        self.machine = Machine(self.axis)
        self.machine_actor = self.machine.get_actor()
        self.machine_actor.SetCamera(self.renderer.GetActiveCamera())

        self.axes = Axes()
        self.axes_actor = self.axes.get_actor()

        transform = vtk.vtkTransform()
        transform.Translate(*self.g5x_offset[:3])
        transform.RotateZ(self.rotation_offset)
        self.axes_actor.SetUserTransform(transform)

        self.path_cache = PathCache(self.tooltip_position)
        self.path_cache_actor = self.path_cache.get_actor()
        self.tool = Tool(self.stat.tool_table[0], self.stat.tool_offset)
        self.tool_actor = self.tool.get_actor()

        self.offset_axes = OrderedDict()
        self.extents = OrderedDict()
        self.show_extents = bool()

        if not IN_DESIGNER:
            self.canon = self.canon_class()
            self.path_actors = self.canon.get_path_actors()

            for origin, actor in self.path_actors.items():

                index = self.origin_map[origin]

                actor_position = self.path_position_table[index - 1]

                actor_transform = vtk.vtkTransform()
                actor_transform.Translate(*actor_position[:3])
                actor_transform.RotateWXYZ(*actor_position[5:9])

                actor.SetUserTransform(actor_transform)

                extents = PathBoundaries(self.renderer, actor)
                extents_actor = extents.get_actor()

                axes = actor.get_axes()

                self.offset_axes[origin] = axes
                self.extents[origin] = extents_actor

                self.renderer.AddActor(axes)
                self.renderer.AddActor(extents_actor)
                self.renderer.AddActor(actor)

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.machine_actor)
        self.renderer.AddActor(self.axes_actor)
        self.renderer.AddActor(self.path_cache_actor)

        self.renderer.ResetCamera()

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

        self.status.file.notify(self.load_program)
        self.status.position.notify(self.update_position)

        # self.status.g5x_index.notify(self.update_g95x_index)
        self.status.g5x_offset.notify(self.update_g95x_offset)
        self.status.g92_offset.notify(self.update_g92_offset)
        # self.status.rotation_xy.notify(self.update_rotation_xy)

        OFFSETTABLE.offset_table_changed.connect(self.on_offset_table_changed)
        OFFSETTABLE.active_offset_changed.connect(self.update_g95x_index)

        self.status.tool_offset.notify(self.update_tool)
        self.status.tool_table.notify(self.update_tool)

        self.line = None
        self._last_filename = str()

        # Add the observers to watch for particular events. These invoke
        # Python functions.
        self.rotating = 0
        self.panning = 0
        self.zooming = 0

        self.pan_mode = False

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
            self.rotate(self.renderer, self.renderer.GetActiveCamera(), x, y, lastX, lastY, centerX, centerY)
        elif self.panning:
            self.pan(self.renderer, self.renderer.GetActiveCamera(), x, y, lastX, lastY, centerX, centerY)
        elif self.zooming:
            self.dolly(self.renderer, self.renderer.GetActiveCamera(), x, y, lastX, lastY, centerX, centerY)

    def keypress(self, obj, event):
        key = obj.GetKeySym()
        if key == "w":
            self.wireframe()
        elif key == "s":
            self.surface()

    # Routines that translate the events into camera motions.

    # This one is associated with the left mouse button. It translates x
    # and y relative motions into camera azimuth and elevation commands.
    def rotate(self, renderer, camera, x, y, lastX, lastY, centerX, centerY):
        camera.Azimuth(lastX - x)
        camera.Elevation(lastY - y)
        camera.OrthogonalizeViewUp()
        self.renderer_window.Render()

    # Pan translates x-y motion into translation of the focal point and
    # position.
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

    # Wireframe sets the representation of all actors to wireframe.
    def wireframe(self):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        actor = actors.GetNextItem()
        while actor:
            actor.GetProperty().SetRepresentationToWireframe()
            actor = actors.GetNextItem()

        self.renderer_window.Render()

    # Surface sets the representation of all actors to surface.
    def surface(self):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        actor = actors.GetNextItem()
        while actor:
            actor.GetProperty().SetRepresentationToSurface()
            actor = actors.GetNextItem()
        self.renderer_window.Render()

    def tlo(self, tlo):
        LOG.debug(tlo)

    @Slot()
    def reload_program(self, *args, **kwargs):
        self.load_program(self._last_filename)

    def load_program(self, fname=None):

        for origin, actor in self.path_actors.items():
            axes = actor.get_axes()
            extents = self.extents[origin]

            self.renderer.RemoveActor(axes)
            self.renderer.RemoveActor(actor)
            self.renderer.RemoveActor(extents)

        self.path_actors.clear()
        self.offset_axes.clear()
        self.extents.clear()

        if fname:
            self.load(fname)

        if self.canon is None:
            return

        self.canon.draw_lines()

        self.axes_actor = self.axes.get_actor()
        self.path_actors = self.canon.get_path_actors()

        self.renderer.AddActor(self.axes_actor)

        for origin, actor in self.path_actors.items():

            axes = actor.get_axes()

            index = self.origin_map[origin]
            path_position = self.path_position_table[index - 1]

            path_transform = vtk.vtkTransform()
            path_transform.Translate(*path_position[:3])
            path_transform.RotateWXYZ(*path_position[5:9])

            axes.SetUserTransform(path_transform)
            actor.SetUserTransform(path_transform)

            extents = PathBoundaries(self.renderer, actor)
            extents_actor = extents.get_actor()

            if self.show_extents:
                extents_actor.XAxisVisibilityOn()
                extents_actor.YAxisVisibilityOn()
                extents_actor.ZAxisVisibilityOn()
            else:
                extents_actor.XAxisVisibilityOff()
                extents_actor.YAxisVisibilityOff()
                extents_actor.ZAxisVisibilityOff()

            self.renderer.AddActor(axes)
            self.renderer.AddActor(extents_actor)
            self.renderer.AddActor(actor)

            self.offset_axes[origin] = axes
            self.extents[origin] = extents_actor

        self.update_render()

    def update_position(self, position):  # the tool movement

        self.spindle_position = position[:3]
        self.spindle_rotation = position[3:6]

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)
        tool_transform.RotateX(-self.spindle_rotation[0])
        tool_transform.RotateY(-self.spindle_rotation[1])
        tool_transform.RotateZ(-self.spindle_rotation[2])

        self.tool_actor.SetUserTransform(tool_transform)

        tlo = self.status.tool_offset
        self.tooltip_position = [pos - tlo for pos, tlo in zip(self.spindle_position, tlo[:3])]

        # self.spindle_actor.SetPosition(self.spindle_position)
        # self.tool_actor.SetPosition(self.spindle_position)
        self.path_cache.add_line_point(self.tooltip_position)
        self.update_render()

    def on_offset_table_changed(self, table):
        self.path_position_table = table

    def update_g95x_offset(self, offset):

        transform = vtk.vtkTransform()
        transform.Translate(*offset[:3])
        transform.RotateWXYZ(*offset[5:9])

        self.axes_actor.SetUserTransform(transform)

        for origin, actor in self.path_actors.items():
            # path_offset = [n - o for n, o in zip(position[:3], self.original_g5x_offset[:3])]

            path_index = self.origin_map[origin]

            old_extents = self.extents[origin]
            self.renderer.RemoveActor(old_extents)

            axes = actor.get_axes()

            if path_index == self.g5x_index:

                path_transform = vtk.vtkTransform()
                path_transform.Translate(*offset[:3])
                path_transform.RotateWXYZ(*offset[5:9])

                axes.SetUserTransform(path_transform)
                actor.SetUserTransform(path_transform)

            extents = PathBoundaries(self.renderer, actor)
            extents_actor = extents.get_actor()

            if self.show_extents:
                extents_actor.XAxisVisibilityOn()
                extents_actor.YAxisVisibilityOn()
                extents_actor.ZAxisVisibilityOn()
            else:
                extents_actor.XAxisVisibilityOff()
                extents_actor.YAxisVisibilityOff()
                extents_actor.ZAxisVisibilityOff()
                
            self.renderer.AddActor(extents_actor)

            self.extents[origin] = extents_actor

        self.interactor.ReInitialize()
        self.update_render()

    def update_g95x_index(self, index):
        self.g5x_index = index
        position = self.path_position_table[index - 1]

        transform = vtk.vtkTransform()
        transform.Translate(*position[:3])
        transform.RotateWXYZ(*position[5:9])

        self.axes_actor.SetUserTransform(transform)

        self.interactor.ReInitialize()
        self.update_render()

    def update_g92_offset(self, g92_offset):

        if str(self.status.task_mode) == "MDI" or str(self.status.task_mode) == "Auto":

            self.g92_offset = g92_offset

            path_offset = list(map(add, self.g92_offset, self.original_g92_offset))

            for origin, actor in self.path_actors.items():
                # LOG.info('G92 Update Started')
                # determine change in g92 offset since path was drawn
                index = self.origin_map[origin] - 1

                new_path_position = list(map(add, self.path_position_table[index][:9], path_offset))

                axes = actor.get_axes()

                path_transform = vtk.vtkTransform()
                path_transform.Translate(*new_path_position[:3])

                self.axes_actor.SetUserTransform(path_transform)
                axes.SetUserTransform(path_transform)
                actor.SetUserTransform(path_transform)

                extents = PathBoundaries(self.renderer, actor)
                extents_actor = extents.get_actor()

                if self.show_extents:
                    extents_actor.XAxisVisibilityOn()
                    extents_actor.YAxisVisibilityOn()
                    extents_actor.ZAxisVisibilityOn()
                else:
                    extents_actor.XAxisVisibilityOff()
                    extents_actor.YAxisVisibilityOff()
                    extents_actor.ZAxisVisibilityOff()

                self.renderer.AddActor(extents_actor)

                self.extents[origin] = extents_actor

            self.interactor.ReInitialize()
            self.update_render()


    # def update_rotation_xy(self, rotation):
    #
    #     self.rotation_offset = rotation
    #
    #     # LOG.info("Rotation: {}".format(rotation))  # in degrees
    #     # ToDo: use transform matrix to rotate existing path?
    #     # probably not worth it since rotation is not used much ...
    #
    #     # LOG.info('rotate offset: {}'.format(rotation))
    #     if str(self.status.task_mode) == "MDI":
    #
    #         # LOG.info('Rotation Update Started')
    #
    #         transform = vtk.vtkTransform()
    #         transform.Translate(*self.g5x_offset[:3])
    #         transform.RotateZ(self.rotation_offset)
    #
    #         self.axes_actor.SetUserTransform(transform)
    #         self.path_actor.SetUserTransform(transform)
    #         self.extents_actor.SetBounds(*self.path_actor.GetBounds())
    #
    #         self.interactor.ReInitialize()
    #         self.update_render()
    #
    #     # nasty hack so ensure the positions have updated before loading
    #     # QTimer.singleShot(10, self.reload_program)

    def update_tool(self):
        self.renderer.RemoveActor(self.tool_actor)

        self.tool = Tool(self.stat.tool_table[0], self.stat.tool_offset)
        self.tool_actor = self.tool.get_actor()

        tool_transform = vtk.vtkTransform()
        tool_transform.Translate(*self.spindle_position)
        tool_transform.RotateX(-self.spindle_rotation[0])
        tool_transform.RotateY(-self.spindle_rotation[1])
        tool_transform.RotateZ(-self.spindle_rotation[2])

        self.tool_actor.SetUserTransform(tool_transform)

        self.renderer.AddActor(self.tool_actor)

        self.update_render()

    def update_render(self):
        self.GetRenderWindow().Render()

    @Slot()
    def setViewOrtho(self):
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        # self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewPersp(self):
        self.renderer.GetActiveCamera().ParallelProjectionOff()
        # self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewP(self):
        self.renderer.GetActiveCamera().SetPosition(1, -1, 1)
        self.renderer.GetActiveCamera().SetViewUp(0, 0, 1)
        self.renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.renderer.ResetCamera()
        self.renderer.GetActiveCamera().Zoom(1.1)
        self.interactor.ReInitialize()

    @Slot()
    def setViewX(self):
        self.renderer.GetActiveCamera().SetPosition(1, 0, 0)
        self.renderer.GetActiveCamera().SetViewUp(0, 0, 1)
        self.renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.renderer.ResetCamera()
        # FIXME ugly hack
        self.renderer.GetActiveCamera().Zoom(1.5)
        self.interactor.ReInitialize()

    @Slot()
    def setViewY(self):
        self.renderer.GetActiveCamera().SetPosition(0, -1, 0)
        self.renderer.GetActiveCamera().SetViewUp(0, 0, 1)
        self.renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.renderer.ResetCamera()
        # FIXME ugly hack
        self.renderer.GetActiveCamera().Zoom(1.5)
        self.interactor.ReInitialize()

    @Slot()
    def setViewZ(self):
        self.renderer.GetActiveCamera().SetPosition(0, 0, 1)
        self.renderer.GetActiveCamera().SetViewUp(0, 1, 0)
        self.renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.renderer.ResetCamera()
        # FIXME ugly hack
        self.renderer.GetActiveCamera().Zoom(2)
        self.interactor.ReInitialize()

    @Slot()
    def printView(self):
        LOG.debug('LOG.debug view stats')
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        LOG.debug('focal point {}'.format(fp))
        p = self.renderer.GetActiveCamera().GetPosition()
        print('position {}'.format(p))
        # dist = math.sqrt( (p[0]-fp[0])**2 + (p[1]-fp[1])**2 + (p[2]-fp[2])**2 )
        # print(dist)
        # self.renderer.GetActiveCamera().SetPosition(10, -40, -1)
        # self.renderer.GetActiveCamera().SetViewUp(0.0, 1.0, 0.0)
        # self.renderer.ResetCamera()
        vu = self.renderer.GetActiveCamera().GetViewUp()
        LOG.debug('view up {}'.format(vu))
        d = self.renderer.GetActiveCamera().GetDistance()
        print('distance {}'.format(d))
        # self.interactor.ReInitialize()

    @Slot()
    def setViewZ2(self):
        self.renderer.GetActiveCamera().SetPosition(0, 0, 1)
        self.renderer.GetActiveCamera().SetViewUp(1, 0, 0)
        self.renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewMachine(self):
        LOG.debug('Machine')
        self.machine_actor.SetCamera(self.renderer.GetActiveCamera())
        self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewPath(self):
        LOG.debug('Path')
        
        active_offset = self.index_map[self.g5x_index]
        self.extents[active_offset].SetCamera(self.renderer.GetActiveCamera())
        self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def clearLivePlot(self):
        LOG.debug('clear live plot')
        self.renderer.RemoveActor(self.path_cache_actor)
        self.path_cache = PathCache(self.tooltip_position)
        self.path_cache_actor = self.path_cache.get_actor()
        self.renderer.AddActor(self.path_cache_actor)
        self.update_render()

    @Slot(bool)
    def enable_panning(self, enabled):
        self.pan_mode = enabled

    @Slot()
    def zoomIn(self):

        camera = self.renderer.GetActiveCamera()
        if camera.GetParallelProjection():
            parallelScale = camera.GetParallelScale() * 0.9
            camera.SetParallelScale(parallelScale)
        else:
            self.renderer.ResetCameraClippingRange()
            camera.Zoom(0.9)

        self.renderer_window.Render()

    @Slot()
    def zoomOut(self):

        camera = self.renderer.GetActiveCamera()
        if camera.GetParallelProjection():
            parallelScale = camera.GetParallelScale() * 1.1
            camera.SetParallelScale(parallelScale)
        else:
            self.renderer.ResetCameraClippingRange()
            camera.Zoom(1.1)

        self.renderer_window.Render()


    @Slot(bool)
    def alphaBlend(self, alpha):
        LOG.debug('alpha blend')

    @Slot(bool)
    def showGrid(self, grid):
        LOG.debug('show grid')
        if grid:
            self.machine_actor.DrawXGridlinesOn()
            self.machine_actor.DrawYGridlinesOn()
            self.machine_actor.DrawZGridlinesOn()
        else:
            self.machine_actor.DrawXGridlinesOff()
            self.machine_actor.DrawYGridlinesOff()
            self.machine_actor.DrawZGridlinesOff()
        self.update_render()

    @Slot(bool)
    def toggleProgramBounds(self, show):
        self.show_extents = show
        for origin, actor in self.path_actors.items():
            extents_actor = self.extents[origin]
            if extents_actor is not None:
                if show:
                    extents_actor.XAxisVisibilityOn()
                    extents_actor.YAxisVisibilityOn()
                    extents_actor.ZAxisVisibilityOn()
                else:
                    extents_actor.XAxisVisibilityOff()
                    extents_actor.YAxisVisibilityOff()
                    extents_actor.ZAxisVisibilityOff()
                self.update_render()

    @Slot()
    def toggleProgramTicks(self):
        for origin, actor in self.path_actors.items():
            extents = self.extents[origin]
            if extents is not None:
                ticks = extents.GetXAxisTickVisibility()
                if ticks:
                    extents.XAxisTickVisibilityOff()
                    extents.YAxisTickVisibilityOff()
                    extents.ZAxisTickVisibilityOff()
                else:
                    extents.XAxisTickVisibilityOn()
                    extents.YAxisTickVisibilityOn()
                    extents.ZAxisTickVisibilityOn()
                self.update_render()

    @Slot()
    def toggleProgramLabels(self):
        for origin, actor in self.path_actors.items():
            extents = self.extents[origin]
            if extents is not None:
                labels = extents.GetXAxisLabelVisibility()
                if labels:
                    extents.XAxisLabelVisibilityOff()
                    extents.YAxisLabelVisibilityOff()
                    extents.ZAxisLabelVisibilityOff()
                else:
                    extents.XAxisLabelVisibilityOn()
                    extents.YAxisLabelVisibilityOn()
                    extents.ZAxisLabelVisibilityOn()
                self.update_render()

    @Slot()
    def toggleMachineBounds(self):
        bounds = self.machine_actor.GetXAxisVisibility()
        if bounds:
            self.machine_actor.XAxisVisibilityOff()
            self.machine_actor.YAxisVisibilityOff()
            self.machine_actor.ZAxisVisibilityOff()
        else:
            self.machine_actor.XAxisVisibilityOn()
            self.machine_actor.YAxisVisibilityOn()
            self.machine_actor.ZAxisVisibilityOn()
        self.update_render()

    @Slot()
    def toggleMachineTicks(self):
        ticks = self.machine_actor.GetXAxisTickVisibility()
        if ticks:
            self.machine_actor.XAxisTickVisibilityOff()
            self.machine_actor.YAxisTickVisibilityOff()
            self.machine_actor.ZAxisTickVisibilityOff()
        else:
            self.machine_actor.XAxisTickVisibilityOn()
            self.machine_actor.YAxisTickVisibilityOn()
            self.machine_actor.ZAxisTickVisibilityOn()
        self.update_render()

    @Slot()
    def toggleMachineLabels(self):
        labels = self.machine_actor.GetXAxisLabelVisibility()
        if labels:
            self.machine_actor.XAxisLabelVisibilityOff()
            self.machine_actor.YAxisLabelVisibilityOff()
            self.machine_actor.ZAxisLabelVisibilityOff()
        else:
            self.machine_actor.XAxisLabelVisibilityOn()
            self.machine_actor.YAxisLabelVisibilityOn()
            self.machine_actor.ZAxisLabelVisibilityOn()
        self.update_render()

    @Property(QColor)
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self._background_color = color

        self.renderer.SetBackground(color.getRgbF()[:3])
        self.update_render()

    @Property(QColor)
    def backgroundColor2(self):
        return self._background_color2

    @backgroundColor2.setter
    def backgroundColor2(self, color2):
        self._background_color2 = color2

        self.renderer.GradientBackgroundOn()
        self.renderer.SetBackground2(color2.getRgbF()[:3])
        self.update_render()

    @backgroundColor2.reset
    def backgroundColor2(self):
        self._background_color2 = QColor(0, 0, 0)

        self.renderer.GradientBackgroundOff()
        self.update_render()

    @Property(bool)
    def enableProgramTicks(self):
        return self._enableProgramTicks

    @enableProgramTicks.setter
    def enableProgramTicks(self, enable):
        self._enableProgramTicks = enable


class PathBoundaries:
    def __init__(self, renderer, path_actor):
        self.path_actor = path_actor

        """
        for k, v in VTKBackPlot.__dict__.items():
            if "function" in str(v):
                LOG.debug(k)

        for attr_name in dir(VTKBackPlot):
            attr_value = getattr(VTKBackPlot, attr_name)
            LOG.debug(attr_name, attr_value, callable(attr_value))

        LOG.debug(dir(VTKBackPlot))
        testit = getattr(VTKBackPlot, '_enableProgramTicks')
        LOG.debug('enableProgramTicks {}'.format(testit))
        """

        cube_axes_actor = vtk.vtkCubeAxesActor()

        cube_axes_actor.SetBounds(self.path_actor.GetBounds())

        cube_axes_actor.SetCamera(renderer.GetActiveCamera())

        cube_axes_actor.SetXLabelFormat("%6.3f")
        cube_axes_actor.SetYLabelFormat("%6.3f")
        cube_axes_actor.SetZLabelFormat("%6.3f")

        cube_axes_actor.SetFlyModeToStaticEdges()

        cube_axes_actor.GetTitleTextProperty(0).SetColor(1.0, 0.0, 0.0)
        cube_axes_actor.GetLabelTextProperty(0).SetColor(1.0, 0.0, 0.0)

        cube_axes_actor.GetTitleTextProperty(1).SetColor(0.0, 1.0, 0.0)
        cube_axes_actor.GetLabelTextProperty(1).SetColor(0.0, 1.0, 0.0)

        cube_axes_actor.GetTitleTextProperty(2).SetColor(0.0, 0.0, 1.0)
        cube_axes_actor.GetLabelTextProperty(2).SetColor(0.0, 0.0, 1.0)

        if not IN_DESIGNER:
            programBoundry = INIFILE.find("VTK", "PROGRAM_BOUNDRY") or ""
            if programBoundry.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisVisibilityOff()
                cube_axes_actor.YAxisVisibilityOff()
                cube_axes_actor.ZAxisVisibilityOff()
            programTicks = INIFILE.find("VTK", "PROGRAM_TICKS") or ""
            if programTicks.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisTickVisibilityOff()
                cube_axes_actor.YAxisTickVisibilityOff()
                cube_axes_actor.ZAxisTickVisibilityOff()
            programLabel = INIFILE.find("VTK", "PROGRAM_LABELS") or ""
            if programTicks.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisLabelVisibilityOff()
                cube_axes_actor.YAxisLabelVisibilityOff()
                cube_axes_actor.ZAxisLabelVisibilityOff()

        self.actor = cube_axes_actor

    def get_actor(self):
        return self.actor


class PathCache:
    def __init__(self, current_position):
        self.current_position = current_position
        self.index = 0
        self.num_points = 2

        self.points = vtk.vtkPoints()
        self.points.InsertNextPoint(current_position)

        self.lines = vtk.vtkCellArray()
        self.lines.InsertNextCell(1)  # number of points
        self.lines.InsertCellPoint(0)

        self.lines_poligon_data = vtk.vtkPolyData()
        self.polygon_mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()
        self.actor.GetProperty().SetColor(yellow)
        self.actor.GetProperty().SetLineWidth(2)
        self.actor.GetProperty().SetOpacity(0.5)
        self.actor.SetMapper(self.polygon_mapper)

        self.lines_poligon_data.SetPoints(self.points)
        self.lines_poligon_data.SetLines(self.lines)

        self.polygon_mapper.SetInputData(self.lines_poligon_data)
        self.polygon_mapper.Update()

    def add_line_point(self, point):
        self.index += 1

        self.points.InsertNextPoint(point)
        self.points.Modified()

        self.lines.InsertNextCell(self.num_points)
        self.lines.InsertCellPoint(self.index - 1)
        self.lines.InsertCellPoint(self.index)
        self.lines.Modified()

    def get_actor(self):
        return self.actor


class Grid:
    def __init__(self):
        x = [
            -1.22396, -1.17188, -1.11979, -1.06771, -1.01562, -0.963542,
            -0.911458, -0.859375, -0.807292, -0.755208, -0.703125, -0.651042,
            -0.598958, -0.546875, -0.494792, -0.442708, -0.390625, -0.338542,
            -0.286458, -0.234375, -0.182292, -0.130209, -0.078125, -0.026042,
            0.0260415, 0.078125, 0.130208, 0.182291, 0.234375, 0.286458,
            0.338542, 0.390625, 0.442708, 0.494792, 0.546875, 0.598958,
            0.651042, 0.703125, 0.755208, 0.807292, 0.859375, 0.911458,
            0.963542, 1.01562, 1.06771, 1.11979, 1.17188]

        y = [
            -1.25, -1.17188, -1.09375, -1.01562, -0.9375, -0.859375,
            -0.78125, -0.703125, -0.625, -0.546875, -0.46875, -0.390625,
            -0.3125, -0.234375, -0.15625, -0.078125, 0, 0.078125,
            0.15625, 0.234375, 0.3125, 0.390625, 0.46875, 0.546875,
            0.625, 0.703125, 0.78125, 0.859375, 0.9375, 1.01562,
            1.09375, 1.17188, 1.25]

        z = [
            0, 0.1, 0.2, 0.3, 0.4, 0.5,
            0.6, 0.7, 0.75, 0.8, 0.9, 1,
            1.1, 1.2, 1.3, 1.4, 1.5, 1.6,
            1.7, 1.75, 1.8, 1.9, 2, 2.1,
            2.2, 2.3, 2.4, 2.5, 2.6, 2.7,
            2.75, 2.8, 2.9, 3, 3.1, 3.2,
            3.3, 3.4, 3.5, 3.6, 3.7, 3.75,
            3.8, 3.9]

        # Create a rectilinear grid by defining three arrays specifying the
        # coordinates in the x-y-z directions.
        xCoords = vtk.vtkFloatArray()
        for i in x:
            xCoords.InsertNextValue(i)

        yCoords = vtk.vtkFloatArray()
        for i in y:
            yCoords.InsertNextValue(i)

        zCoords = vtk.vtkFloatArray()
        for i in z:
            zCoords.InsertNextValue(i)

        # The coordinates are assigned to the rectilinear grid. Make sure that
        # the number of values in each of the XCoordinates, YCoordinates,
        # and ZCoordinates is equal to what is defined in SetDimensions().
        #
        rgrid = vtk.vtkRectilinearGrid()
        rgrid.SetDimensions(len(x), len(y), len(z))
        rgrid.SetXCoordinates(xCoords)
        rgrid.SetYCoordinates(yCoords)
        rgrid.SetZCoordinates(zCoords)

        # Extract a plane from the grid to see what we've got.
        plane = vtk.vtkRectilinearGridGeometryFilter()
        plane.SetInputData(rgrid)
        plane.SetExtent(0, 46, 16, 16, 0, 43)

        rgridMapper = vtk.vtkPolyDataMapper()
        rgridMapper.SetInputConnection(plane.GetOutputPort())

        self.wire_actor = vtk.vtkActor()
        self.wire_actor.SetMapper(rgridMapper)
        self.wire_actor.GetProperty().SetRepresentationToWireframe()
        self.wire_actor.GetProperty().SetColor(0, 0, 0)

    def get_actor(self):
        return self.wire_actor


class Machine:
    def __init__(self, axis):
        self.status = STATUS

        cube_axes_actor = vtk.vtkCubeAxesActor()

        x_max = axis[0]["max_position_limit"]
        x_min = axis[0]["min_position_limit"]

        y_max = axis[1]["max_position_limit"]
        y_min = axis[1]["min_position_limit"]

        z_max = axis[2]["max_position_limit"]
        z_min = axis[2]["min_position_limit"]

        cube_axes_actor.SetBounds(x_min, x_max, y_min, y_max, z_min, z_max)

        cube_axes_actor.SetXLabelFormat("%6.3f")
        cube_axes_actor.SetYLabelFormat("%6.3f")
        cube_axes_actor.SetZLabelFormat("%6.3f")

        cube_axes_actor.SetFlyModeToStaticEdges()

        cube_axes_actor.GetTitleTextProperty(0).SetColor(1.0, 0.0, 0.0)
        cube_axes_actor.GetLabelTextProperty(0).SetColor(1.0, 0.0, 0.0)

        cube_axes_actor.GetTitleTextProperty(1).SetColor(0.0, 1.0, 0.0)
        cube_axes_actor.GetLabelTextProperty(1).SetColor(0.0, 1.0, 0.0)

        cube_axes_actor.GetTitleTextProperty(2).SetColor(0.0, 0.0, 1.0)
        cube_axes_actor.GetLabelTextProperty(2).SetColor(0.0, 0.0, 1.0)

        if not IN_DESIGNER:
            machineBoundry = INIFILE.find("VTK", "MACHINE_BOUNDRY") or ""
            if machineBoundry.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisVisibilityOff()
                cube_axes_actor.YAxisVisibilityOff()
                cube_axes_actor.ZAxisVisibilityOff()
            machineTicks = INIFILE.find("VTK", "MACHINE_TICKS") or ""
            if machineTicks.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisTickVisibilityOff()
                cube_axes_actor.YAxisTickVisibilityOff()
                cube_axes_actor.ZAxisTickVisibilityOff()
            machineLabels = INIFILE.find("VTK", "MACHINE_LABELS") or ""
            if machineLabels.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisLabelVisibilityOff()
                cube_axes_actor.YAxisLabelVisibilityOff()
                cube_axes_actor.ZAxisLabelVisibilityOff()

        units = str(self.status.program_units)

        cube_axes_actor.SetXUnits(units)
        cube_axes_actor.SetYUnits(units)
        cube_axes_actor.SetZUnits(units)

        cube_axes_actor.DrawXGridlinesOn()
        cube_axes_actor.DrawYGridlinesOn()
        cube_axes_actor.DrawZGridlinesOn()

        if not IN_DESIGNER:
            showGrid = INIFILE.find("VTK", "GRID_LINES") or ""
            if showGrid.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.DrawXGridlinesOff()
                cube_axes_actor.DrawYGridlinesOff()
                cube_axes_actor.DrawZGridlinesOff()

        cube_axes_actor.SetGridLineLocation(cube_axes_actor.VTK_GRID_LINES_FURTHEST)

        cube_axes_actor.GetXAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)
        cube_axes_actor.GetYAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)
        cube_axes_actor.GetZAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)

        self.actor = cube_axes_actor

    def get_actor(self):
        return self.actor


class Axes:
    def __init__(self):

        self.status = STATUS
        self.units = MACHINE_UNITS

        if self.units == 2:
            self.length = 10.0
        else:
            self.length = 1.0

        transform = vtk.vtkTransform()
        transform.Translate(0.0, 0.0, 0.0)  # Z up

        self.actor = vtk.vtkAxesActor()
        self.actor.SetUserTransform(transform)

        self.actor.AxisLabelsOff()
        self.actor.SetShaftType(vtk.vtkAxesActor.CYLINDER_SHAFT)

        self.actor.SetTotalLength(self.length, self.length, self.length)

    def get_actor(self):
        return self.actor


class Tool:
    def __init__(self, tool, offset):

        self.status = STATUS
        self.units = MACHINE_UNITS

        if self.units == 2:
            self.height = 25.4 * 2.0
        else:
            self.height = 2.0

        transform = vtk.vtkTransform()

        if tool.id == 0 or tool.diameter < .05:
            source = vtk.vtkConeSource()
            source.SetHeight(self.height / 2)
            source.SetCenter(-self.height / 4 - offset[2], -offset[1], -offset[0])
            source.SetRadius(self.height / 4)
            transform.RotateWXYZ(90, 0, 1, 0)
        else:
            source = vtk.vtkCylinderSource()
            source.SetHeight(self.height / 2)
            source.SetCenter(-offset[0], self.height / 4 - offset[2], offset[1])
            source.SetRadius(tool.diameter / 2)
            transform.RotateWXYZ(90, 1, 0, 0)

        source.SetResolution(128)

        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputConnection(source.GetOutputPort())
        transform_filter.Update()

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(transform_filter.GetOutputPort())

        # Create an actor
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)

    def get_actor(self):
        return self.actor


class CoordinateWidget:
    def __init__(self, interactor):
        colors = vtk.vtkNamedColors()

        axes = vtk.vtkAxesActor()

        widget = vtk.vtkOrientationMarkerWidget()
        rgba = [0] * 4
        colors.GetColor("Carrot", rgba)
        widget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(interactor)
        widget.SetViewport(0.0, 0.0, 0.4, 0.4)
        widget.SetEnabled(1)
        widget.InteractiveOn()
