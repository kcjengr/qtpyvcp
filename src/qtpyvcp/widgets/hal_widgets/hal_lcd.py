from PySide6.QtWidgets import QLCDNumber
from PySide6.QtCore import Property

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget, VCPWidget


class HalLCDNumber(QLCDNumber, HALWidget, VCPWidget):
    """HAL LCD Number

    LCD Number for displaying `float` or `s32` HAL pin values.

    .. table:: Generated HAL Pins

        ===================== ========= =========
        HAL Pin Name          Type      Direction
        ===================== ========= =========
        qtpyvcp.lcd.in-i      s32       in
        qtpyvcp.lcd.in-f      float     in
        ===================== ========= =========
    """

    def __init__(self, parent=None):
        super(HalLCDNumber, self).__init__(parent)

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
        """Number Format Property

        Args:
            fmt (str) : A valid python style format string. Defaults to ``%i``.
        """
        return self._format

    @numberFormat.setter
    def numberFormat(self, fmt):
        self._format = fmt
        self.setValue(0)

    def initialize(self):
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

        # add lcd-dro.in HAL pin
        self._in_pin = comp.addPin(obj_name + ".in-f", "float", "in")
        self.setValue(self._in_pin.value)
        self._in_pin.valueChanged.connect(self.setValue)

        # add lcd-dro.in HAL pin
        self._in_pin = comp.addPin(obj_name + ".in-i", "s32", "in")
        self.setValue(self._in_pin.value)
        self._in_pin.valueChanged.connect(self.setValue)
