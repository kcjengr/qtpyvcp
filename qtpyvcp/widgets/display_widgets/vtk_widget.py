import vtk

from qtpy.QtWidgets import QWidget, QFrame, QVBoxLayout, QSizePolicy
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qtpyvcp.widgets import VCPWidget


class VTKWidget(QWidget, VCPWidget):

    def __init__(self, parent=None):
        super(VTKWidget, self).__init__(parent)

        self.vertical_layout = QVBoxLayout()
        self.vtkWidget = QtVTKRender()
        self.vertical_layout.addWidget(self.vtkWidget)

        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Create source
        source = vtk.vtkConeSource()
        source.SetCenter(0, 0, 0)
        source.SetRadius(0.5)

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()

        self.setLayout(self.vertical_layout)

        self.interactor.Initialize()
        self.interactor.Start()


class QtVTKRender(QVTKRenderWindowInteractor):
    def __init__(self, **kw):
        QVTKRenderWindowInteractor.__init__(self, **kw)


