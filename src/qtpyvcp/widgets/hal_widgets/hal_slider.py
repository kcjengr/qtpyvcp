import os

from PySide6.QtWidgets import QSlider

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget, VCPWidget

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin

IN_DESIGNER = os.getenv('DESIGNER', False)

LOG = getLogger(__name__)
STATUS = getPlugin('status')

class HalSlider(QSlider, HALWidget, VCPWidget):
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
        
        if not IN_DESIGNER:
            self.valueChanged.connect(self.onValueChanged)

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

    def onValueChanged(self, val):
        if self._s32_value_pin is not None:
            self._s32_value_pin.value = val
            self._float_value_pin.value = val / 100.0

    def mouseDoubleClickEvent(self, event):
        if STATUS.isLocked():
            LOG.debug('Skip HAL mouseDoubleClickEvent')
            return 
        self.setValue(100)

    def initialize(self):
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

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

