
import vtk.qt
import math
from vtk.util.colors import *

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper


class RobotActor(vtk.vtkAssembly):
    def __init__(self):
        super(RobotActor, self).__init__()
        
        self.filenames = {
            "joint0": ["models/meca500/base.stl", [0,0,0], [0,0,0]],
            "joint1": ["models/meca500/link1.stl", [0,0,-135], [0,0,135]],
            "joint2": ["models/meca500/link2.stl", [0,0,-135], [0,0,135]],
            "joint3": ["models/meca500/link3.stl", [-61.5,0,-38], [61.5,0,38]],
            "joint4": ["models/meca500/link4.stl", [-58.5,0,0], [58.5,0,0]],
            "joint5": ["models/meca500/link5.stl", [-70,0,0], [70,0,0]],
            "joint6": ["models/meca500/link6.stl", [0,0,0], [0,0,0]],
        }

        self.parts = list()
        
        for id, data in enumerate(self.filenames.items()):
            
            source = vtk.vtkSTLReader()
            source.SetFileName(data[1][0])
        
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(source.GetOutputPort())
            
            partActor = vtk.vtkActor()
            
            partActor.SetMapper(mapper)
            partActor.SetOrigin(data[1][1])
            partActor.SetPosition(data[1][2])
            
            partActor.GetProperty().SetColor(1, 0, 1)
            partActor.GetProperty().SetDiffuseColor(0.9, 0.9, 0.9)
            partActor.GetProperty().SetDiffuse(.8)
            partActor.GetProperty().SetSpecular(.5)
            partActor.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
            partActor.GetProperty().SetSpecularPower(30.0)
            
            self.parts.append(partActor)
            self.AddPart(partActor)
        
    