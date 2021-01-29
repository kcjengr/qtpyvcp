import vtk.qt
from axes_actor import AxesActor
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

class PathActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource):
        super(PathActor, self).__init__()
        self._datasource = linuxcncDataSource

        self.origin_index = None
        self.origin_cords = None


        if self._datasource.isMachineMetric():
            self.length = 2.5
        else:
            self.length = 0.25

        self.axes_actor = AxesActor(self._datasource)

        if self._datasource.isMachineLathe():
            self.axes_actor.SetTotalLength(self.length, 0, self.length)
        else:
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

    def get_axes_actor(self):
        return self.axes_actor