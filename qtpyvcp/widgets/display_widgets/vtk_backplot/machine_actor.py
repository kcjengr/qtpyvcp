import vtk.qt
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

class MachineActor(vtk.vtkCubeAxesActor):
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

        self.SetXLabelFormat("%6.3f")
        self.SetYLabelFormat("%6.3f")
        self.SetZLabelFormat("%6.3f")

        self.SetFlyModeToStaticEdges()

        self.GetTitleTextProperty(0).SetColor(1.0, 0.0, 0.0)
        self.GetTitleTextProperty(0).SetOpacity(0.5)
        self.GetTitleTextProperty(0).SetBackgroundColor(0.0, 0.0, 0.0)
        self.GetTitleTextProperty(0).SetBackgroundOpacity(1.0)
        self.GetTitleTextProperty(0).SetFrame(True)
        self.GetTitleTextProperty(0).SetFrameWidth(1)
        self.GetTitleTextProperty(0).SetFrameColor(1, 1, 1)
        self.GetTitleTextProperty(0).SetFontFamilyAsString("Arial")
        self.GetTitleTextProperty(0).SetFontFile(None)
        self.GetTitleTextProperty(0).SetFontSize(14)
        self.GetTitleTextProperty(0).SetBold(False)
        self.GetTitleTextProperty(0).SetItalic(False)
        self.GetTitleTextProperty(0).SetShadow(True)
        self.GetTitleTextProperty(0).SetShadowOffset(1, -1)
        self.GetTitleTextProperty(0).SetJustification(1)
        self.GetTitleTextProperty(0).SetLineOffset(0)
        self.GetTitleTextProperty(0).SetLineSpacing(1.1)
        
        self.GetLabelTextProperty(0).SetColor(1.0, 0.0, 0.0)
        self.GetLabelTextProperty(0).SetOpacity(0.5)
        self.GetLabelTextProperty(0).SetBackgroundColor(0.0, 0.0, 0.0)
        self.GetLabelTextProperty(0).SetBackgroundOpacity(1.0)
        self.GetLabelTextProperty(0).SetFrame(True)
        self.GetLabelTextProperty(0).SetFrameWidth(1)
        self.GetLabelTextProperty(0).SetFrameColor(1, 1, 1)
        self.GetLabelTextProperty(0).SetFontFamilyAsString("Arial")
        self.GetLabelTextProperty(0).SetFontFile(None)
        self.GetLabelTextProperty(0).SetFontSize(14)
        self.GetLabelTextProperty(0).SetBold(False)
        self.GetLabelTextProperty(0).SetItalic(False)
        self.GetLabelTextProperty(0).SetShadow(True)
        self.GetLabelTextProperty(0).SetShadowOffset(1, -1)
        self.GetLabelTextProperty(0).SetJustification(1)
        self.GetLabelTextProperty(0).SetLineOffset(0)
        self.GetLabelTextProperty(0).SetLineSpacing(1.1)

        self.GetTitleTextProperty(1).SetColor(1.0, 0.0, 0.0)
        self.GetTitleTextProperty(1).SetOpacity(0.5)
        self.GetTitleTextProperty(1).SetBackgroundColor(0.0, 0.0, 0.0)
        self.GetTitleTextProperty(1).SetBackgroundOpacity(1.0)
        self.GetTitleTextProperty(1).SetFrame(True)
        self.GetTitleTextProperty(1).SetFrameWidth(1)
        self.GetTitleTextProperty(1).SetFrameColor(1, 1, 1)
        self.GetTitleTextProperty(1).SetFontFamilyAsString("Arial")
        self.GetTitleTextProperty(1).SetFontFile(None)
        self.GetTitleTextProperty(1).SetFontSize(14)
        self.GetTitleTextProperty(1).SetBold(False)
        self.GetTitleTextProperty(1).SetItalic(False)
        self.GetTitleTextProperty(1).SetShadow(True)
        self.GetTitleTextProperty(1).SetShadowOffset(1, -1)
        self.GetTitleTextProperty(1).SetJustification(1)
        self.GetTitleTextProperty(1).SetLineOffset(0)
        self.GetTitleTextProperty(1).SetLineSpacing(1.1)
        
        self.GetLabelTextProperty(1).SetColor(1.0, 0.0, 0.0)
        self.GetLabelTextProperty(1).SetOpacity(0.5)
        self.GetLabelTextProperty(1).SetBackgroundColor(0.0, 0.0, 0.0)
        self.GetLabelTextProperty(1).SetBackgroundOpacity(1.0)
        self.GetLabelTextProperty(1).SetFrame(True)
        self.GetLabelTextProperty(1).SetFrameWidth(1)
        self.GetLabelTextProperty(1).SetFrameColor(1, 1, 1)
        self.GetLabelTextProperty(1).SetFontFamilyAsString("Arial")
        self.GetLabelTextProperty(1).SetFontFile(None)
        self.GetLabelTextProperty(1).SetFontSize(14)
        self.GetLabelTextProperty(1).SetBold(False)
        self.GetLabelTextProperty(1).SetItalic(False)
        self.GetLabelTextProperty(1).SetShadow(True)
        self.GetLabelTextProperty(1).SetShadowOffset(1, -1)
        self.GetLabelTextProperty(1).SetJustification(1)
        self.GetLabelTextProperty(1).SetLineOffset(0)
        self.GetLabelTextProperty(1).SetLineSpacing(1.1)
        
        self.GetTitleTextProperty(2).SetColor(1.0, 0.0, 0.0)
        self.GetTitleTextProperty(2).SetOpacity(0.5)
        self.GetTitleTextProperty(2).SetBackgroundColor(0.0, 0.0, 0.0)
        self.GetTitleTextProperty(2).SetBackgroundOpacity(1.0)
        self.GetTitleTextProperty(2).SetFrame(True)
        self.GetTitleTextProperty(2).SetFrameWidth(1)
        self.GetTitleTextProperty(2).SetFrameColor(1, 1, 1)
        self.GetTitleTextProperty(2).SetFontFamilyAsString("Arial")
        self.GetTitleTextProperty(2).SetFontFile(None)
        self.GetTitleTextProperty(2).SetFontSize(14)
        self.GetTitleTextProperty(2).SetBold(False)
        self.GetTitleTextProperty(2).SetItalic(False)
        self.GetTitleTextProperty(2).SetShadow(True)
        self.GetTitleTextProperty(2).SetShadowOffset(1, -1)
        self.GetTitleTextProperty(2).SetJustification(1)
        self.GetTitleTextProperty(2).SetLineOffset(0)
        self.GetTitleTextProperty(2).SetLineSpacing(1.1)
        
        self.GetLabelTextProperty(2).SetColor(1.0, 0.0, 0.0)
        self.GetLabelTextProperty(2).SetOpacity(0.5)
        self.GetLabelTextProperty(2).SetBackgroundColor(0.0, 0.0, 0.0)
        self.GetLabelTextProperty(2).SetBackgroundOpacity(1.0)
        self.GetLabelTextProperty(2).SetFrame(True)
        self.GetLabelTextProperty(2).SetFrameWidth(1)
        self.GetLabelTextProperty(2).SetFrameColor(1, 1, 1)
        self.GetLabelTextProperty(2).SetFontFamilyAsString("Arial")
        self.GetLabelTextProperty(2).SetFontFile(None)
        self.GetLabelTextProperty(2).SetFontSize(14)
        self.GetLabelTextProperty(2).SetBold(False)
        self.GetLabelTextProperty(2).SetItalic(False)
        self.GetLabelTextProperty(2).SetShadow(True)
        self.GetLabelTextProperty(2).SetShadowOffset(1, -1)
        self.GetLabelTextProperty(2).SetJustification(1)
        self.GetLabelTextProperty(2).SetLineOffset(0)
        self.GetLabelTextProperty(2).SetLineSpacing(1.1)

        # self.GetTitleTextProperty(0).SetColor(0.0, 1.0, 0.0)
        # self.GetLabelTextProperty(0).SetColor(0.0, 1.0, 0.0)

        # self.GetTitleTextProperty(1).SetColor(0.0, 1.0, 0.0)
        # self.GetLabelTextProperty(1).SetColor(0.0, 1.0, 0.0)

        # self.GetTitleTextProperty(2).SetColor(0.0, 0.0, 1.0)
        # self.GetLabelTextProperty(2).SetColor(0.0, 0.0, 1.0)
                

        self.SetXUnits(units)
        self.SetYUnits(units)
        self.SetZUnits(units)

        self.DrawXGridlinesOn()
        self.DrawYGridlinesOn()
        self.DrawZGridlinesOn()

        self.SetGridLineLocation(self.VTK_GRID_LINES_FURTHEST)

        self.GetXAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)
        self.GetYAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)
        self.GetZAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)

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