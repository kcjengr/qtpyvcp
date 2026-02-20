import os
import numpy as np

from vtk import (
    vtkActor,
    vtkPoints,
    vtkPolyDataMapper,
    vtkPolyData,
    vtkDelaunay2D,
    vtkSmoothPolyDataFilter,
    vtkTransform
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
        self.mesh_z_offset = 0.0

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

            self.mesh_x_offset = getSetting("backplot.mesh-x-offset")
            self.mesh_y_offset = getSetting("backplot.mesh-y-offset")
            self.mesh_z_offset = getSetting("backplot.mesh-z-offset")

            # Define the size of the grid (number of points in X and Y directions)
            num_points_x = len(self.probe_results)
            num_points_y = len(self.probe_results[0])

            # Define the original range of X and Y coordinates
            x_range = np.linspace(0, 1, num_points_x)
            y_range = np.linspace(0, 1, num_points_y)

            # Initialize the points array
            points_array = np.zeros((num_points_x * num_points_y, 3))

            # Generate the points with elevation and translated coordinates
            for i, x in enumerate(x_range):
                for j, y in enumerate(y_range):
                    # Calculate the Z-coordinate (elevation) using a simple function
                    z = self.probe_results[i][j]
                    points_array[i * num_points_y + j] = [x_range[i], y_range[j], z]

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

            x_offset = self.mesh_x_offset.value
            y_offset = self.mesh_y_offset.value
            z_offset = self.mesh_z_offset.value

            mesh_transform = vtkTransform()
            mesh_transform.Translate(x_offset, y_offset, z_offset)

            # Smooth the mesh using vtkSmoothPolyDataFilter
            # smooth_filter = vtkSmoothPolyDataFilter()
            # smooth_filter.SetInputConnection(delaunay.GetOutputPort())
            # smooth_filter.SetNumberOfIterations(50)  # Number of smoothing iterations
            # smooth_filter.SetRelaxationFactor(0.1)  # Relaxation factor
            # smooth_filter.FeatureEdgeSmoothingOff()
            # smooth_filter.BoundarySmoothingOff()
            # smooth_filter.Update()

            # Create a mapper and set the input connection
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(delaunay.GetOutputPort())

            self.SetUserTransform(mesh_transform)
            self.SetMapper(mapper)
            self.GetProperty().SetPointSize(10)

        else:
            self.log.info("HIDE POINTS SURFACE ")

    # def run(self):
    #         self.view.GetInteractor().Start()