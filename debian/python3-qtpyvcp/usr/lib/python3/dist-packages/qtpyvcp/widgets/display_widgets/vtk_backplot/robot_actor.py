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
        
        self.parts_list = list()
        
        for id, data in enumerate(parts):
            
            source = vtk.vtkSTLReader()
            source.SetFileName(data["model"])
        
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
            tmp_assembly.SetPosition(data["position"])
            tmp_assembly.SetOrigin(data["origin"])
            
            self.parts_list.append(tmp_assembly)
            self.parts_list[id].AddPart(partActor)
            
            if(id > 0):
                self.parts_list[id-1].AddPart(tmp_assembly)
            
        self.AddPart(self.parts_list[0])
        
    def get_parts(self):
        return self.parts_list
        