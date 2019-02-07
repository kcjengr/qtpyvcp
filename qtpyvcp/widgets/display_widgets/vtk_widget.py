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
        line = VTKLineElement(feed_lines)

        i = 0

        for index, point in enumerate(self.gr.canon.feed):
            coords = point[1][:3]
            line.add_point(index, coords)

            i += 1

        print(i)
        print("LOOL")

        line.draw_poly_line()

        print("LOOOOOL")

        actor = line.get_actor()
        actor.GetProperty().SetColor(1, 1, 1)  # (R,G,B)
        self.parent.add_actor(actor)

        print("LOOOOOOOOOOOOL")


        # for item in self.gr.canon.traverse:
        #     line = VTKLineElement(8)
        #     line.poly_line(item[2][:3], item[1][:3])
        #     actor = line.get_actor()
        #     actor.GetProperty().SetColor(1, 0, 0)  # (R,G,B)
        #     self.parent.add_actor(actor)


class VTKLineElement:
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

        self.lines.InsertNextCell(self.num_points + 2 )
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
