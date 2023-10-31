import os

import vtk.qt
from qtpyvcp.utilities import logger

from qtpyvcp.utilities.settings import getSetting

LOG = logger.getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)


class MachineActor(vtk.vtkCubeAxesActor2D):
    def __init__(self, linuxcncDataSource):
        super(MachineActor, self).__init__()
        
        self._datasource = linuxcncDataSource
        
        axis = self._datasource.getAxis()
        units = self._datasource.getProgramUnits()

        x_max = axis[0]["max_position_limit"]
        x_min = axis[0]["min_position_limit"]

        y_max = axis[1]["max_position_limit"]
        y_min = axis[1]["min_position_limit"]

        z_max = axis[2]["max_position_limit"]
        z_min = axis[2]["min_position_limit"]

        self.SetBounds(x_min, x_max, y_min, y_max, z_min, z_max)


        self.SetLabelFormat("%6.3f")
        
        self.SetFlyModeToOuterEdges()
        
        label_properties = self.GetAxisLabelTextProperty()
        label_properties.SetOrientation(30)
        label_properties.SetLineOffset(5)
        
        self.SetAxisLabelTextProperty(label_properties)
        
        if not IN_DESIGNER:
            bounds = getSetting('backplot.show-machine-bounds')
            self.showMachineBounds(bounds and bounds.value)
                                   
    def showMachineTicks(self, ticks):
        if ticks:
            self.AxisTickVisibilityOn()
        else:
            self.AxisTickVisibilityOff()

    def showMachineBounds(self, bounds):
        if bounds:
            self.AxisVisibilityOn()
        else:
            self.AxisVisibilityOff()

    def showMachineLabels(self, labels):
        if labels:
            self.AxisLabelVisibilityOn()
        else:
            self.AxisLabelVisibilityOff()

    def showGridlines(self, grid):
        if grid:
            self.DrawGridlinesOn()
        else:
            self.DrawGridlinesOff()
            