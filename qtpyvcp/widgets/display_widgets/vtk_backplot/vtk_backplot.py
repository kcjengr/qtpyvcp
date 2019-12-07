import os
import linuxcnc

from qtpy.QtCore import Property, Signal, Slot, QTimer
from qtpy.QtGui import QColor

import vtk
# https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1
import vtk.qt
vtk.qt.QVTKRWIBase = "QGLWidget"

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


class VTKCanon(StatCanon):
    def __init__(self, colors=COLOR_MAP, *args, **kwargs):
        super(VTKCanon, self).__init__(*args, **kwargs)

        self.status = STATUS
        self.units = MACHINE_UNITS

        self.path_colors = colors

        # Create a vtkUnsignedCharArray container and store the colors in it
        self.colors = vtk.vtkUnsignedCharArray()
        self.colors.SetNumberOfComponents(4)

        self.points = vtk.vtkPoints()
        self.lines = vtk.vtkCellArray()

        self.poly_data = vtk.vtkPolyData()
        self.data_mapper = vtk.vtkPolyDataMapper()
        self.path_actor = vtk.vtkActor()

        self.path_points = []
        self.append_path_point = self.path_points.append

    def add_path_point(self, line_type, start_point, end_point):
        if self.units == 2:
            point_list = list()
            for point in end_point:
                point *= 25.4
                point_list.append(point)

            self.append_path_point((line_type, point_list[:3]))

        else:
            self.append_path_point((line_type, end_point[:3]))

    def draw_lines(self):

        index = 0
        for line_type, end_point in self.path_points:
            # LOG.debug(line_type, end_point)
            self.points.InsertNextPoint(end_point[:3])
            self.colors.InsertNextTypedTuple(self.path_colors[line_type])

            line = vtk.vtkLine()
            if index == 0:
                line.GetPointIds().SetId(0, 0)
                line.GetPointIds().SetId(1, 1)
            else:
                line.GetPointIds().SetId(0, index - 1)
                line.GetPointIds().SetId(1, index)

            self.lines.InsertNextCell(line)

            index += 1

        # free up memory, lots of it for big files
        self.path_points = []

        self.poly_data.SetPoints(self.points)
        self.poly_data.SetLines(self.lines)

        self.poly_data.GetCellData().SetScalars(self.colors)

        self.data_mapper.SetInputData(self.poly_data)
        self.data_mapper.Update()

        self.path_actor.SetMapper(self.data_mapper)

    def get_actor(self):
        return self.path_actor


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

        self.g5x_offset = self.stat.g5x_offset
        self.g92_offset = self.stat.g92_offset
        self.rotation_offset = self.stat.rotation_xy

        self.original_g5x_offset = [0.0] * 9
        self.original_g92_offset = [0.0] * 9
        self.original_rotation_offset = 0.0

        self.spindle_position = (0.0, 0.0, 0.0)
        self.tooltip_position = (0.0, 0.0, 0.0)

        self.units = MACHINE_UNITS

        self.axis = self.stat.axis

        self.nav_style = vtk.vtkInteractorStyleTrackballCamera()

        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetActiveCamera(self.camera)
        self.GetRenderWindow().AddRenderer(self.renderer)
        self.SetInteractorStyle(self.nav_style)
        self.interactor = self.GetRenderWindow().GetInteractor()

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

        if not IN_DESIGNER:
            self.canon = self.canon_class()
            self.path_actor = self.canon.get_actor()

            self.path_actor.SetPosition(*self.g5x_offset[:3])
            self.extents = PathBoundaries(self.renderer, self.path_actor)
            self.extents_actor = self.extents.get_actor()

            self.renderer.AddActor(self.extents_actor)
            self.renderer.AddActor(self.path_actor)

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.machine_actor)
        self.renderer.AddActor(self.axes_actor)
        self.renderer.AddActor(self.path_cache_actor)

        self.renderer.ResetCamera()

        self.interactor.Initialize()
        self.interactor.Start()

        self.status.file.notify(self.load_program)
        self.status.position.notify(self.update_position)

        self.status.g5x_offset.notify(self.update_g5x_offset)
        self.status.g92_offset.notify(self.update_g92_offset)
        self.status.rotation_xy.notify(self.update_rotation_xy)

        self.status.tool_offset.notify(self.update_tool)
        self.status.tool_table.notify(self.update_tool)

        self.line = None
        self._last_filename = str()

    def tlo(self, tlo):
        LOG.debug(tlo)

    @Slot()
    def reload_program(self, *args, **kwargs):
        self.load_program(self._last_filename)

    def load_program(self, fname=None):

        self.renderer.RemoveActor(self.path_actor)
        self.renderer.RemoveActor(self.extents_actor)

        self.original_rotation_offset = self.stat.rotation_xy
        self.original_g5x_offset = self.stat.g5x_offset
        self.original_g92_offset = self.stat.g92_offset

        if fname:
            self.load(fname)

        if self.canon is None:
            return

        self.canon.draw_lines()

        self.axes_actor = self.axes.get_actor()
        self.path_actor = self.canon.get_actor()
        self.extents_actor = self.extents.get_actor()

        self.renderer.AddActor(self.axes_actor)
        self.renderer.AddActor(self.path_actor)
        self.renderer.AddActor(self.extents_actor)

        self.update_render()

    def update_position(self, pos):  # the tool movement
        self.spindle_position = pos[:3]

        tlo = self.status.tool_offset
        self.tooltip_position = [pos - tlo for pos, tlo in zip(pos[:3], tlo[:3])]

        self.tool_actor.SetPosition(self.spindle_position)
        self.path_cache.add_line_point(self.tooltip_position)
        self.update_render()

    def update_g5x_offset(self, g5x_offset):
        # LOG.info('g5x offset')
        # LOG.debug(self.status.state)
        # LOG.debug(self.status.interp_state)
        # LOG.debug(self.status.exec_state)
        # LOG.debug(self.status.task_mode)
        if str(self.status.task_mode) == "MDI":

            self.g5x_offset = g5x_offset
            # LOG.info('G5x Update Started')
            # determine change in g5x offset since path was drawn

            path_offset = [n - o for n, o in zip(g5x_offset[:3], self.original_g5x_offset[:3])]

            transform = vtk.vtkTransform()
            transform.Translate(*self.g5x_offset[:3])
            transform.RotateZ(self.rotation_offset)

            self.axes_actor.SetUserTransform(transform)
            self.path_actor.SetPosition(*path_offset)

            self.extents_actor.SetBounds(*self.path_actor.GetBounds())

            self.interactor.ReInitialize()
            self.update_render()

    def update_g92_offset(self, g92_offset):
        # LOG.info('g92 offset')
        if str(self.status.task_mode) == "MDI":

            self.g92_offset = g92_offset

            # LOG.info('G92 Update Started')
            # determine change in g92 offset since path was drawn

            path_offset = [n - o for n, o in zip(g92_offset[:3], self.original_g92_offset[:3])]

            transform = vtk.vtkTransform()
            transform.Translate(*self.g5x_offset[:3])
            transform.RotateZ(self.rotation_offset)

            self.axes_actor.SetUserTransform(transform)
            self.path_actor.SetPosition(*path_offset)
            self.extents_actor.SetBounds(*self.path_actor.GetBounds())

            self.interactor.ReInitialize()
            self.update_render()

    def update_rotation_xy(self, rotation):
        # LOG.info("Rotation: {}".format(rotation))  # in degrees
        # ToDo: use transform matrix to rotate existing path?
        # probably not worth it since rotation is not used much ...

        # LOG.info('rotate offset: {}'.format(rotation))
        if str(self.status.task_mode) == "MDI":

            self.rotation_offset = rotation

            # LOG.info('Rotation Update Started')

            transform = vtk.vtkTransform()
            transform.Translate(*self.g5x_offset[:3])
            transform.RotateZ(self.rotation_offset)

            self.axes_actor.SetUserTransform(transform)
            self.path_actor.SetUserTransform(transform)
            self.extents_actor.SetBounds(*self.path_actor.GetBounds())

            self.interactor.ReInitialize()
            self.update_render()

        # nasty hack so ensure the positions have updated before loading
        # QTimer.singleShot(10, self.reload_program)

    def update_tool(self):
        self.renderer.RemoveActor(self.tool_actor)

        self.tool = Tool(self.stat.tool_table[0], self.stat.tool_offset)
        self.tool_actor = self.tool.get_actor()

        self.tool_actor.SetPosition(self.spindle_position)

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
        self.renderer.GetActiveCamera().Zoom(1.5)
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
        self.extents_actor.SetCamera(self.renderer.GetActiveCamera())
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

    @Slot()
    def zoomIn(self):
        self.renderer.GetActiveCamera().Zoom(1.1)
        self.interactor.ReInitialize()

    @Slot()
    def zoomOut(self):
        self.renderer.GetActiveCamera().Zoom(0.9)
        self.interactor.ReInitialize()

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

    @Slot()
    def toggleProgramBounds(self):
        if self.extents_actor is not None:
            bounds = self.extents_actor.GetXAxisVisibility()
            if bounds:
                self.extents_actor.XAxisVisibilityOff()
                self.extents_actor.YAxisVisibilityOff()
                self.extents_actor.ZAxisVisibilityOff()
            else:
                self.extents_actor.XAxisVisibilityOn()
                self.extents_actor.YAxisVisibilityOn()
                self.extents_actor.ZAxisVisibilityOn()
            self.update_render()

    @Slot()
    def toggleProgramTicks(self):
        if self.extents_actor is not None:
            ticks = self.extents_actor.GetXAxisTickVisibility()
            if ticks:
                self.extents_actor.XAxisTickVisibilityOff()
                self.extents_actor.YAxisTickVisibilityOff()
                self.extents_actor.ZAxisTickVisibilityOff()
            else:
                self.extents_actor.XAxisTickVisibilityOn()
                self.extents_actor.YAxisTickVisibilityOn()
                self.extents_actor.ZAxisTickVisibilityOn()
            self.update_render()

    @Slot()
    def toggleProgramLabels(self):
        if self.extents_actor is not None:
            labels = self.extents_actor.GetXAxisLabelVisibility()
            if labels:
                self.extents_actor.XAxisLabelVisibilityOff()
                self.extents_actor.YAxisLabelVisibilityOff()
                self.extents_actor.ZAxisLabelVisibilityOff()
            else:
                self.extents_actor.XAxisLabelVisibilityOn()
                self.extents_actor.YAxisLabelVisibilityOn()
                self.extents_actor.ZAxisLabelVisibilityOn()
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
            source.SetCenter(-self.height / 4 + offset[2], -offset[1], -offset[0])
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
