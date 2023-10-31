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

        x_actor = self.GetXAxisActor2D()
        y_actor = self.GetYAxisActor2D()
        z_actor = self.GetZAxisActor2D()
        
        x_actor.SetLabelFactor(8)
        y_actor.SetLabelFactor(8)
        z_actor.SetLabelFactor(8)
        
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
            self.XAxisTickVisibilityOn()
            self.YAxisTickVisibilityOn()
            self.ZAxisTickVisibilityOn()
        else:
            self.XAxisTickVisibilityOff()
            self.YAxisTickVisibilityOff()
            self.ZAxisTickVisibilityOff()

    def showMachineBounds(self, bounds):
        if bounds:
            self.XAxisVisibilityOn()
            self.YAxisVisibilityOn()
            self.ZAxisVisibilityOn()
        else:
            self.XAxisVisibilityOff()
            self.YAxisVisibilityOff()
            self.ZAxisVisibilityOff()


    def showMachineLabels(self, labels):
        if labels:
            self.XAxisLabelVisibilityOn()
            self.YAxisLabelVisibilityOn()
            self.ZAxisLabelVisibilityOn()
        else:
            self.XAxisLabelVisibilityOff()
            self.YAxisLabelVisibilityOff()
            self.ZAxisLabelVisibilityOff()

    def showGridlines(self, grid):
        if grid:
            self.DrawXGridlinesOn()
            self.DrawYGridlinesOn()
            self.DrawZGridlinesOn()
        else:
            self.DrawXGridlinesOff()
            self.DrawYGridlinesOff()
            self.DrawZGridlinesOff()