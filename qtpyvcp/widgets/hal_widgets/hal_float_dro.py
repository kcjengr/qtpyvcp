"""
HAL float DRO
-------------

Label for displaying `float` HAL pin values.

Generated HAL Pins
++++++++++++++++++

========================= ========= =========
HAL Pin Name              Type      Direction
========================= ========= =========
qtpyvcp.float-dro.enable  float     in
qtpyvcp.float-dro.in      float     in
========================= ========= =========
"""

from qtpy.QtWidgets import QLabel
from qtpy.QtCore import Property

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalFloatDro(QLabel, HALWidget):
    """HAL float DRO"""
    def __init__(self, parent=None):
        super(HalFloatDro, self).__init__(parent)

        self._in_pin = None
        self._enable_pin = None
        self._format = "%6.4f"

        self.setValue(0)

    def setValue(self, value):
        self.setText(self._format % value)

    @Property(str)
    def numberFormat(self):
        return self._format

    @numberFormat.setter
    def numberFormat(self, fmt):
        self._format = fmt
        self.setValue(0)

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add float-dro.enable HAL pin
        self._enable_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add float-dro.in HAL pin
        self._in_pin = comp.addPin(obj_name + ".in", "float", "in")
        self.setValue(self._in_pin.value)
        self._in_pin.valueChanged.connect(self.setValue)
