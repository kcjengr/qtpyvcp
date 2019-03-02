from collections import defaultdict

import vtk, math

from qtpy.QtCore import Property, Signal, Slot
from qtpy.QtGui import QColor
from vtk.util.colors import tomato, yellow, mint

from qtpy.QtWidgets import QWidget, QVBoxLayout

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger

from vtk_cannon import VTKCanon

import os
import linuxcnc

LOG = logger.getLogger(__name__)
STATUS = getPlugin('status')
IN_DESIGNER = os.getenv('DESIGNER', False)

INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))


class VTKWidget(QVTKRenderWindowInteractor, VCPWidget):

    def __init__(self, parent=None):
        super(VTKWidget, self).__init__(parent)

        # properties
        self._background_color = QColor(0, 0, 0)

        self.current_position = (0.0, 0.0, 0.0)
        self.parent = parent
        self.status = STATUS

        self.axis = self.status.stat.axis

        self.gr = VTKCanon()

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

        self.path_cache = PathCache(self.current_position)
        self.path_cache_actor = self.path_cache.get_actor()

        self.tool = Tool()
        self.tool_actor = self.tool.get_actor()

        self.path_actors = list()

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.machine_actor)
        self.renderer.AddActor(self.axes_actor)
        self.renderer.AddActor(self.path_cache_actor)

        self.renderer.ResetCamera()

        self.interactor.Initialize()
        self.interactor.Start()

        self.status.file.notify(self.load_program)
        self.status.position.notify(self.move_tool)
        self.status.g5x_offset.notify(self.reload_program)
        self.status.g92_offset.notify(self.reload_program)
        self.status.tool_offset.notify(self.reload_program)

        self.line = None
        self._last_filename = str()

    @Slot()
    def reload_program(self, *args, **kwargs):
        self.load_program(self._last_filename)

    def load_program(self, fname=None):
        for path_actor in self.path_actors:
            self.renderer.RemoveActor(path_actor)

        if fname:
            self._last_filename = fname
        else:
            fname = self._last_filename

        self.gr.load(fname)

        path = Path(self.gr, self.renderer)
        self.path_actors = path.get_actors()

        for path_actor in self.path_actors:
            self.renderer.AddActor(path_actor)

        self.update_render()

    def move_tool(self, position):
        self.current_position = position[:3]
        self.tool_actor.SetPosition(position[:3])
        self.path_cache.add_line_point(position[:3])
        self.update_render()

    def update_render(self):
        self.GetRenderWindow().Render()

    @Slot()
    def setViewOrtho(self):
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewPersp(self):
        self.renderer.GetActiveCamera().ParallelProjectionOff()
        self.renderer.ResetCamera()
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
        self.renderer.GetActiveCamera().Zoom(2.5)
        self.interactor.ReInitialize()

    @Slot()
    def setViewY(self):
        self.renderer.GetActiveCamera().SetPosition(0, -1, 0)
        self.renderer.GetActiveCamera().SetViewUp(0, 0, 1)
        self.renderer.GetActiveCamera().SetFocalPoint(0,0,0)
        self.renderer.ResetCamera()
        # FIXME ugly hack
        self.renderer.GetActiveCamera().Zoom(2.0)
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
        print('print view stats')
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        print('focal point {}'.format(fp))
        p = self.renderer.GetActiveCamera().GetPosition()
        print('position {}'.format(p))
        #dist = math.sqrt( (p[0]-fp[0])**2 + (p[1]-fp[1])**2 + (p[2]-fp[2])**2 )
        #print(dist)
        #self.renderer.GetActiveCamera().SetPosition(10, -40, -1)
        #self.renderer.GetActiveCamera().SetViewUp(0.0, 1.0, 0.0)
        #self.renderer.ResetCamera()
        vu = self.renderer.GetActiveCamera().GetViewUp()
        print('view up {}'.format(vu))
        d = self.renderer.GetActiveCamera().GetDistance()
        print('distance {}'.format(d))
        #self.interactor.ReInitialize()

    @Slot()
    def setViewZ2(self):
        self.renderer.GetActiveCamera().SetPosition(0, 0, 1)
        self.renderer.GetActiveCamera().SetViewUp(1, 0, 0)
        self.renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewMachine(self):
        print('Machine')
        self.machine_actor.SetCamera(self.renderer.GetActiveCamera())
        self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def setViewPath(self):
        print('Path')
        self.path_actors[1].SetCamera(self.renderer.GetActiveCamera())
        self.renderer.ResetCamera()
        self.interactor.ReInitialize()

    @Slot()
    def clearLivePlot(self):

        LOG.debug('clear live plot')

        self.renderer.RemoveActor(self.path_cache_actor)

        self.path_cache = PathCache(self.current_position)
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
        print('alpha blend')

    @Slot(bool)
    def showGrid(self, grid):
        print('show grid')

    @Slot(bool)
    def programBounds(self, bounds):
        if bounds:
            self.path_actors[1].XAxisVisibilityOff()
            self.path_actors[1].YAxisVisibilityOff()
            self.path_actors[1].ZAxisVisibilityOff()
        else:
            self.path_actors[1].XAxisVisibilityOn()
            self.path_actors[1].YAxisVisibilityOn()
            self.path_actors[1].ZAxisVisibilityOn()
        self.update_render()

    @Slot(bool)
    def programTicks(self, bounds):
        if bounds:
            self.path_actors[1].XAxisTickVisibilityOn()
            self.path_actors[1].YAxisTickVisibilityOn()
            self.path_actors[1].ZAxisTickVisibilityOn()
            self.path_actors[1].XAxisMinorTickVisibilityOff()
            self.path_actors[1].YAxisMinorTickVisibilityOff()
            self.path_actors[1].ZAxisMinorTickVisibilityOff()
        else:
            self.path_actors[1].XAxisTickVisibilityOff()
            self.path_actors[1].YAxisTickVisibilityOff()
            self.path_actors[1].ZAxisTickVisibilityOff()
        self.update_render()

    @Slot(bool)
    def programLabels(self, bounds):
        if bounds:
            self.path_actors[1].XAxisLabelVisibilityOn()
            self.path_actors[1].YAxisLabelVisibilityOn()
            self.path_actors[1].ZAxisLabelVisibilityOn()
        else:
            self.path_actors[1].XAxisLabelVisibilityOff()
            self.path_actors[1].YAxisLabelVisibilityOff()
            self.path_actors[1].ZAxisLabelVisibilityOff()
        self.update_render()

    @Slot(bool)
    def machineBounds(self, bounds):
        if bounds:
            self.machine_actor.XAxisVisibilityOff()
            self.machine_actor.YAxisVisibilityOff()
            self.machine_actor.ZAxisVisibilityOff()
        else:
            self.machine_actor.XAxisVisibilityOn()
            self.machine_actor.YAxisVisibilityOn()
            self.machine_actor.ZAxisVisibilityOn()
        self.update_render()

    @Slot(bool)
    def machineTicks(self, bounds):
        if bounds:
            self.machine_actor.XAxisTickVisibilityOn()
            self.machine_actor.YAxisTickVisibilityOn()
            self.machine_actor.ZAxisTickVisibilityOn()
            self.machine_actor.XAxisMinorTickVisibilityOff()
            self.machine_actor.YAxisMinorTickVisibilityOff()
            self.machine_actor.ZAxisMinorTickVisibilityOff()
        else:
            self.machine_actor.XAxisTickVisibilityOff()
            self.machine_actor.YAxisTickVisibilityOff()
            self.machine_actor.ZAxisTickVisibilityOff()
        self.update_render()

    @Slot(bool)
    def machineLabels(self, bounds):
        if bounds:
            self.machine_actor.XAxisLabelVisibilityOn()
            self.machine_actor.YAxisLabelVisibilityOn()
            self.machine_actor.ZAxisLabelVisibilityOn()
        else:
            self.machine_actor.XAxisLabelVisibilityOff()
            self.machine_actor.YAxisLabelVisibilityOff()
            self.machine_actor.ZAxisLabelVisibilityOff()
        self.update_render()

    @Property(QColor)
    def backgroundColor(self):
        return self._background_color

    @backgroundColor.setter
    def backgroundColor(self, color):
        self._background_color = color
        self.renderer.SetBackground(color.getRgbF()[:3])
        self.update_render()


