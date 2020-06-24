"""
HAL Bar Indicator
-----------------

Bar for indicating the value of `float` HAL pins.

.. table:: Generated HAL Pins

    ============================= ===== =========
    HAL Pin Name                  Type  Direction
    ============================= ===== =========
    qtpyvcp.bar-indicator.in-i    u32   in
    qtpyvcp.bar-indicator.in-f    float in
    qtpyvcp.bar-indicator.min-val float in
    qtpyvcp.bar-indicator.max-val float in
    ============================= ===== =========
"""

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget
from qtpyvcp.widgets.base_widgets.bar_indicator import BarIndicatorBase

# Setup logging
from qtpyvcp.utilities.logger import getLogger
log = getLogger(__name__)


class HalBarIndicator(BarIndicatorBase, HALWidget):
    """HAL Bar Indicator"""
    def __init__(self, parent=None):
        super(HalBarIndicator, self).__init__(parent)

        self._int_in_pin = None
        self._float_in_pin = None

        self._min_val_pin = None
        self._max_val_pin = None

    def initialize(self):
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

        if self.minimum < 0:
            int_pin_typ = 's32'
        else:
            int_pin_typ = 'u32'

        # add bar-indicator.in-f HAL pin
        self._int_in_pin = comp.addPin(obj_name + ".in-f", "float", "in")
        self.setValue(self._int_in_pin.value)
        self._int_in_pin.valueChanged.connect(self.setValue)

        # add bar-indicator.in-i HAL pin
        self._float_in_pin = comp.addPin(obj_name + ".in-i", int_pin_typ, "in")
        self.setValue(self._float_in_pin.value)
        self._float_in_pin.valueChanged.connect(self.setValue)

        # add bar-indicator.min-val HAL pin
        self._min_val_pin = comp.addPin(obj_name + ".min-val", "float", "in")
        self._min_val_pin.value = self.minimum
        self._min_val_pin.valueChanged.connect(lambda v: self.setProperty('minimum', v))

        # add bar-indicator.max-val HAL pin
        self._max_val_pin = comp.addPin(obj_name + ".max-val", "float", "in")
        self._max_val_pin.value = self.maximum
        self._max_val_pin.valueChanged.connect(lambda v: self.setProperty('maximum', v))

# testing
if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = HalBarIndicator()
    w.setObjectName('hal-bar')
    w.initialize()
    w.show()
    w.setValue(65)
    sys.exit(app.exec_())