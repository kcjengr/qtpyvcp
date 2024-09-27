import os
import numpy as np

from vtk import (
    vtkActor,
    vtkPoints,
    vtkPolyDataMapper,
    vtkPolyData,
    vtkDelaunay2D,
    vtkSmoothPolyDataFilter

)

# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingContextOpenGL2
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkChartsCore import (
    vtkChartXYZ,
    vtkPlotSurface
)
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import vtkFloatArray
from vtkmodules.vtkCommonDataModel import (
    vtkRectf,
    vtkTable,
    vtkVector2i
)
from vtkmodules.vtkRenderingContext2D import vtkContextMouseEvent
from vtkmodules.vtkViewsContext2D import vtkContextView

from qtpyvcp.utilities import logger

# from qtpyvcp.widgets.display_widgets.vtk_backplot.linuxcnc_datasource import LinuxCncDataSource
from qtpyvcp.utilities.settings import getSetting
from qtpyvcp.plugins import iterPlugins, getPlugin

LOG = logger.getLogger(__name__)


class PointsSurfaceActor(vtkActor):
    def __init__(self, datasource):
        super(PointsSurfaceActor, self).__init__()
        self.log = LOG
        self._datasource = datasource

        self.probe_results = [[0.0]]

        self.axis = self._datasource.getAxis()
        # show_surface = getSetting('backplot.show-points-surface')
        # self.showSurface(show_surface and show_surface.value)

        self.probe_results = [
            [0.000000, -0.000000, -0.380763, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [1.000000, 0.000000, 3.533403, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [2.000000, 0.000000, 4.215070, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [3.000000, 0.000000, 4.024237, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [3.000000, 1.000000, 4.510903, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [2.000000, 1.000000, 4.621737, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [1.000000, 1.000000, 4.764237, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [0.000000, 1.000000, 4.740070, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [0.000000, 2.000000, 4.830070, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [1.000000, 2.000000, 5.090903, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [2.000000, 2.000000, 4.716737, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [3.000000, 2.000000, 4.947570, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [000000, 3.000000, 4.980903, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [2.000000, 3.000000, 4.829237, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [1.000000, 3.000000, 5.010903, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000],
            [0.000000, 3.000000, 4.858403, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000]
        ]


    def showSurface(self, show_surface):

        if show_surface:
            self.log.info("SHOW POINTS SURFACE ")
            # Define the size of the grid (number of points in X and Y directions)

            # Define the size of the grid (number of points in X and Y directions)
            num_points_x = len(self.probe_results[0])
            num_points_y = len(self.probe_results)

            print(num_points_x, num_points_y)

            # Define the original range of X and Y coordinates
            original_x_range = np.linspace(0, 1, num_points_x)
            original_y_range = np.linspace(0, 1, num_points_y)

            # Define the new range of X and Y coordinates
            new_x_range = np.linspace(0.0, 10.0, num_points_x)
            new_y_range = np.linspace(0.0, -10.0, num_points_y)

            # Initialize the points array
            points_array = np.zeros((num_points_x * num_points_y, 3))

            # Generate the points with elevation and translated coordinates
            for i, x in enumerate(original_x_range):
                for j, y in enumerate(original_y_range):
                    # Calculate the Z-coordinate (elevation) using a simple function
                    z = self.probe_results[j][i]
                    # Translate the X and Y coordinates to the new range
                    new_x = new_x_range[i]
                    new_y = new_y_range[j]
                    points_array[i * num_points_y + j] = [new_x, new_y, z]

            # Print the points array
            print(points_array)

            # Create a vtkPoints object and add the points
            vtk_points = vtkPoints()
            for point in points_array:
                vtk_points.InsertNextPoint(point)

            # Create a vtkPolyData object and set the points
            polydata = vtkPolyData()
            polydata.SetPoints(vtk_points)

            # Create a vtkDelaunay2D filter to generate the mesh
            delaunay = vtkDelaunay2D()
            delaunay.SetInputData(polydata)
            delaunay.Update()

            # Smooth the mesh using vtkSmoothPolyDataFilter
            smooth_filter = vtkSmoothPolyDataFilter()
            smooth_filter.SetInputConnection(delaunay.GetOutputPort())
            smooth_filter.SetNumberOfIterations(50)  # Number of smoothing iterations
            smooth_filter.SetRelaxationFactor(0.1)  # Relaxation factor
            smooth_filter.FeatureEdgeSmoothingOff()
            smooth_filter.BoundarySmoothingOff()
            smooth_filter.Update()

            # Create a mapper and set the input connection
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(smooth_filter.GetOutputPort())

            self.SetMapper(mapper)
            self.GetProperty().SetPointSize(10)

        else:
            self.log.info("HIDE POINTS SURFACE ")

    # def run(self):
    #         self.view.GetInteractor().Start()