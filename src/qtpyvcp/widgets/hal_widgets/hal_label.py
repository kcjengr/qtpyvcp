from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Property

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget, VCPWidget

from qtpyvcp.widgets.hal_widgets import HalType

# Setup logging
from qtpyvcp.utilities.logger import getLogger
LOG = getLogger(__name__)

class HalLabel(QLabel, HALWidget, VCPWidget):
    """HAL Label

    Label for displaying HAL pin values.

    Input pin type is selectable via the :class:`.pinType` property in designer,
    and can be any valid HAL type (bool, uint, sint, real).

    The text format can be specified via the :class:`.valueFormat` property in
    designer and can be any valid python style format string.

    .. table:: Generated HAL Pins

        ========================= =========== =========
        HAL Pin Name              Type        Direction
        ========================= =========== =========
        qtpyvcp.label.enable      bool        in
        qtpyvcp.label.in          selecatable in
        ========================= =========== =========
    """
    TYPE_MAP = ('bool', 'uint', 'sint', 'real')

    def __init__(self, parent=None):
        super(HalLabel, self).__init__(parent)

        self._in_pin = None
        self._enable_pin = None

        self._typ = "real"
        self._fmt = ".2f"
        
        self._value = 0

        self.setValue(0)

    def setValue(self, value):
        self._value = value
        
        try:
            self.setText(f"{value:{self._fmt}}")
        except Exception as e:
            self.setText(f"ERR: {self._fmt}")
            LOG.warning("Invalid format specified")
            

    @Property(str)
    def valueFormat(self):
        """Value format property for HAL input display."""
        return self._fmt

    @valueFormat.setter
    def valueFormat(self, fmt):
        self._fmt = fmt
        self.setValue(self._value)

    @Property(str)
    def pinType(self):
        return self._typ

    @pinType.setter
    def pinType(self, typ_enum):
        if isinstance(typ_enum, HalType):
            typ = typ_enum.name
        elif isinstance(typ_enum, str):
            typ = typ_enum.strip()
        else:
            try:
                typ = HalType(typ_enum).name
            except Exception:
                typ = ''

        self._typ = typ if typ in self.TYPE_MAP else 'real'

        try:
            val = {'bool': False, 'uint': 0, 'sint': 0, 'real': 0.0}[self._typ]
            self.setValue(val)
        except Exception as ex:
            LOG.debug(ex)

    def initialize(self):
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

        # add label.enable HAL pin
        self._enable_pin = comp.addPin(f"{obj_name}.enable", "bool", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add label.in HAL pin
        self._in_pin = comp.addPin(f"{obj_name}.in", self._typ, "in")
        self.setValue(self._in_pin.value)
        self._in_pin.valueChanged.connect(self.setValue)

