"""
HAL LCD DRO
-------------

LCD DRO for displaying `float` or `s32` HAL pin values.

Generated HAL Pins
++++++++++++++++++

========================= ========= =========
HAL Pin Name              Type      Direction
========================= ========= =========
qtpyvcp.lcd-dro.in-i      s32       in
qtpyvcp.lcd-dro.in-f      float     in
========================= ========= =========
"""

from qtpy.QtWidgets import QLCDNumber
from qtpy.QtCore import Property

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalLcdDro(QLCDNumber, HALWidget):
    """HAL LCD DRO"""
    def __init__(self, parent=None):
        super(HalLcdDro, self).__init__(parent)

        self._in_pin = None
        self._enable_pin = None
        self._format = "%5.3f"

        self.setDigitCount(6)
        self.setSegmentStyle(QLCDNumber.Flat)

        self.setValue(0.0)

    def setValue(self, val):
        self.display(self._format % val)

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

        # add lcd-dro.in HAL pin
        self._in_pin = comp.addPin(obj_name + ".in-f", "float", "in")
        self.setValue(self._in_pin.value)
        self._in_pin.valueChanged.connect(self.setValue)

        # add lcd-dro.in HAL pin
        self._in_pin = comp.addPin(obj_name + ".in-i", "s32", "in")
        self.setValue(self._in_pin.value)
        self._in_pin.valueChanged.connect(self.setValue)
