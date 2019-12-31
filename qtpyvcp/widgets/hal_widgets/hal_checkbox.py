

from qtpy.QtWidgets import QCheckBox
from qtpy.QtCore import Property, QEvent

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalCheckBox(QCheckBox, HALWidget):
    """HAL CheckBox

    CheckBox for displaying and setting `bit` HAL pin values.

    .. table:: Generated HAL Pins

        ========================= ===== =========
        HAL Pin Name              Type  Direction
        ========================= ===== =========
        qtpyvcp.checkbox.enable   bit   in
        qtpyvcp.checkbox.check    bit   in
        qtpyvcp.checkbox.checked  bit   out
        ========================= ===== =========
    """
    def __init__(self, parent=None):
        super(HalCheckBox, self).__init__(parent)

        self._enable_pin = None
        self._check_pin = None
        self._checked_pin = None

        self.toggled.connect(self.onCheckedStateChanged)

    def changeEvent(self, event):
        super(HalCheckBox, self).changeEvent(event)
        if event == QEvent.EnabledChange and self._enable_pin is not None:
            self._enable_pin.value = self.isEnabled()

    def onCheckedStateChanged(self, checked):
        if self._checked_pin is not None:
            self._checked_pin.value = checked

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add checkbox.enable HAL pin
        self._enable_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add checkbox.check HAL pin
        self._check_pin = comp.addPin(obj_name + ".check", "bit", "in")
        self._check_pin.value = self.isChecked()
        self._check_pin.valueChanged.connect(self.setChecked)

        # add checkbox.checked HAL pin
        self._checked_pin = comp.addPin(obj_name + ".checked", "bit", "out")
        self._checked_pin.value = self.isChecked()
