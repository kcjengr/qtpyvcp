import vtk

from qtpy.QtWidgets import QWidget, QVBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets import VCPWidget

from vtk_cannon import VTKCanon

STATUS = getPlugin('status')


class VTKWidget(QWidget, VCPWidget):

    def __init__(self, parent=None):
        super(VTKWidget, self).__init__(parent)

        self.parent = parent
        self.status = STATUS

        self.axis = self.status.stat.axis

        self.gr = VTKCanon()

        self.vertical_layout = QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor()
        self.vertical_layout.addWidget(self.vtkWidget)

        self.nav_style = vtk.vtkInteractorStyleTrackballCamera()

        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.vtkWidget.SetInteractorStyle(self.nav_style)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # self.coords_widget = CoordinateWidget(self.interactor)  # Todo is bugged

        # self.grid = Grid()
        # self.grid_actor = self.grid.get_actor()

        self.machine = Machine(self.renderer, self.axis)
        self.machine_actor = self.machine.get_actor()

        # self.axes = Axes()
        # self.axes_actor = self.axes.get_actor()

        self.tool = Tool()
        self.tool_actor = self.tool.get_actor()

        # self.frustum = Frustum()
        # self.frustum_actor = self.frustum.get_actor()

        self.renderer.SetBackground(0.36, 0.36, 0.36)

        self.renderer.AddActor(self.tool_actor)
        self.renderer.AddActor(self.machine_actor)

        # self.renderer.AddActor(self.grid_actor)
        # self.renderer.AddActor(self.axes_actor)
        # self.renderer.AddActor(self.frustum_actor)

        self.renderer.ResetCamera()

        self.setLayout(self.vertical_layout)

        self.interactor.Initialize()
        self.interactor.Start()

        self.status.file.notify(self.load_program)
        self.status.position.notify(self.move_tool)

        self.line = None
        self._last_filename = None

    def load_program(self, fname=None):

        if fname is None:
            fname = self._last_filename
        else:
            self._last_filename = fname

        self.gr.load(fname)

        path = Path(self.gr, self.renderer)
        path_actors = path.get_actors()

        for path_actor in path_actors:
            self.renderer.AddActor(path_actor)

    def move_tool(self, position):
        self.tool_actor.SetPosition(position[:3])
        self.update_render()

    def update_render(self):
        self.vtkWidget.GetRenderWindow().Render()


class Path:
    def __init__(self, gr, renderer):
        self.gr = gr

        feed_lines = len(self.gr.canon.feed)
        traverse_lines = len(self.gr.canon.traverse)
        line = PolyLine(feed_lines + traverse_lines)

        path = dict()

        for point in self.gr.canon.traverse:
            seq = point[0]
            cords = point[1][:3]

            path[seq] = cords

        for point in self.gr.canon.feed:
            seq = point[0]
            cords = point[1][:3]

            path[seq] = cords

        for index, cords in enumerate(path.items()):
            line.add_point(index, cords[1])

        line.draw_poly_line()

        self.feed_actor = line.get_actor()
        self.color = self.gr.colors["straight_feed"]
        self.feed_actor.GetProperty().SetColor(self.color)  # (R,G,B)

        self.path_boundaries = PathBoundaries(renderer, self.feed_actor)
        self.path_boundaries_actor = self.path_boundaries.get_actor()

        # for item in self.gr.canon.traverse:
        #     line = VTKLineElement(8)
        #     line.poly_line(item[2][:3], item[1][:3])
        #     actor = line.get_actor()
        #     actor.GetProperty().SetColor(1, 0, 0)  # (R,G,B)
        #     self.parent.add_actor(actor)

    def get_actors(self):
        return [self.feed_actor, self.path_boundaries_actor]


class PathBoundaries:
    def __init__(self, renderer, path_actor):

        self.actor = path_actor

        cube_axes_actor = vtk.vtkCubeAxesActor()

        cube_axes_actor.SetBounds(self.actor.GetBounds())

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

        # cube_axes_actor.XAxisMinorTickVisibilityOff()
        # cube_axes_actor.YAxisMinorTickVisibilityOff()
        # cube_axes_actor.ZAxisMinorTickVisibilityOff()

        cube_axes_actor.XAxisTickVisibilityOn()
        cube_axes_actor.YAxisTickVisibilityOn()
        cube_axes_actor.ZAxisTickVisibilityOn()

        self.actor = cube_axes_actor

    def get_actor(self):
        return self.actor


