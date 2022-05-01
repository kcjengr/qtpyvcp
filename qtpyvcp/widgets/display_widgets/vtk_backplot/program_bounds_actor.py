import os

import vtk.qt
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import getSetting

LOG = logger.getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)


class ProgramBoundsActor(vtk.vtkCubeAxesActor2D):
    def __init__(self, camera, path_actor):
        super(ProgramBoundsActor, self).__init__()

        self.path_actor = path_actor

        """
        for k, v in VTKBackPlot.__dict__.items():
            if "function" in str(v):
                LOG.debug(k)

        for attr_name in dir(VTKBackPlot):
            attr_value = getattr(VTKBackPlot, attr_name)
            LOG.debug(attr_name, attr_value, callable(attr_value))
        
        LOG.debug(dir(VTKBackPlot))
        testit = getattr(VTKBackPlot, '_enableProgramTicks')
        LOG.debug('enableProgramTicks {}'.format(testit))
        """
        
        self.SetCamera(camera)
        self.SetNumberOfLabels(3)
        
        x_min, x_max, y_min, y_max, z_min, z_max = self.path_actor.GetBounds()
        
        self.SetBounds(x_min, x_max, y_min, y_max, z_min, z_max)
        self.SetUseRanges(1)
        self.SetRanges(0, x_max - x_min, 0, y_max - y_min, 0, z_max - z_min)

        self.SetLabelFormat("%6.3f mm")
        self.SetFlyModeToOuterEdges()

        if not IN_DESIGNER:
            bounds = getSetting('backplot.show-program-bounds')
            self.showProgramBounds(bounds and bounds.value)

    def showProgramBounds(self, bounds):
        if bounds:
            self.SetShowActualBounds(True)
        else:
            self.SetShowActualBounds(False)

    def toggleProgramBounds(self):
        self.showProgramBounds(not self.GetShowActualBounds())

