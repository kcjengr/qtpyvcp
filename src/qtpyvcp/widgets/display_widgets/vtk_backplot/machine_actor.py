from pprint import pprint

import vtk.qt
import math
from vtk.util.colors import *

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper

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
        self.GetLabelTextProperty(0).SetColor(1.0, 0.0, 0.0)

        self.GetTitleTextProperty(1).SetColor(0.0, 1.0, 0.0)
        self.GetLabelTextProperty(1).SetColor(0.0, 1.0, 0.0)

        self.GetTitleTextProperty(2).SetColor(0.0, 0.0, 1.0)
        self.GetLabelTextProperty(2).SetColor(0.0, 0.0, 1.0)

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



class MachinePartsASM(vtk.vtkAssembly):
    
    def __init__(self, parts):
        super(MachinePartsASM, self).__init__()
        
        self.parts = dict()
        pprint(parts)
        
        for data in parts:
            # print(f"KEY {id} VAL {data}")
            
            part_id = data.get("id")
            part_root = data.get("root")
            part_position = data.get("position")
            part_origin = data.get("origin")
            part_model = data.get("model")
            
            source = vtk.vtkSTLReader()
            source.SetFileName(part_model)
        
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(source.GetOutputPort())
            
            partActor = vtk.vtkActor()
            
            partActor.SetMapper(mapper)
            
            partActor.GetProperty().SetColor(1, 0, 1)
            partActor.GetProperty().SetDiffuseColor(0.9, 0.9, 0.9)
            partActor.GetProperty().SetDiffuse(.8)
            partActor.GetProperty().SetSpecular(.5)
            partActor.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
            partActor.GetProperty().SetSpecularPower(30.0)
            
            tmp_assembly = vtk.vtkAssembly()
            tmp_assembly.AddPart(partActor)
            tmp_assembly.SetPosition(part_position[0], part_position[1], part_position[2])
            tmp_assembly.SetOrigin(part_origin)
            
            
            self.parts[part_id] = tmp_assembly
            
            if part_root is None:
                LOG.info(f"Joint id {part_id} is ROOT part")
                
                self.AddPart(self.parts[part_id])
            else:
                LOG.info(f"Joint id {part_id} LINKED to Joint {part_root}")
                
                self.parts[part_root].AddPart(self.parts[part_id])
        
                  
        
    def get_parts(self):
        return self.parts
