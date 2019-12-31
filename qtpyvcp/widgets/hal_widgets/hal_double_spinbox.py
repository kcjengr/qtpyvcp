

from qtpy.QtWidgets import QDoubleSpinBox
from qtpy.QtCore import QEvent

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalDoubleSpinBox(QDoubleSpinBox, HALWidget):
    """HAL DoubleSpinBox

    DoubleSpinBox for displaying and setting `float` HAL pin values.

    .. table:: Generated HAL Pins

        ========================= ========= =========
        HAL Pin Name              Type      Direction
        ========================= ========= =========
        qtpyvcp.spinbox.enable    bit       in
        qtpyvcp.spinbox.in        float     in
        qtpyvcp.spinbox.out       float     out
        ========================= ========= =========
    """
    def __init__(self, parent=None):
        super(HalDoubleSpinBox, self).__init__(parent)

        self._value_pin = None
        self._enabled_pin = None

        self._signed_int = True

        self.valueChanged.connect(self.onCheckedStateChanged)

    def changeEvent(self, event):
        super(HalDoubleSpinBox, self).changeEvent(event)
        if event == QEvent.EnabledChange and self._enabled_pin is not None:
            self._enabled_pin.value = self.isEnabled()

    def onCheckedStateChanged(self, checked):
        if self._value_pin is not None:
            self._value_pin.value = checked

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add spinbox.enabled HAL pin
        self._enabled_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enabled_pin.value = self.isEnabled()
        self._enabled_pin.valueChanged.connect(self.setEnabled)

        # add spinbox.checked HAL pin
        self._value_pin = comp.addPin(obj_name + ".out", "float", "out")
        self._value_pin.value = self.value()

        # add spinbox.checked HAL pin
        self._set_value_pin = comp.addPin(obj_name + ".in", "float", "in")
        self._set_value_pin.valueChanged.connect(self.setValue)
