"""
HAL Button
----------

Button for setting `bit` HAL pin values.

Generated HAL Pins
++++++++++++++++++

========================= ===== =========
HAL Pin Name              Type  Direction
========================= ===== =========
qtpyvcp.button.enable     bit   in
qtpyvcp.button.out        bit   out
========================= ===== =========
"""

from qtpy.QtWidgets import QPushButton

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalButton(QPushButton, HALWidget):
    """HAL CheckBox"""
    def __init__(self, parent=None):
        super(HalButton, self).__init__(parent)

        self.setText("HAL Button")

        self._enable_pin = None
        self._pressed_pin = None

        self.pressed.connect(self.onPress)
        self.released.connect(self.onRelease)

    def onPress(self):
        if self._pressed_pin is not None:
            self._pressed_pin.value = True

    def onRelease(self):
        if self._pressed_pin is not None:
            self._pressed_pin.value = False

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add button.enable HAL pin
        self._enable_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add button.out HAL pin
        self._pressed_pin = comp.addPin(obj_name + ".out", "bit", "out")
