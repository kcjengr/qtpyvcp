import vtk.qt
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

class AxesActor(vtk.vtkAxesActor):
    def __init__(self, linuxcncDataSource):
        super(AxesActor, self).__init__()
        self._datasource = linuxcncDataSource
        self._axis_mask = self._datasource.getAxisMask()

        if  self._datasource.isMachineMetric():
            self.length = 1.5
        else:
            self.length = 0.375
            
        transform = vtk.vtkTransform()
        transform.Translate(0.0, 0.0, 0.0)  # Z up

        self.SetUserTransform(transform)

        self.AxisLabelsOff()
        self.SetShaftTypeToLine()
        self.SetTipTypeToCone()

        # Lathe modes
        if self._datasource.isMachineLathe():
            self.SetTotalLength(self.length, 0, self.length)
        else:
            self.SetTotalLength(self.length, self.length, self.length)