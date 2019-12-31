
from qtpy.QtWidgets import QGroupBox

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalGroupBox(QGroupBox, HALWidget):
    """HAL GroupBox

    GroupBox that can be enabled/disabled via HAL pins.

    .. table:: Generated HAL Pins

        ========================= ===== =========
        HAL Pin Name              Type  Direction
        ========================= ===== =========
        qtpyvcp.group-box.enable   bit   in
        qtpyvcp.group-box.check    bit   in
        qtpyvcp.group-box.checked  bit   out
        ========================= ===== =========
    """

    def __init__(self, parent=None):
        super(HalGroupBox, self).__init__(parent)

        self._enable_pin = None
        self._check_pin = None
        self._checked_pin = None

        self.toggled.connect(self.onCheckedStateChanged)

    def onCheckedStateChanged(self, checked):
        if self._checked_pin is not None:
            self._checked_pin.value = checked

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add group-box.enable HAL pin
        self._enable_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        if self.isCheckable():
            # add group-box.check HAL pin
            self._check_pin = comp.addPin(obj_name + ".check", "bit", "in")
            self._check_pin.value = self.isChecked()
            self._check_pin.valueChanged.connect(self.setChecked)

            # add group-box.checked HAL pin
            self._checked_pin = comp.addPin(obj_name + ".checked", "bit", "out")
            self._checked_pin.value = self.isChecked()
