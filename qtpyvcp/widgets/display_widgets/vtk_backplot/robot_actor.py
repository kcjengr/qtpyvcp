import vtk.qt
import math
from vtk.util.colors import *

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper


class RobotActor(vtk.vtkAssembly):
    def __init__(self, parts):
        super(RobotActor, self).__init__()
        
        for id, data in enumerate(parts):
            
            print(data)
            
            source = vtk.vtkSTLReader()
            source.SetFileName(data["model"])
        
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(source.GetOutputPort())
            
            partActor = vtk.vtkActor()
            
            partActor.SetMapper(mapper)
            partActor.SetPosition(data["position"])
            partActor.SetOrigin(data["origin"])
            
            partActor.GetProperty().SetColor(1, 0, 1)
            partActor.GetProperty().SetDiffuseColor(0.9, 0.9, 0.9)
            partActor.GetProperty().SetDiffuse(.8)
            partActor.GetProperty().SetSpecular(.5)
            partActor.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
            partActor.GetProperty().SetSpecularPower(30.0)
            
            self.AddPart(partActor)
        
    