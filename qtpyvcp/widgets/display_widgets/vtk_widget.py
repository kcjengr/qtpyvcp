import sys
import vtk

from qtpy.QtWidgets import QMainWindow, QWidget, QFrame, QVBoxLayout, QApplication
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.widgets import VCPWidget


class VTKWidget(VCPWidget):

    def __init__(self, parent = None):
        super(VTKWidget, self).__init__()
        
        self.frame = QFrame()
        self.vl = QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Create source
        source = vtk.vtkSphereSource()
        source.SetCenter(0, 0, 0)
        source.SetRadius(5.0)

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.ren.AddActor(actor)
        self.ren.ResetCamera()

        self.frame.setLayout(self.vl)
        self.addwidget(self.frame)

        self.iren.Initialize()
        self.iren.Start()
