import vtk

from qtpy.QtWidgets import QWidget, QFrame, QVBoxLayout, QSizePolicy
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets import VCPWidget

from vtk_cannon import VTKCanon


STATUS = getPlugin('status')


class VTKWidget(QWidget, VCPWidget):

    def __init__(self, parent=None):
        super(VTKWidget, self).__init__(parent)

        self.vertical_layout = QVBoxLayout()
        self.vtkWidget = QtVTKRender(self)
        self.vertical_layout.addWidget(self.vtkWidget)

        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.grid = Grid()
        self.grid_actor = self.grid.get_actor()

        self.cube = Cube()
        self.cube_actor = self.cube.get_actor()

        # self.frustum = Frustum()
        # self.frustum_actor = self.frustum.get_actor()

        # Create source
        source = vtk.vtkConeSource()
        source.SetResolution(64)
        source.SetCenter(0, 0, 0.5)
        source.SetRadius(0.5)

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.renderer.AddActor(actor)
        self.renderer.SetBackground(0.1, 0.2, 0.4)

        self.renderer.AddActor(self.grid_actor)
        self.renderer.AddActor(self.cube_actor)
        # self.renderer.AddActor(self.frustum_actor)


        self.renderer.ResetCamera()

        self.setLayout(self.vertical_layout)

        self.interactor.Initialize()
        self.interactor.Start()

    def add_actor(self, actor):
        self.renderer.AddActor(actor)


class QtVTKRender(QVTKRenderWindowInteractor):
    def __init__(self, parent, **kw):
        QVTKRenderWindowInteractor.__init__(self, parent, **kw)

        self.gr = VTKCanon()

        self.parent = parent
        self.status = STATUS

        self.status.file_loaded.connect(self.load_program)

        self.line = None
        self._last_filename = None

    def load_program(self, fname=None):

        if fname is None:
            fname = self._last_filename
        else:
            self._last_filename = fname

        self.gr.load(fname)

        feed_lines = len(self.gr.canon.feed)
        print(feed_lines)
        line = PolyLine(feed_lines)

        for index, point in enumerate(self.gr.canon.feed):
            coords = point[1][:3]
            line.add_point(index, coords)

        line.draw_poly_line()
        actor = line.get_actor()
        actor.GetProperty().SetColor(1, 1, 1)  # (R,G,B)
        self.parent.add_actor(actor)

        # for item in self.gr.canon.traverse:
        #     line = VTKLineElement(8)
        #     line.poly_line(item[2][:3], item[1][:3])
        #     actor = line.get_actor()
        #     actor.GetProperty().SetColor(1, 0, 0)  # (R,G,B)
        #     self.parent.add_actor(actor)


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


class Cube:
    def __init__(self):
        cube = vtk.vtkCubeSource()

        # mapper
        cube_mapper = vtk.vtkPolyDataMapper()
        cube_mapper.SetInputConnection(cube.GetOutputPort())

        # actor
        self.cube_actor = vtk.vtkActor()
        self.cube_actor.SetMapper(cube_mapper)
        self.cube_actor.GetProperty().SetRepresentationToWireframe()

    def get_actor(self):
        return self.cube_actor


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
