
from qtpy.QtWidgets import QSlider

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalSlider(QSlider, HALWidget):
    """HAL Slider

    Slider for setting `u32` or `float` HAL pin values.

    .. table:: Generated HAL Pins

        ========================= ===== =========
        HAL Pin Name              Type  Direction
        ========================= ===== =========
        qtpyvcp.slider.enable     bit   in
        qtpyvcp.slider.out-i      u32   out
        qtpyvcp.slider.out-f      float out
        ========================= ===== =========
    """
    def __init__(self, parent=None):
        super(HalSlider, self).__init__(parent)

        self._enable_pin = None
        self._s32_value_pin = None
        self._float_value_pin = None

        self._signed_int = True

        self.valueChanged.connect(self.onValueChanged)

    def onValueChanged(self, val):
        if self._s32_value_pin is not None:
            self._s32_value_pin.value = val
            self._float_value_pin.value = val / 100.0

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add slider.enable HAL pin
        self._enable_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add slider.percent HAL pin
        self._s32_value_pin = comp.addPin(obj_name + ".out-i", "u32", "out")
        self._s32_value_pin.value = self.value()

        # add slider.scale HAL pin
        self._float_value_pin = comp.addPin(obj_name + ".out-f", "float", "out")
        self._float_value_pin.value = self.value() / 100.0
