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
        colors = vtkNamedColors()

        if self._datasource.isMachineMetric():
            self.height = 25.4 * 2.0
        else:
            self.height = 2.0



        if self._datasource.isMachineFoam():

            transform = vtk.vtkTransform()

            source = vtk.vtkConeSource()
            source.SetHeight(self.height / 2)
            #source.SetCenter(-self.height / 4 - tool.zoffset, -tool.yoffset, -tool.xoffset)
            source.SetCenter(-self.height / 4, 0, 0)
            source.SetRadius(self.height / 4)
            source.SetResolution(64)
            transform.RotateWXYZ(-90, 0, 1, 0)
            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetTransform(transform)
            transform_filter.SetInputConnection(source.GetOutputPort())
            transform_filter.Update()

            # Create a mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(transform_filter.GetOutputPort())

            self.GetProperty().SetColor(colors.GetColor3d('Red'))

        elif self._datasource.isMachineLathe():
            mapper = vtk.vtkPolyDataMapper()
        elif self._datasource.isMachineJet():
            mapper = vtk.vtkPolyDataMapper()
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

        self.tool_position = []
        self.foam_z = 0.0
        self.foam_w = 0.0

        self.tool = self._tool_table[0]

        if self._datasource.isMachineMetric():
            self.height = 25.4 * 2.0
        else:
            self.height = 2.0

        # FOAM TOOL

        if self._datasource.isMachineLathe():

            if self.tool.id == 0 or self.tool.id == -1:
                source = vtk.vtkRegularPolygonSource()
                source.SetNumberOfSides(64)
                source.SetRadius(0.035)
                source.SetCenter(0.0, 0.0, 0.0)

                transform = vtk.vtkTransform()
                transform.RotateWXYZ(90, 1, 0, 0)

                transform_filter = vtk.vtkTransformPolyDataFilter()
                transform_filter.SetTransform(transform)
                transform_filter.SetInputConnection(source.GetOutputPort())
                transform_filter.Update()

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(transform_filter.GetOutputPort())
            else:
                if self.tool.orientation == 1 and self.tool.frontangle == 90 and self.tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset - 0.05))
                    points.InsertNextPoint((-self.tool.xoffset + 0.5, 0.0, -self.tool.zoffset - 0.05))
                    points.InsertNextPoint((-self.tool.xoffset + 0.5, 0.0, -self.tool.zoffset))
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset))

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

                elif self.tool.orientation == 2 and self.tool.frontangle == 90 and self.tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-self.tool.xoffset + 0.5, 0.0, -self.tool.zoffset))
                    points.InsertNextPoint((-self.tool.xoffset + 0.5, 0.0, -self.tool.zoffset + 0.05))
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset + 0.05))
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset))

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

                elif self.tool.orientation == 3 and self.tool.frontangle == 90 and self.tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset))
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset + 0.05))
                    points.InsertNextPoint((-self.tool.xoffset - 0.5, 0.0, -self.tool.zoffset + 0.05))
                    points.InsertNextPoint((-self.tool.xoffset - 0.5, 0.0, -self.tool.zoffset))

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

                elif self.tool.orientation == 4 and self.tool.frontangle == 90 and self.tool.backangle == 90:

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-self.tool.xoffset - 0.5, 0.0, -self.tool.zoffset))
                    points.InsertNextPoint((-self.tool.xoffset - 0.5, 0.0, -self.tool.zoffset - 0.05))
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset - 0.05))
                    points.InsertNextPoint((-self.tool.xoffset, 0.0, -self.tool.zoffset))

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

                elif self.tool.orientation == 9:

                    radius = self.tool.diameter / 2

                    # Setup four points
                    points = vtk.vtkPoints()
                    points.InsertNextPoint((-self.tool.xoffset + radius, 0.0, -self.tool.zoffset))
                    points.InsertNextPoint((-self.tool.xoffset + radius, 0.0, -self.tool.zoffset + 1.0))
                    points.InsertNextPoint((-self.tool.xoffset - radius, 0.0, -self.tool.zoffset + 1.0))
                    points.InsertNextPoint((-self.tool.xoffset - radius, 0.0, -self.tool.zoffset))

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

                    if self.tool.orientation == 1:
                        fa_x_pol = negative
                        fa_z_pol = negative

                        ba_x_pol = negative
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 2:
                        fa_x_pol = negative
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = positive

                    elif self.tool.orientation == 3:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = positive
                        ba_z_pol = positive
                        flip = True

                    elif self.tool.orientation == 4:
                        fa_x_pol = positive
                        fa_z_pol = negative

                        ba_x_pol = positive
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 5:
                        fa_x_pol = negative
                        fa_z_pol = negative

                        ba_x_pol = positive
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 6:
                        fa_x_pol = negative
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = negative
                        flip = True

                    elif self.tool.orientation == 7:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = negative
                        ba_z_pol = positive

                    elif self.tool.orientation == 8:
                        fa_x_pol = positive
                        fa_z_pol = positive

                        ba_x_pol = positive
                        ba_z_pol = negative
                    else:
                        fa_x_pol = 0.0
                        fa_z_pol = 0.0

                        ba_x_pol = 0.0
                        ba_z_pol = 0.0

                    A = radians(float(self.tool.frontangle))
                    B = radians(float(self.tool.backangle))
                    C = 0.35

                    p1_x = abs(C * sin(A))
                    p1_z = abs(C * cos(A))

                    p2_x = abs(C * sin(B))
                    p2_z = abs(C * cos(B))

                    p1_x_pos = p1_x * fa_x_pol
                    p1_z_pos = p1_z * fa_z_pol

                    p2_x_pos = p2_x * ba_x_pol
                    p2_z_pos = p2_z * ba_z_pol

                    LOG.debug("Drawing Lathe tool id {}".format(self.tool.id))

                    LOG.debug("FrontAngle {} Point P1 X = {} P1 Z = {}"
                              .format(float(self.tool.frontangle), p1_x_pos, p1_z_pos))
                    LOG.debug("BackAngle {} Point P2 X = {} P2 Z = {}"
                              .format(float(self.tool.backangle), p2_x_pos, p2_z_pos))

                    # Setup three points
                    points = vtk.vtkPoints()

                    if flip:
                        points.InsertNextPoint((self.tool.xoffset + p2_x_pos, 0.0, p2_z_pos - self.tool.zoffset))
                        points.InsertNextPoint((self.tool.xoffset + p1_x_pos, 0.0, p1_z_pos - self.tool.zoffset))
                        points.InsertNextPoint((self.tool.xoffset, 0.0, -self.tool.zoffset))  # Fixed here
                    else:
                        points.InsertNextPoint((self.tool.xoffset, 0.0, -self.tool.zoffset))  # Fixed here
                        points.InsertNextPoint((self.tool.xoffset + p1_x_pos, 0.0, p1_z_pos - self.tool.zoffset))
                        points.InsertNextPoint((self.tool.xoffset + p2_x_pos, 0.0, p2_z_pos - self.tool.zoffset))

                    # Create the polygon
                    polygon = vtk.vtkPolygon()
                    polygon.GetPointIds().SetNumberOfIds(6)  # make a quad
                    polygon.GetPointIds().SetId(0, 0)
                    polygon.GetPointIds().SetId(1, 1)
                    polygon.GetPointIds().SetId(2, 2)

                    polygon.GetPointIds().SetId(3, 2)
                    polygon.GetPointIds().SetId(4, 1)
                    polygon.GetPointIds().SetId(5, 0)

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

        # LATHE TOOL

        elif self._datasource.isMachineFoam():

            # if self._datasource.isMachineMetric:
            #       self.foam_z *= 254
            #       self.foam_w *= 254
            #


            self.start_point = [self.tool.xoffset, self.tool.yoffset, self.tool.zoffset+self.foam_z]
            self.end_point = [self.tool.uoffset, self.tool.voffset, self.tool.woffset+self.foam_z]

            self.source = vtkLineSource()
            self.source.SetPoint1(self.start_point)
            self.source.SetPoint2(self.end_point)

            transform = vtk.vtkTransform()

            # # source.SetHeight(self.tool.zoffset)
            # source.SetHeight(10)
            # source.SetCenter(self.tool.xoffset, self.tool.zoffset - 5, self.tool.yoffset,)
            # source.SetRadius(self.tool.diameter / 2)
            # source.SetResolution(64)

            transform.RotateWXYZ(0, 1, 0, 0)

            transform.RotateX(self.tool.aoffset)
            transform.RotateY(self.tool.boffset)
            transform.RotateZ(self.tool.coffset)

            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetTransform(transform)
            transform_filter.SetInputConnection(self.source.GetOutputPort())
            transform_filter.Update()
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(transform_filter.GetOutputPort())

        # CNC TOOL

        else:

            self.source = vtkCylinderSource()
            transform = vtk.vtkTransform()


            self.source.SetHeight(self.tool.zoffset)
            self.source.SetCenter(self.tool.xoffset, self.tool.yoffset, -self.tool.zoffset/2)
            self.source.SetRadius(self.tool.diameter / 2)
            self.source.SetResolution(64)

            transform.RotateWXYZ(90, 1, 0, 0)
            
            transform.Translate(self.tool.xoffset, -self.tool.zoffset/2, self.tool.zoffset/2)

            transform.RotateX(self.tool.aoffset)
            transform.RotateY(self.tool.boffset)
            transform.RotateZ(self.tool.coffset)

            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetTransform(transform)
            transform_filter.SetInputConnection(self.source.GetOutputPort())
            transform_filter.Update()
            
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(transform_filter.GetOutputPort())

        # colors = vtkNamedColors()

        # Create a mapper and actor for the arrow
        # mapper = vtkPolyDataMapper()
        # mapper.SetInputConnection(transform_filter.GetOutputPort())
        #
        #
        self.SetMapper(mapper)

        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(1)

    def set_foam_offsets(self, zo, wo):

        self.foam_z = zo
        self.foam_w = wo

    def set_position_cnc(self, position):
        
        
        # self.source.SetCenter(self.tool.xoffset, self.tool.yoffset, -self.tool.zoffset/2)

        
        transform = vtk.vtkTransform()
        
        transform.Translate(position[0], position[1], (position[2] - self.tool.zoffset))
        
        transform.RotateX(position[3])
        transform.RotateY(position[5])
        transform.RotateZ(position[4])
        
        transform.Translate(-position[0], -position[1], -(position[2] - self.tool.zoffset))

        self.SetUserTransform(transform)
        
        self.SetPosition(position[0], position[1], position[2])
        
        
    def set_position(self, position):
        self.tool_position = position

        x, y, z = position[:3]
        u, v, w = position[6:9]

        self.source.SetPoint1(x, y ,z+self.foam_z)
        self.source.SetPoint2(u, v, w+self.foam_w)



