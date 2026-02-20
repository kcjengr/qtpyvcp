import os

import vtk.qt
from qtpyvcp.utilities.settings import getSetting

IN_DESIGNER = os.getenv('DESIGNER', False)


class ProgramBoundsActor(vtk.vtkCubeAxesActor2D):
    def __init__(self, camera, path_actor):
        super(ProgramBoundsActor, self).__init__()

        self.path_actor = path_actor

        self.SetCamera(camera)
        
        self.SetNumberOfLabels(3)
        
        x_min, x_max, y_min, y_max, z_min, z_max = self.path_actor.GetBounds()
        
        self.SetBounds(x_min, x_max, y_min, y_max, z_min, z_max)
        
        corner_offset = 0.0
        self.SetCornerOffset(corner_offset)
        
        self.SetUseRanges(1)
        
        self.SetRanges(0, x_max - x_min, 0, y_max - y_min, 0, z_max - z_min)

        self.SetLabelFormat("%6.3f")
        
        self.SetFlyModeToOuterEdges()
        
        self.SetScaling(False)
        self.SetShowActualBounds(1)
        
        x_actor = self.GetXAxisActor2D()
        y_actor = self.GetYAxisActor2D()
        z_actor = self.GetZAxisActor2D()
        
        x_actor.SetLabelFactor(5)
        y_actor.SetLabelFactor(5)
        z_actor.SetLabelFactor(5)

        label_properties = self.GetAxisLabelTextProperty()

        label_properties.SetOrientation(30)
        label_properties.SetLineOffset(5)
        
        self.SetAxisLabelTextProperty(label_properties)

        if not IN_DESIGNER:
            bounds = getSetting('backplot.show-program-bounds')
            self.showProgramBounds(bounds and bounds.value)

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
        self.showProgramBounds(not self.GetShowActualBounds())
