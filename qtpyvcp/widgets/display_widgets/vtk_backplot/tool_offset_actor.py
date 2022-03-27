# -*- coding: utf-8 -*-

import vtk.qt
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import (
    vtkMath,
    vtkMinimalStandardRandomSequence
)
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkFiltersSources import vtkArrowSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper

from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)


class ToolOffsetActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource):
        super(ToolOffsetActor, self).__init__()
        
        self._datasource = linuxcncDataSource
        self._tool_table = self._datasource.getToolTable()
        
        tool = self._tool_table[0]
        print(tool)
        colors = vtkNamedColors()
        
        source = vtkArrowSource()
        self.GetProperty().SetColor(colors.GetColor3d('Cyan'))
        
        # Generate a random start and end point
        start_point = [-tool.xoffset, -tool.yoffset, -tool.zoffset]
        end_point = [0, 0, 0]
    
        rng = vtkMinimalStandardRandomSequence()
        rng.SetSeed(8775070)  # For testing.

        # Compute a basis
        normalizedX = [0] * 3
        normalizedY = [0] * 3
        normalizedZ = [0] * 3
        
        # The X axis is a vector from start to end
        vtkMath.Subtract(end_point, start_point, normalizedX)
        length = vtkMath.Norm(normalizedX)
        vtkMath.Normalize(normalizedX)
        
         # The Z axis is an arbitrary vector cross X
        arbitrary = [0] * 3
        for i in range(0, 3):
            rng.Next()
            arbitrary[i] = rng.GetRangeValue(-10, 10)
            
        vtkMath.Cross(normalizedX, arbitrary, normalizedZ)
        vtkMath.Normalize(normalizedZ)

    
        # The Y axis is Z cross X
        vtkMath.Cross(normalizedZ, normalizedX, normalizedY)
        matrix = vtkMatrix4x4()
    
        # Create the direction cosine matrix
        matrix.Identity()
        for i in range(0, 3):
            matrix.SetElement(i, 0, normalizedX[i])
            matrix.SetElement(i, 1, normalizedY[i])
            matrix.SetElement(i, 2, normalizedZ[i])
    
        # Apply the transforms
        transform = vtkTransform()
        transform.Translate(start_point)
        transform.Concatenate(matrix)
        transform.Scale(length, length, length)
    
        # Transform the polydata
        transformPD = vtkTransformPolyDataFilter()
        transformPD.SetTransform(transform)
        transformPD.SetInputConnection(source.GetOutputPort())
    
        # Create a mapper and actor for the arrow
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(transformPD.GetOutputPort())
            
            
        self.SetMapper(mapper)

        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(1)
            