"""
HAL LOAD METER Indicator
-----------------

LOAD METER for indicate the value of `float` HAL pins.

.. table:: Generated HAL Pins

    ========================= ========= =========
    HAL Pin Name              Type      Direction
    ========================= ========= =========
    qtpyvcp.loadmeter.value   float     in
    ========================= ========= =========
"""

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget
from qtpyvcp.widgets.base_widgets.bar_indicator import BarIndicator

# Setup logging
from qtpyvcp.utilities.logger import getLogger
log = getLogger(__name__)


class HalBarIndicator(BarIndicator, HALWidget):
    """HAL LOAD METER"""
    def __init__(self, parent=None):
        super(HalBarIndicator, self).__init__(parent)

        self._value_pin = None
        self._enabled_pin = None

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add loadmeter.value HAL pin
        self._value_pin = comp.addPin(obj_name + ".value", "float", "in")
        # self._value_pin.value = self.isO()
        self._value_pin.valueChanged.connect(lambda value: self.setValue(value))
