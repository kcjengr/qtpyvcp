from vtk import vtkActor, vtkCubeSource, vtkPolyDataMapper, vtkTransform

from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

class StockActor(vtkActor):
    def __init__(self, linuxcncDataSource):
        super(StockActor, self).__init__()

        self._datasource = linuxcncDataSource

        self.position = self._datasource.getActiveWcsOffsets()

        self.source = vtkCubeSource()
        self.source.SetCenter(0, 0, 0)
        self.source.SetXLength(0)
        self.source.SetYLength(0)
        self.source.SetZLength(0)
        self.source.Update()


        self.transform = vtkTransform()

        self.transform.Translate(self.position[0], self.position[1], self.position[2])

        self.transform.RotateX(self.position[3])
        self.transform.RotateY(self.position[5])
        self.transform.RotateZ(self.position[4])

        self.transform.Translate(-self.position[0], -self.position[1], -self.position[2])

        self.SetUserTransform(self.transform)

        self.SetPosition(self.position[0], self.position[1], self.position[2])

        stockMapper = vtkPolyDataMapper()
        stockMapper.SetInputConnection(self.source.GetOutputPort())

        self.SetMapper(stockMapper)
        self.GetProperty().SetOpacity(0.50)
        self.GetProperty().SetColor(0, 0, 1)

        self._datasource.g5xOffsetChanged.connect(self.set_position)
        self._datasource.stockUpdated.connect(self.update_data)

    def update_data(self, stock):

        size = stock.get("stock_size")
        origin = stock.get("stock_origin")

        LOG.debug(f"{size}")
        LOG.debug(f"{origin}")


        x_orig = origin.get('x')
        y_orig = origin.get('y')
        z_orig = origin.get('z')

        x_lenght = size.get('x')
        y_lenght = size.get('y')
        z_lenght = size.get('z')


        self.source.SetCenter(x_orig, y_orig, z_orig)
        self.source.SetXLength(x_lenght)
        self.source.SetYLength(y_lenght)
        self.source.SetZLength(z_lenght)
        self.source.Update()

    def set_position(self, position):
        self.position = position

        self.transform.Translate(self.position[0], self.position[1], self.position[2])
        self.transform.RotateX(self.position[3])
        self.transform.RotateY(self.position[5])
        self.transform.RotateZ(self.position[4])

        self.transform.Translate(-self.position[0], -self.position[1], -self.position[2])
        self.SetPosition(self.position[0], self.position[1], self.position[2])


    def get_source(self):
        return self.source
