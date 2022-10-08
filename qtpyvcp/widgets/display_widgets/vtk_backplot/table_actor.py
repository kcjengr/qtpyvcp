import vtk.qt
import math
from vtk.util.colors import *

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper


class TableActor(vtk.vtkActor):
    
    def __init__(self, mmodel):
        super(TableActor, self).__init__()
        
        source = vtk.vtkSTLReader()
        source.SetFileName(mmodel)
    
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        self.SetMapper(mapper)
        
        self.GetProperty().SetColor(1, 0, 1)
        self.GetProperty().SetDiffuseColor(0.9, 0.9, 0.9)
        self.GetProperty().SetDiffuse(.8)
        self.GetProperty().SetSpecular(.5)
        self.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
        self.GetProperty().SetSpecularPower(30.0)
        