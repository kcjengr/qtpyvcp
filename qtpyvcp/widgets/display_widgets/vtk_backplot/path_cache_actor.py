import vtk.qt
from qtpyvcp.utilities import logger
from vtk.util.colors import yellow

LOG = logger.getLogger(__name__)

class PathCacheActor(vtk.vtkActor):
    def __init__(self, current_position):
        super(PathCacheActor, self).__init__()
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
        self.GetProperty().SetColor(yellow)
        self.GetProperty().SetLineWidth(2)
        self.GetProperty().SetOpacity(0.5)
        self.SetMapper(self.polygon_mapper)

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