import vtk.qt

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkFiltersSources import vtkCylinderSource
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper


class SpindleActor(vtk.vtkActor):
    def __init__(self, linuxcncDataSource, model_path):
        super(SpindleActor, self).__init__()
        
        self._datasource = linuxcncDataSource
        self._tool_table = self._datasource.getToolTable()
        
        tool = self._tool_table[0]
        
        if self._datasource.isMachineMetric():
            self.height = 25.4 * 2.0
        else:
            self.height = 2.0
            
        start_point = [-tool.xoffset, -tool.yoffset, -tool.zoffset]
        end_point = [0, 0, 0]
        
        filename = model_path
        # filename = os.path.join(os.path.dirname(__file__), "models/laser.stl")

        source = vtk.vtkSTLReader()
        source.SetFileName(filename)
                
        transform = vtk.vtkTransform()
        
        # transform.RotateWXYZ(180, 1, 0, 0)

        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputConnection(source.GetOutputPort())
        transform_filter.Update()
        
        colors = vtkNamedColors()
        
        # Create a mapper and actor for the arrow
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(transform_filter.GetOutputPort())
            
            
        self.SetMapper(mapper)
        
        self.GetProperty().SetDiffuse(0.8)
        self.GetProperty().SetDiffuseColor(colors.GetColor3d('LightSteelBlue'))
        self.GetProperty().SetSpecular(0.3)
        self.GetProperty().SetSpecularPower(60.0)
        
        # Avoid visible backfaces on Linux with some video cards like intel
        # From: https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1#comment89720589_51360335
        self.GetProperty().SetBackfaceCulling(1)
