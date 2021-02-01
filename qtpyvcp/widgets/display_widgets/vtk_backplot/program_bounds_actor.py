import os

import vtk.qt
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import getSetting

LOG = logger.getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)

class ProgramBoundsActor(vtk.vtkCubeAxesActor):
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

        self.SetBounds(self.path_actor.GetBounds())

        self.SetCamera(camera)

        self.SetXLabelFormat("%6.3f")
        self.SetYLabelFormat("%6.3f")
        self.SetZLabelFormat("%6.3f")

        self.SetFlyModeToStaticEdges()

        self.GetTitleTextProperty(0).SetColor(1.0, 0.0, 0.0)
        self.GetLabelTextProperty(0).SetColor(1.0, 0.0, 0.0)

        self.GetTitleTextProperty(1).SetColor(0.0, 1.0, 0.0)
        self.GetLabelTextProperty(1).SetColor(0.0, 1.0, 0.0)

        self.GetTitleTextProperty(2).SetColor(0.0, 0.0, 1.0)
        self.GetLabelTextProperty(2).SetColor(0.0, 0.0, 1.0)

        if not IN_DESIGNER:
            bounds = getSetting('backplot.show-program-bounds')
            self.showProgramBounds(bounds and bounds.value)

            ticks = getSetting('backplot.show-program-ticks')
            self.showProgramTicks(ticks and ticks.value)

            labels = getSetting('backplot.show-program-labels')
            self.showProgramLabels(labels and labels.value)

    def showProgramLabels(self, labels):
        if labels:
            self.XAxisLabelVisibilityOn()
            self.YAxisLabelVisibilityOn()
            self.ZAxisLabelVisibilityOn()
        else:
            self.XAxisLabelVisibilityOff()
            self.YAxisLabelVisibilityOff()
            self.ZAxisLabelVisibilityOff()

    def toggleProgramLabels(self):
        self.showProgramLabels(not self.GetXAxisLabelVisibility())

    def showProgramTicks(self, ticks):
        if ticks:
            self.XAxisTickVisibilityOn()
            self.YAxisTickVisibilityOn()
            self.ZAxisTickVisibilityOn()
        else:
            self.XAxisTickVisibilityOff()
            self.YAxisTickVisibilityOff()
            self.ZAxisTickVisibilityOff()

    def toggleProgramTicks(self):
        self.showProgramTicks(not self.GetXAxisTickVisibility())

    def showProgramBounds(self, bounds):
        if bounds:
            self.XAxisVisibilityOn()
            self.YAxisVisibilityOn()
            self.ZAxisVisibilityOn()
        else:
            self.XAxisVisibilityOff()
            self.YAxisVisibilityOff()
            self.ZAxisVisibilityOff()

    def toggleProgramBounds(self):
        self.showProgramBounds(not self.GetXAxisVisibility())