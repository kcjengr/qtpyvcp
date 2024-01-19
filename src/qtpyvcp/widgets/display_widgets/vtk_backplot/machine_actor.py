import os
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
from collections import OrderedDict

from qtpyvcp.utilities.settings import getSetting

LOG = logger.getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)



class MachineCubeActor(vtk.vtkCubeAxesActor):
    def __init__(self, linuxcncDataSource):
        super(MachineCubeActor, self).__init__()
        
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
        
        
        self.SetGridLineLocation(self.VTK_GRID_LINES_FURTHEST);

        grid_color = vtk.vtkProperty()
        grid_color.SetColor(0.05, 0.05, 0.05)
        
        self.SetXAxesGridlinesProperty(grid_color)
        self.SetYAxesGridlinesProperty(grid_color)
        self.SetZAxesGridlinesProperty(grid_color)
        
        edjes_color = vtk.vtkProperty()
        edjes_color.SetColor(0.45, 0.45, 0.45)
        
        self.SetXAxesLinesProperty(edjes_color)
        self.SetYAxesLinesProperty(edjes_color)
        self.SetZAxesLinesProperty(edjes_color)

        # x_actor = self.GetXAxisActor()
        # y_actor = self.GetYAxisActor()
        # z_actor = self.GetZAxisActor()
        #
        # x_actor.SetLabelFactor(8)
        # y_actor.SetLabelFactor(8)
        # z_actor.SetLabelFactor(8)
        #

        # self.SetLabelFormat("%6.3f")
        
        # self.SetFlyModeToOuterEdges()
        
        self.SetFlyModeToStaticEdges()
        
        # self.SetFlyModeToClosestTriad()
        # self.SetFlyModeToStaticTriad()
        
        
        # label_properties = self.GetAxisLabelTextProperty()
        # label_properties.SetOrientation(30)
        # label_properties.SetLineOffset(5)
        #
        # self.SetAxisLabelTextProperty(label_properties)
        
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




class MachineLineActor(vtk.vtkCubeAxesActor2D):
    def __init__(self, linuxcncDataSource):
        super(MachineLineActor, self).__init__()
        
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
        
        if self._datasource.isMachineJet():
            self.SetFlyModeToNone()
        else:
            self.SetFlyModeToOuterEdges()
        
        if self._datasource.isMachineJet():
            self.ZAxisVisibilityOff()
            # self.YAxisVisibilityOff()
            
        label_properties = self.GetAxisLabelTextProperty()
        label_properties.SetOrientation(30)
        label_properties.SetLineOffset(5)
        
        self.SetAxisLabelTextProperty(label_properties)
        
        if not IN_DESIGNER:
            bounds = getSetting('backplot.show-machine-bounds')
            self.showMachineBounds(bounds and bounds.value)
                                   
    def showMachineTicks(self, ticks):
        pass
        # if ticks:
        #     self.XAxisTickVisibilityOn()
        #     self.YAxisTickVisibilityOn()
        #     self.ZAxisTickVisibilityOn()
        # else:
        #     self.XAxisTickVisibilityOff()
        #     self.YAxisTickVisibilityOff()
        #     self.ZAxisTickVisibilityOff()

    def showMachineBounds(self, bounds):
        if bounds:
            if self._datasource.isMachineJet():
                self.XAxisVisibilityOn()
                self.YAxisVisibilityOn()
            else:  
                self.XAxisVisibilityOn()
                self.YAxisVisibilityOn()
                self.ZAxisVisibilityOn()
        else:
            if self._datasource.isMachineJet():
                self.XAxisVisibilityOff()
                self.YAxisVisibilityOff()
            else:
                self.XAxisVisibilityOff()
                self.YAxisVisibilityOff()
                self.ZAxisVisibilityOff()


    def showMachineLabels(self, labels):
        pass
        # if labels:
        #     self.XAxisLabelVisibilityOn()
        #     self.YAxisLabelVisibilityOn()
        #     self.ZAxisLabelVisibilityOn()
        # else:
        #     self.XAxisLabelVisibilityOff()
        #     self.YAxisLabelVisibilityOff()
        #     self.ZAxisLabelVisibilityOff()

    def showGridlines(self, grid):
        pass
        # if grid:
        #     self.DrawXGridlinesOn()
        #     self.DrawYGridlinesOn()
        #     self.DrawZGridlinesOn()
        # else:
        #     self.DrawXGridlinesOff()
        #     self.DrawYGridlinesOff()
        #     self.DrawZGridlinesOff()


class MachinePart(vtk.vtkAssembly):

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
        
        print("########")
        print("NEW Machine")
        
        # print(f"{parts}")
        previous_asm = None
        
        parts_dict = OrderedDict()
        previous_depth = 0
        branch_num = 0
        
        # for depth, part_root, part_data in self.items_recursive(parts):
        for part in self.items_recursive(parts, self):
            print(f"{part}")
            
        print(f"vtkAssembly: {self}")


    def create_part(self, data):
        
        part_id = data.get("id")
        part_model = data.get("model")
        part_type = data.get("type")
        part_position = data.get("position")
        part_origin = data.get("origin")
        part_axis = data.get("axis")
        part_joint = data.get("joint")
        
        print(f"part_id:\t\t{part_id}")
        print(f"part_model:\t\t{part_model}")
        print(f"part_type:\t\t{part_type}")
        print(f"part_position:\t\t{part_position}")
        print(f"part_origin:\t\t{part_origin}")
        print(f"part_axis:\t\t{part_axis}")
        print(f"part_joint:\t\t{part_joint}")
        
        part_source = vtk.vtkSTLReader()
        part_source.SetFileName(part_model)
        part_source.Update()
        
        part_mapper = vtk.vtkPolyDataMapper()
        part_mapper.SetInputConnection(part_source.GetOutputPort())
        
        part_actor = vtk.vtkActor()
        
        part_actor.SetMapper(part_mapper)
        
        part_actor.GetProperty().SetColor(1, 0, 1)
        part_actor.GetProperty().SetDiffuseColor(0.9, 0.9, 0.9)
        part_actor.GetProperty().SetDiffuse(.8)
        part_actor.GetProperty().SetSpecular(.5)
        part_actor.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
        part_actor.GetProperty().SetSpecularPower(30.0)
        
        part_actor.SetPosition(part_position[0], part_position[1], part_position[2])
        part_actor.SetOrigin(part_origin[0], part_origin[1], part_origin[2])
        
        tmp_assembly = MachinePart()
        tmp_assembly.SetPartAxis(part_axis)
        tmp_assembly.SetPartType(part_type)
        
        tmp_assembly.AddPart(part_actor)
        
        return tmp_assembly

    def items_recursive(self, d, parent):
        
        for _, v in d.items():
            if isinstance(v, dict):
                tmp_part = self.create_part(v)
                parent.AddPart(tmp_part)
                yield tmp_part
                for p in self.items_recursive(v, tmp_part):
                    parent.AddPart(tmp_part)
                    yield tmp_part
        
                