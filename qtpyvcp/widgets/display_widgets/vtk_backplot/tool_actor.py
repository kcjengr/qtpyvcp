# -*- coding: utf-8 -*-

import os

from math import cos, sin, radians

import vtk.qt

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper

from qtpyvcp.utilities import logger
from qtpyvcp.utilities.settings import getSetting

from qtpyvcp.plugins import iterPlugins, getPlugin
from qtpyvcp.plugins.db_tool_table import DBToolTable

from qtpyvcp.lib.db_tool.base import Session, Base, engine
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool, ToolModel

LOG = logger.getLogger(__name__)

class ToolActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource):
        super(ToolActor, self).__init__()
        self._datasource = linuxcncDataSource
        self._tool_table = self._datasource.getToolTable()

        self.session = Session()

        tool = self._tool_table[0]

        if self._datasource.isMachineMetric():
            self.height = 25.4 * 2.0
        else:
            self.height = 2.0

        if self._datasource.isMachineLathe():
            if tool.id == 0 or tool.id == -1:
                polygonSource = vtk.vtkRegularPolygonSource()
                polygonSource.SetNumberOfSides(64)
                polygonSource.SetRadius(0.035)
                polygonSource.SetCenter(0.0, 0.0, 0.0)

                transform = vtk.vtkTransform()
                transform.RotateWXYZ(90, 1, 0, 0)

                transform_filter = vtk.vtkTransformPolyDataFilter()
                transform_filter.SetTransform(transform)
                transform_filter.SetInputConnection(polygonSource.GetOutputPort())
                transform_filter.Update()

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(transform_filter.GetOutputPort())
            else:
                if tool.orientation == 1 and tool.frontangle == 90 and tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset - 0.05))
                    points.InsertNextPoint((-tool.xoffset + 0.5, 0.0, -tool.zoffset - 0.05))
                    points.InsertNextPoint((-tool.xoffset + 0.5, 0.0, -tool.zoffset))
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset))

                    # Create the polygon
                    # Create a quad on the four points
                    quad = vtk.vtkQuad()
                    quad.GetPointIds().SetId(0, 0)
                    quad.GetPointIds().SetId(1, 1)
                    quad.GetPointIds().SetId(2, 2)
                    quad.GetPointIds().SetId(3, 3)

                    # Add the polygon to a list of polygons
                    polygons = vtk.vtkCellArray()
                    polygons.InsertNextCell(quad)

                    # Create a PolyData
                    polygonPolyData = vtk.vtkPolyData()
                    polygonPolyData.SetPoints(points)
                    polygonPolyData.SetPolys(polygons)

                    # Create a mapper and actor
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(polygonPolyData)

                elif tool.orientation == 2 and tool.frontangle == 90 and tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-tool.xoffset + 0.5, 0.0, -tool.zoffset))
                    points.InsertNextPoint((-tool.xoffset + 0.5, 0.0, -tool.zoffset + 0.05))
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset + 0.05))
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset))

                    # Create the polygon
                    # Create a quad on the four points
                    quad = vtk.vtkQuad()
                    quad.GetPointIds().SetId(0, 0)
                    quad.GetPointIds().SetId(1, 1)
                    quad.GetPointIds().SetId(2, 2)
                    quad.GetPointIds().SetId(3, 3)

                    # Add the polygon to a list of polygons
                    polygons = vtk.vtkCellArray()
                    polygons.InsertNextCell(quad)

                    # Create a PolyData
                    polygonPolyData = vtk.vtkPolyData()
                    polygonPolyData.SetPoints(points)
                    polygonPolyData.SetPolys(polygons)

                    # Create a mapper and actor
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(polygonPolyData)

                elif tool.orientation == 3 and tool.frontangle == 90 and tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset))
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset + 0.05))
                    points.InsertNextPoint((-tool.xoffset - 0.5, 0.0, -tool.zoffset + 0.05))
                    points.InsertNextPoint((-tool.xoffset - 0.5, 0.0, -tool.zoffset))

                    # Create the polygon
                    # Create a quad on the four points
                    quad = vtk.vtkQuad()
                    quad.GetPointIds().SetId(0, 0)
                    quad.GetPointIds().SetId(1, 1)
                    quad.GetPointIds().SetId(2, 2)
                    quad.GetPointIds().SetId(3, 3)

                    # Add the polygon to a list of polygons
                    polygons = vtk.vtkCellArray()
                    polygons.InsertNextCell(quad)

                    # Create a PolyData
                    polygonPolyData = vtk.vtkPolyData()
                    polygonPolyData.SetPoints(points)
                    polygonPolyData.SetPolys(polygons)

                    # Create a mapper and actor
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(polygonPolyData)

                elif tool.orientation == 4 and tool.frontangle == 90 and tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-tool.xoffset - 0.5, 0.0, -tool.zoffset))
                    points.InsertNextPoint((-tool.xoffset - 0.5, 0.0, -tool.zoffset - 0.05))
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset - 0.05))
                    points.InsertNextPoint((-tool.xoffset, 0.0, -tool.zoffset))

                    # Create the polygon
                    # Create a quad on the four points
                    quad = vtk.vtkQuad()
                    quad.GetPointIds().SetId(0, 0)
                    quad.GetPointIds().SetId(1, 1)
                    quad.GetPointIds().SetId(2, 2)
                    quad.GetPointIds().SetId(3, 3)

                    # Add the polygon to a list of polygons
                    polygons = vtk.vtkCellArray()
                    polygons.InsertNextCell(quad)

                    # Create a PolyData
                    polygonPolyData = vtk.vtkPolyData()
                    polygonPolyData.SetPoints(points)
                    polygonPolyData.SetPolys(polygons)

                    # Create a mapper and actor
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(polygonPolyData)

                elif tool.orientation == 9:

                    radius = tool.diameter / 2

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-tool.xoffset + radius, 0.0, -tool.zoffset))
                    points.InsertNextPoint((-tool.xoffset + radius, 0.0, -tool.zoffset + 1.0))
                    points.InsertNextPoint((-tool.xoffset - radius, 0.0, -tool.zoffset + 1.0))
                    points.InsertNextPoint((-tool.xoffset - radius, 0.0, -tool.zoffset))

                    # Create the polygon
                    # Create a quad on the four points
                    quad = vtk.vtkQuad()
                    quad.GetPointIds().SetId(0, 0)
                    quad.GetPointIds().SetId(1, 1)
                    quad.GetPointIds().SetId(2, 2)
                    quad.GetPointIds().SetId(3, 3)

                    # Add the polygon to a list of polygons
                    polygons = vtk.vtkCellArray()
                    polygons.InsertNextCell(quad)

                    # Create a PolyData
                    polygonPolyData = vtk.vtkPolyData()
                    polygonPolyData.SetPoints(points)
                    polygonPolyData.SetPolys(polygons)

                    # Create a mapper and actor
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(polygonPolyData)
                else:
                    positive = 1
                    negative = -1
                    flip = False

                    if tool.orientation == 1:
                        fa_x_pol = negative
                        fa_z_pol = negative

                        ba_x_pol = negative
                        ba_z_pol = negative
                        flip = True

                    elif tool.orientation == 2:
                        fa_x_pol = negative
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = positive

                    elif tool.orientation == 3:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = positive
                        ba_z_pol = positive
                        flip = True

                    elif tool.orientation == 4:
                        fa_x_pol = positive
                        fa_z_pol = negative

                        ba_x_pol = positive
                        ba_z_pol = negative
                        flip = True

                    elif tool.orientation == 5:
                        fa_x_pol = negative
                        fa_z_pol = negative

                        ba_x_pol = positive
                        ba_z_pol = negative
                        flip = True

                    elif tool.orientation == 6:
                        fa_x_pol = negative
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = negative
                        flip = True

                    elif tool.orientation == 7:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = positive

                    elif tool.orientation == 8:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = positive
                        ba_z_pol = negative
                    else:
                        fa_x_pol = 0.0
                        fa_z_pol = 0.0

                        ba_x_pol = 0.0
                        ba_z_pol = 0.0

                    A = radians(float(tool.frontangle))
                    B = radians(float(tool.backangle))
                    C = 0.35

                    p1_x = abs(C * sin(A))
                    p1_z = abs(C * cos(A))

                    p2_x = abs(C * sin(B))
                    p2_z = abs(C * cos(B))

                    p1_x_pos = p1_x * fa_x_pol
                    p1_z_pos = p1_z * fa_z_pol

                    p2_x_pos = p2_x * ba_x_pol
                    p2_z_pos = p2_z * ba_z_pol

                    LOG.debug("Drawing Lathe tool id {}".format(tool.id))

                    LOG.debug(
                        "FrontAngle {} Point P1 X = {} P1 Z = {}".format(float(tool.frontangle), p1_x_pos, p1_z_pos))
                    LOG.debug(
                        "BackAngle {} Point P2 X = {} P2 Z = {}".format(float(tool.backangle), p2_x_pos, p2_z_pos))

                    # Setup three points
                    points = vtk.vtkPoints()

                    if flip:
                        points.InsertNextPoint((tool.xoffset + p2_x_pos, 0.0, p2_z_pos - tool.zoffset))
                        points.InsertNextPoint((tool.xoffset + p1_x_pos, 0.0, p1_z_pos - tool.zoffset))
                        points.InsertNextPoint((tool.xoffset, 0.0, -tool.zoffset))
                    else:
                        points.InsertNextPoint((tool.xoffset, 0.0, -tool.zoffset))
                        points.InsertNextPoint((tool.xoffset + p1_x_pos, 0.0, p1_z_pos - tool.zoffset))
                        points.InsertNextPoint((tool.xoffset + p2_x_pos, 0.0, p2_z_pos - tool.zoffset))

                    # Create the polygon
                    polygon = vtk.vtkPolygon()
                    polygon.GetPointIds().SetNumberOfIds(3)  # make a quad
                    polygon.GetPointIds().SetId(0, 0)
                    polygon.GetPointIds().SetId(1, 1)
                    polygon.GetPointIds().SetId(2, 2)

                    # Add the polygon to a list of polygons
                    polygons = vtk.vtkCellArray()
                    polygons.InsertNextCell(polygon)

                    # Create a PolyData
                    polygon_poly_data = vtk.vtkPolyData()
                    polygon_poly_data.SetPoints(points)
                    polygon_poly_data.SetPolys(polygons)

                    transform = vtk.vtkTransform()
                    transform.RotateWXYZ(180, 0, 0, 1)

                    transform_filter = vtk.vtkTransformPolyDataFilter()
                    transform_filter.SetTransform(transform)
                    transform_filter.SetInputData(polygon_poly_data)
                    transform_filter.Update()

                    # Create a mapper
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputConnection(transform_filter.GetOutputPort())

        else:
            if tool.id == 0 or tool.diameter < .05:
                transform = vtk.vtkTransform()

                source = vtk.vtkConeSource()
                source.SetHeight(self.height / 2)
                #source.SetCenter(-self.height / 4 - tool.zoffset, -tool.yoffset, -tool.xoffset)
                source.SetCenter(-self.height / 4, 0, 0)
                source.SetRadius(self.height / 4)
                source.SetResolution(64)
                transform.RotateWXYZ(90, 0, 1, 0)
                transform_filter = vtk.vtkTransformPolyDataFilter()
                transform_filter.SetTransform(transform)
                transform_filter.SetInputConnection(source.GetOutputPort())
                transform_filter.Update()

                # Create a mapper
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(transform_filter.GetOutputPort())
            else:
                plugins = dict(iterPlugins())
                tool_table_plugin = plugins["tooltable"]
                
                transform = vtk.vtkTransform()
                # Create a mapper
                mapper = vtk.vtkPolyDataMapper()
                
                if isinstance(tool_table_plugin, DBToolTable):
                    tool_data = self.session.query(ToolModel).filter(ToolModel.tool_no == tool.id).first()
        
                    if tool_data:
                        
                        filename = tool_data.model
                        
                        source = vtk.vtkSTLReader()
                        source.SetFileName(filename)
                        
                        # source = vtk.vtkCylinderSource()
                        # source.SetHeight(self.height / 2)
                        # #source.SetCenter(-tool.xoffset, self.height / 4 - tool.zoffset, tool.yoffset)
                        # source.SetCenter(0, self.height / 4, 0)
                        # source.SetRadius(tool.diameter / 2)
                        # source.SetResolution(64)
                        
                        # transform.RotateWXYZ(180, 1, 0, 0)
        
                        transform_filter = vtk.vtkTransformPolyDataFilter()
                        transform_filter.SetTransform(transform)
                        transform_filter.SetInputConnection(source.GetOutputPort())
                        transform_filter.Update()
        
                        mapper.SetInputConnection(transform_filter.GetOutputPort())

        self.SetMapper(mapper)

        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(1)


class ToolBitActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource):
        super(ToolBitActor, self).__init__()
        
        self._datasource = linuxcncDataSource
        self._tool_table = self._datasource.getToolTable()
        
        tool = self._tool_table[0]
        
        if self._datasource.isMachineMetric():
            self.height = 25.4 * 2.0
        else:
            self.height = 2.0
            
        start_point = [tool.xoffset, tool.yoffset, tool.zoffset]
        end_point = [0, 0, 0]
        
        source = vtkCylinderSource()
        transform = vtk.vtkTransform()

        # source.SetHeight(tool.zoffset)
        source.SetHeight(10)
        source.SetCenter(tool.xoffset, tool.zoffset - 5, tool.yoffset,)
        source.SetRadius(tool.diameter / 2)
        source.SetResolution(64)
        
        transform.RotateWXYZ(90, 1, 0, 0)
        
        transform.RotateX(tool.aoffset)
        transform.RotateY(tool.boffset)
        transform.RotateZ(tool.coffset)
        
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputConnection(source.GetOutputPort())
        transform_filter.Update()
        
        colors = vtkNamedColors()
        
        # Create a mapper and actor for the arrow
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(transform_filter.GetOutputPort())
            
            
        self.SetMapper(mapper)
        
        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(1)

                    