class PolyLine:
    def __init__(self, points):

        self.num_points = points

        self.points = vtk.vtkPoints()
        self.points.SetNumberOfPoints(self.num_points)

        self.lines = vtk.vtkCellArray()
        self.polygon = vtk.vtkPolyData()
        self.polygon_mapper = vtk.vtkPolyDataMapper()
        self.polygon_actor = vtk.vtkActor()

    def add_point(self, index, point):
        self.points.SetPoint(index, point)

    def draw_poly_line(self):

        self.lines.InsertNextCell(self.num_points + 2)
        self.lines.InsertCellPoint(0)

        for i in range(self.num_points):
            self.lines.InsertCellPoint(i)

        self.lines.InsertCellPoint(0)

        self.polygon.SetPoints(self.points)
        self.polygon.SetLines(self.lines)

        if vtk.VTK_MAJOR_VERSION <= 5:
            self.polygon_mapper.SetInputConnection(self.polygon.GetProducerPort())
        else:
            self.polygon_mapper.SetInputData(self.polygon)
            self.polygon_mapper.Update()

        self.polygon_actor.SetMapper(self.polygon_mapper)

    def get_actor(self):
        return self.polygon_actor


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
    def __init__(self, renderer, axis):
        cube_axes_actor = vtk.vtkCubeAxesActor()

        x_max = axis[0]["max_position_limit"]
        x_min = axis[0]["min_position_limit"]

        y_max = axis[1]["max_position_limit"]
        y_min = axis[1]["min_position_limit"]

        z_max = axis[2]["max_position_limit"]
        z_min = axis[2]["min_position_limit"]

        cube_axes_actor.SetBounds(x_min, x_max, y_min, y_max, z_min, z_max)

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

        # cube_axes_actor.XAxisMinorTickVisibilityOff()
        # cube_axes_actor.YAxisMinorTickVisibilityOff()
        # cube_axes_actor.ZAxisMinorTickVisibilityOff()

        cube_axes_actor.XAxisTickVisibilityOn()
        cube_axes_actor.YAxisTickVisibilityOn()
        cube_axes_actor.ZAxisTickVisibilityOn()

        # cube_axes_actor.SetXUnits("mm")  # Todo machine units here
        # cube_axes_actor.SetYUnits("mm")
        # cube_axes_actor.SetZUnits("mm")

        self.actor = cube_axes_actor

    def get_actor(self):
        return self.actor


class Axes:
    def __init__(self):
        transform = vtk.vtkTransform()
        transform.Translate(1.0, 0.0, 0.0)  # Z up

        # actor
        self.actor = vtk.vtkCubeAxesActor()
        self.actor.SetUserTransform(transform)

    def get_actor(self):
        return self.actor


class Frustum:
    def __init__(self):
        colors = vtk.vtkNamedColors()

        camera = vtk.vtkCamera()
        camera.SetClippingRange(0.1, 0.4)
        planesArray = [0] * 24

        camera.GetFrustumPlanes(1.0, planesArray)

        planes = vtk.vtkPlanes()
        planes.SetFrustumPlanes(planesArray)

        frustumSource = vtk.vtkFrustumSource()
        frustumSource.ShowLinesOff()
        frustumSource.SetPlanes(planes)

        shrink = vtk.vtkShrinkPolyData()
        shrink.SetInputConnection(frustumSource.GetOutputPort())
        shrink.SetShrinkFactor(.9)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(shrink.GetOutputPort())

        back = vtk.vtkProperty()
        back.SetColor(colors.GetColor3d("Tomato"))

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().EdgeVisibilityOn()
        self.actor.GetProperty().SetColor(colors.GetColor3d("Banana"))
        self.actor.SetBackfaceProperty(back)

    def get_actor(self):
        return self.actor


class Tool:
    def __init__(self):

        self.height = 1.0

        # Create source
        source = vtk.vtkConeSource()
        source.SetResolution(8)
        source.SetHeight(self.height)
        source.SetCenter(-self.height/2, 0, 0)
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