class Path:
    def __init__(self, gr, renderer):
        self.gr = gr

        feed_lines = len(self.gr.canon.feed)
        traverse_lines = len(self.gr.canon.traverse)
        arcfeed_lines = len(self.gr.canon.arcfeed)

        total_lines = feed_lines + traverse_lines + arcfeed_lines

        line = PathLine(total_lines)

        path = dict()

        for traverse in self.gr.canon.traverse:
            seq = traverse[0]
            line_type = "straight_feed"
            cords = traverse[1][:3]

            path[seq] = [cords, line_type]

        for feed in self.gr.canon.feed:
            seq = feed[0]
            line_type = "traverse"
            cords = feed[1][:3]

            path[seq] = [cords, line_type]

        arc_segments = defaultdict(list)

        for index, arc in enumerate(self.gr.canon.arcfeed):
            seq = arc[0]
            line_type = "arc_feed"
            cords = arc[1][:3]
            arc_segments[seq].append((seq, [cords, line_type]))

        for point_data in path.items():
            line.add_line_point(point_data)

        for line_no, arc in arc_segments.items():
            for segment in arc:
                line.add_line_point(segment)

        line.draw_path_line()

        self.path_actor = line.get_actor()

        self.path_boundaries = PathBoundaries(renderer, self.path_actor)
        self.path_boundaries_actor = self.path_boundaries.get_actor()

    def get_actors(self):
        return [self.path_actor, self.path_boundaries_actor]


