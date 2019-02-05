import math
from copy import copy

import vtk

from pygcode import Line, GCodeLinearMove, GCodeRapidMove

from qtpy.QtWidgets import QWidget, QFrame, QVBoxLayout, QSizePolicy
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets import VCPWidget


STATUS = getPlugin('status')


class VTKWidget(QWidget, VCPWidget):

    def __init__(self, parent=None):
        super(VTKWidget, self).__init__(parent)

        self.vertical_layout = QVBoxLayout()
        self.vtkWidget = QtVTKRender(self)
        self.vertical_layout.addWidget(self.vtkWidget)

        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Create source
        source = vtk.vtkConeSource()
        source.SetResolution(64)
        source.SetCenter(0, 0, 0.5)
        source.SetRadius(0.5)

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.renderer.AddActor(actor)
        self.renderer.SetBackground(0.1, 0.2, 0.4)
        self.renderer.ResetCamera()

        self.setLayout(self.vertical_layout)

        self.interactor.Initialize()
        self.interactor.Start()

    def add_actor(self, actor):
        self.renderer.AddActor(actor)


class QtVTKRender(QVTKRenderWindowInteractor):
    def __init__(self, parent, **kw):
        QVTKRenderWindowInteractor.__init__(self, parent, **kw)

        self.parent = parent
        self.status = STATUS

        self.status.file_loaded.connect(self.load_program)

        self.line = None
        self._last_filename = None

        self.previous_point = [0.0, 0.0, 0.0]

    def load_program(self, fname=None):

        if fname is None:
            fname = self._last_filename
        else:
            self._last_filename = fname

        with open(fname, 'r') as fh:

            self._last_filename = fname

            for line_text in fh.readlines():
                line = Line(line_text)

                for gcode in line.block.gcodes:

                    if isinstance(gcode, GCodeLinearMove):

                        self.line = VTKLineElement()

                        x_word = line.block.X
                        y_word = line.block.Y
                        z_word = line.block.Z

                        current_point = list(range(3))

                        if x_word is None:
                            current_point[0] = self.previous_point[0]
                        else:
                            current_point[0] = x_word.value

                        if y_word is None:
                            current_point[1] = self.previous_point[1]
                        else:
                            current_point[1] = y_word.value

                        if z_word is None:
                            current_point[2] = self.previous_point[2]
                        else:
                            current_point[2] = z_word.value

                        self.line.poly_line(current_point, self.previous_point)

                        self.previous_point = copy(current_point)

                        actor = self.line.get_actor()

                        actor.GetProperty().SetColor(1, 1, 1)  # (R,G,B)

                        self.parent.add_actor(actor)

                    elif isinstance(gcode, GCodeRapidMove):

                        self.line = VTKLineElement()

                        x_word = line.block.X
                        y_word = line.block.Y
                        z_word = line.block.Z

                        current_point = list(range(3))

                        if x_word is None:
                            current_point[0] = self.previous_point[0]
                        else:
                            current_point[0] = x_word.value

                        if y_word is None:
                            current_point[1] = self.previous_point[1]
                        else:
                            current_point[1] = y_word.value

                        if z_word is None:
                            current_point[2] = self.previous_point[2]
                        else:
                            current_point[2] = z_word.value

                        self.line.poly_line(current_point, self.previous_point)

                        self.previous_point = copy(current_point)

                        actor = self.line.get_actor()

                        actor.GetProperty().SetColor(1, 0, 0)  # (R,G,B)

                        self.parent.add_actor(actor)


class VTKLineElement:
    def __init__(self):
        self.points = None
        self.lines = None
        self.polygon = None
        self.polygonMapper = None
        self.polygonActor = None

    def poly_line(self, current_point, previous_point):

        self.points = vtk.vtkPoints()

        self.points.SetNumberOfPoints(2)
        self.points.SetPoint(0, previous_point)
        self.points.SetPoint(1, current_point)

        self.lines = vtk.vtkCellArray()
        self.lines.InsertNextCell(3)
        self.lines.InsertCellPoint(0)
        self.lines.InsertCellPoint(1)
        self.lines.InsertCellPoint(0)

        self.polygon = vtk.vtkPolyData()
        self.polygon.SetPoints(self.points)
        self.polygon.SetLines(self.lines)

        self.polygonMapper = vtk.vtkPolyDataMapper()

        if vtk.VTK_MAJOR_VERSION <= 5:
            self.polygonMapper.SetInputConnection(self.polygon.GetProducerPort())
        else:
            self.polygonMapper.SetInputData(self.polygon)
            self.polygonMapper.Update()

        self.polygonActor = vtk.vtkActor()
        self.polygonActor.SetMapper(self.polygonMapper)

    def get_actor(self):
        return self.polygonActor
