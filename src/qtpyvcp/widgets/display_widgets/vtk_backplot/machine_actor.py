
import math

from pprint import pprint
from _collections import defaultdict

import vtk.qt
from vtk.util.colors import *

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper

from qtpyvcp.utilities import logger
from pyqtgraph.examples.colorMapsLinearized import previous

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


class MachinePart(vtk.vtkActor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.part_axis = None
        self.part_type = None
    def SetPartAxis(self, attr):
        self.part_axis = attr
        
    def SetPartType(self, attr):
        self.part_type = attr

    def GetPartAxis(self):
        return self.part_axis
    
    def GetPartType(self):
        return self.part_type


class MachinePartsASM(vtk.vtkAssembly):
    
    def __init__(self, parts):
        super(MachinePartsASM, self).__init__()
        
        # self.parts = dict()
        #
        # machine_parts = dict()

        # pprint(parts)
       
        # root_id = parts.get("id")
        # root_model = parts.get("model")
        # root_position = parts.get("position")
        # root_origin = parts.get("origin")
        # root_type = parts.get("type")
        # root_child = parts.get("child")
        #
        #
        #
        # print(root_id)
        # print(root_model)
        # print(root_position)
        # print(root_origin)
        # print(root_type)
        # print(root_child)
        #
        # print("######")
        #
        # machine_parts = dict()
        
        print("########")
        
        # part_transform = vtk.vtkTransform()
        
        # part_transform.Translate(part_position[0], part_position[1], part_position[2])
         
        # machine_assembly = vtk.vtkAssembly()
        #
        # tmp_assembly.AddPart(partActor)
    
    
        path = vtk.vtkAssemblyPath()
        
        previous_part = None
        for part_root, part_data in self.items_recursive(parts):
            
            print("NEW PART")
            
            part_id = part_data.get("id")
            part_model = part_data.get("model")
            part_type = part_data.get("type")
            part_position = part_data.get("position")
            part_origin = part_data.get("origin")
            part_axis = part_data.get("axis")
            part_joint = part_data.get("joint")
            part_child = part_data.get("child")
            
            print(part_root)
            print()
            print(part_id)
            print(part_model)
            print(part_type)
            print(part_position)
            print(part_origin)
            print(part_axis)
            print(part_joint)
        
            part_source = vtk.vtkSTLReader()
            part_source.SetFileName(part_model)
            
            part_mapper = vtk.vtkPolyDataMapper()
            part_mapper.SetInputConnection(part_source.GetOutputPort())
            
            part_actor = MachinePart()
            
            part_actor.SetMapper(part_mapper)
            
            part_actor.GetProperty().SetColor(1, 0, 1)
            part_actor.GetProperty().SetDiffuseColor(0.9, 0.9, 0.9)
            part_actor.GetProperty().SetDiffuse(.8)
            part_actor.GetProperty().SetSpecular(.5)
            part_actor.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
            part_actor.GetProperty().SetSpecularPower(30.0)
            
            part_actor.SetPosition(part_position[0], part_position[1], part_position[2])
            part_actor.SetOrigin(part_origin[0], part_origin[1], part_origin[2])
            
            part_actor.SetPartAxis(part_axis)
            part_actor.SetPartType(part_type)

            
            tmp_assembly = vtk.vtkAssembly()
            tmp_assembly.AddPart(part_actor)

            
            if previous_part == None:
                 path.AddNode(self, vtk.vtkMatrix4x4())
                 previous_part = self
                 self.AddPart(part_actor)
                 
            else:
                 path.AddNode(part_actor, vtk.vtkMatrix4x4())
                 previous_part = part_actor
            
            
            print("########")
            

    def items_recursive(self, d):
        
        for k, v in d.items():
            
            if isinstance(v, dict):
                
                yield k, v
                
                for k1, v1 in self.items_recursive(v):
                    
                    yield k1, v1   
            else:
                pass