class PathLine:
    def __init__(self, points):

        self.num_points = points

        self.points = vtk.vtkPoints()
        self.lines = vtk.vtkCellArray()

        self.line_type = list()

        self.lines_poligon_data = vtk.vtkPolyData()
        self.polygon_mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()

    def add_line_point(self, point):
        data = point[1][0]
        line_type = point[1][1]
        self.line_type.append(line_type)
        self.points.InsertNextPoint(data)

    def draw_path_line(self):
        namedColors = vtk.vtkNamedColors()

        # Create a vtkUnsignedCharArray container and store the colors in it
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)

        for index in range(0, self.num_points - 1):

            line_type = self.line_type[index]

            if line_type == "traverse" or line_type == "arc_feed":
                colors.InsertNextTypedTuple(namedColors.GetColor3ub("mint"))
            elif line_type == "straight_feed":
                colors.InsertNextTypedTuple(namedColors.GetColor3ub("tomato"))

            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, index)  # the second 0 is the index of the Origin in linesPolyData's points
            line.GetPointIds().SetId(1, index + 1)  # the second 1 is the index of P0 in linesPolyData's points
            self.lines.InsertNextCell(line)

        self.lines_poligon_data.SetPoints(self.points)
        self.lines_poligon_data.SetLines(self.lines)

        self.lines_poligon_data.GetCellData().SetScalars(colors)

        self.polygon_mapper.SetInputData(self.lines_poligon_data)
        self.polygon_mapper.Update()

        self.actor.SetMapper(self.polygon_mapper)

    def get_actor(self):
        return self.actor


class PathBoundaries:
    def __init__(self, renderer, path_actor):
        self.path_actor = path_actor

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

        cube_axes_actor.XAxisLabelVisibilityOff()
        cube_axes_actor.YAxisLabelVisibilityOff()
        cube_axes_actor.ZAxisLabelVisibilityOff()

        cube_axes_actor.XAxisTickVisibilityOff()
        cube_axes_actor.YAxisTickVisibilityOff()
        cube_axes_actor.ZAxisTickVisibilityOff()

        if not IN_DESIGNER:
            programBoundry = INIFILE.find("VTK", "PROGRAM_BOUNDRY") or ""
            if programBoundry.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisVisibilityOff()
                cube_axes_actor.YAxisVisibilityOff()
                cube_axes_actor.ZAxisVisibilityOff()

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

        cube_axes_actor.XAxisLabelVisibilityOff()
        cube_axes_actor.YAxisLabelVisibilityOff()
        cube_axes_actor.ZAxisLabelVisibilityOff()

        cube_axes_actor.XAxisTickVisibilityOff()
        cube_axes_actor.YAxisTickVisibilityOff()
        cube_axes_actor.ZAxisTickVisibilityOff()

        if not IN_DESIGNER:
            machineBoundry = INIFILE.find("VTK", "MACHINE_BOUNDRY") or ""
            if machineBoundry.lower() in ['false', 'off', 'no', '0']:
                cube_axes_actor.XAxisVisibilityOff()
                cube_axes_actor.YAxisVisibilityOff()
                cube_axes_actor.ZAxisVisibilityOff()

        units = str(self.status.program_units)

        cube_axes_actor.SetXUnits(units)
        cube_axes_actor.SetYUnits(units)
        cube_axes_actor.SetZUnits(units)

        self.actor = cube_axes_actor

    def get_actor(self):
        return self.actor


class Axes:
    def __init__(self):
        transform = vtk.vtkTransform()
        transform.Translate(0.0, 0.0, 0.0)  # Z up

        self.actor = vtk.vtkAxesActor()
        self.actor.SetUserTransform(transform)

        self.actor.AxisLabelsOff()
        self.actor.SetShaftType(vtk.vtkAxesActor.CYLINDER_SHAFT)

    def get_actor(self):
        return self.actor


class Tool:
    def __init__(self):
        self.height = 1.0

        # Create source
        source = vtk.vtkConeSource()
        source.SetResolution(128)
        source.SetHeight(self.height)
        source.SetCenter(-self.height / 2, 0, 0)
        source.SetRadius(0.5)

        transform = vtk.vtkTransform()
        transform.RotateWXYZ(90, 0, 1, 0)
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
