from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Property, Q_ENUMS

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget

from . import HalType

# Setup logging
from qtpyvcp.utilities.logger import getLogger
LOG = getLogger(__name__)

class HalLabel(QLabel, HALWidget, HalType):
    """HAL Label

    Label for displaying HAL pin values.

    Input pin type is selectable via the :class:`.pinType` property in designer,
    and can be any valid HAL type (bit, u32, s32, float).

    The text format can be specified via the :class:`.textFormat` property in
    designer and can be any valid python style format string.

    .. table:: Generated HAL Pins

        ========================= =========== =========
        HAL Pin Name              Type        Direction
        ========================= =========== =========
        qtpyvcp.label.enable      bit         in
        qtpyvcp.label.in          selecatable in
        ========================= =========== =========
    """
    Q_ENUMS(HalType)

    def __init__(self, parent=None):
        super(HalLabel, self).__init__(parent)

        self._in_pin = None
        self._enable_pin = None

        self._typ = "float"
        self._fmt = ".2f"
        
        self._value = 0

        self.setValue(0)

    def setValue(self, value):
        self._value = value
        self.setText(f"{value:{self._fmt}}")
            

    @Property(str)
    def textFormat(self):
        """Text Format Property

        Args:
            fmt (str) : A valid python style format string. Defaults to ``%s``.
        """
        
        return self._fmt

    @textFormat.setter
    def textFormat(self, fmt):
        self._fmt = fmt
        self.setValue(self._value)
             
    @Property(HalType)
    def pinType(self):
        return getattr(HalType, self._typ)

    @pinType.setter
    def pinType(self, typ_enum):
        self._typ = HalType.toString(typ_enum)
        try:
            val = {'bit': False, 'u32': 0, 's32': 0, 'float': 0.0}[self._typ]
            self.setValue(val)
        except Exception as ex:
            LOG.debug(ex)

    def initialize(self):
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

        # add label.enable HAL pin
        self._enable_pin = comp.addPin(f"{obj_name}.enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add label.in HAL pin
        self._in_pin = comp.addPin(f"{obj_name}.in", self._typ, "in")
        self.setValue(self._in_pin.value)
        self._in_pin.valueChanged.connect(self.setValue)
