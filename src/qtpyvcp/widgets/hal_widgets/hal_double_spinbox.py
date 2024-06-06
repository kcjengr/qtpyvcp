

from PySide6.QtWidgets import QDoubleSpinBox
from PySide6.QtCore import QEvent

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin

LOG = getLogger(__name__)
STATUS = getPlugin('status')

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

    def mousePressEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept mouse Press Event')
            event.accept()
            return 
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if STATUS.isLocked():
            LOG.debug('Accept mouse Release Event')
            event.accept()
            return 
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept keyPressEvent Event')
            event.accept()
            return 
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept keyReleaseEvent Event')
            event.accept()
            return 
        super().keyReleaseEvent(event)

    def changeEvent(self, event):
        super(HalDoubleSpinBox, self).changeEvent(event)
        if event == QEvent.EnabledChange and self._enabled_pin is not None:
            self._enabled_pin.value = self.isEnabled()

    def onCheckedStateChanged(self, checked):
        if STATUS.isLocked():
            LOG.debug('Skip HAL onCheckedStateChanged')
            return 
        if self._value_pin is not None:
            self._value_pin.value = checked

    def initialize(self):
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

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
