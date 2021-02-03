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

        for i in range(3):  # XYZ
            
            self.GetTitleTextProperty(i).SetColor(1.0, 0.0, 0.0)
            self.GetTitleTextProperty(i).SetOpacity(0.5)
            self.GetTitleTextProperty(i).SetBackgroundColor(0.0, 0.0, 0.0)
            self.GetTitleTextProperty(i).SetBackgroundOpacity(1.0)
            self.GetTitleTextProperty(i).SetFrame(True)
            self.GetTitleTextProperty(i).SetFrameWidth(1)
            self.GetTitleTextProperty(i).SetFrameColor(1, 1, 1)
            self.GetTitleTextProperty(i).SetFontFamilyAsString("Arial")
            self.GetTitleTextProperty(i).SetFontFile(None)
            self.GetTitleTextProperty(i).SetFontSize(14)
            self.GetTitleTextProperty(i).SetBold(False)
            self.GetTitleTextProperty(i).SetItalic(False)
            self.GetTitleTextProperty(i).SetShadow(True)
            self.GetTitleTextProperty(i).SetShadowOffset(1, -1)
            self.GetTitleTextProperty(i).SetJustification(1)
            self.GetTitleTextProperty(i).SetLineOffset(0)
            self.GetTitleTextProperty(i).SetLineSpacing(1.1)
            
            self.GetLabelTextProperty(i).SetColor(1.0, 0.0, 0.0)
            self.GetLabelTextProperty(i).SetOpacity(0.5)
            self.GetLabelTextProperty(i).SetBackgroundColor(0.0, 0.0, 0.0)
            self.GetLabelTextProperty(i).SetBackgroundOpacity(1.0)
            self.GetLabelTextProperty(i).SetFrame(True)
            self.GetLabelTextProperty(i).SetFrameWidth(1)
            self.GetLabelTextProperty(i).SetFrameColor(1, 1, 1)
            self.GetLabelTextProperty(i).SetFontFamilyAsString("Arial")
            self.GetLabelTextProperty(i).SetFontFile(None)
            self.GetLabelTextProperty(i).SetFontSize(14)
            self.GetLabelTextProperty(i).SetBold(False)
            self.GetLabelTextProperty(i).SetItalic(False)
            self.GetLabelTextProperty(i).SetShadow(True)
            self.GetLabelTextProperty(i).SetShadowOffset(1, -1)
            self.GetLabelTextProperty(i).SetJustification(1)
            self.GetLabelTextProperty(i).SetLineOffset(0)
            self.GetLabelTextProperty(i).SetLineSpacing(1.1)

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