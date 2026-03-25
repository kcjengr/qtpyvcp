import vtk.qt
from qtpyvcp.utilities import logger
from vtk.util.colors import cyan

LOG = logger.getLogger(__name__)

class PathCacheActor(vtk.vtkActor):
    def __init__(self, current_position):
        super(PathCacheActor, self).__init__()
        self.current_position = current_position
        self.index = 0
        self.num_points = 2
        self.first_sample_seeded = False

        self.points = vtk.vtkPoints()
        self.points.InsertNextPoint(current_position)

        self.lines = vtk.vtkCellArray()

        self.lines_poligon_data = vtk.vtkPolyData()
        self.polygon_mapper = vtk.vtkPolyDataMapper()
        self.GetProperty().SetColor(cyan)
        self.GetProperty().SetLineWidth(2.5)
        self.GetProperty().SetOpacity(0.5)
        self.SetMapper(self.polygon_mapper)
        
        self.lines_poligon_data.SetPoints(self.points)
        self.lines_poligon_data.SetLines(self.lines)

        self.polygon_mapper.SetInputData(self.lines_poligon_data)
        self.polygon_mapper.Update()

        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(1)

    def add_line_point(self, point):
        if not self.first_sample_seeded:
            # First live sample only seeds the breadcrumb origin to avoid a
            # synthetic startup segment from an unknown position.
            self.points.SetPoint(0, point)
            self.points.Modified()
            self.current_position = point
            self.first_sample_seeded = True
            self.index = 0
            return

        self.index += 1

        self.points.InsertNextPoint(point)
        self.points.Modified()

        self.lines.InsertNextCell(self.num_points)
        self.lines.InsertCellPoint(self.index - 1)
        self.lines.InsertCellPoint(self.index)
        self.lines.Modified()
