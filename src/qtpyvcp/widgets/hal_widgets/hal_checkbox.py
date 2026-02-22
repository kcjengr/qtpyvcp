import os

from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Property, QEvent

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget, VCPWidget

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin

LOG = getLogger(__name__)
STATUS = getPlugin('status')

IN_DESIGNER = os.getenv('DESIGNER', False)

class HalCheckBox(QCheckBox, HALWidget, VCPWidget):
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
        if not IN_DESIGNER:
            self.toggled.connect(self.onCheckedStateChanged)

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
        super(HalCheckBox, self).changeEvent(event)
        if event == QEvent.EnabledChange and self._enable_pin is not None:
            self._enable_pin.value = self.isEnabled()

    def onCheckedStateChanged(self, checked):
        if STATUS.isLocked():
            LOG.debug('Skip HAL onCheckedStateChanged')
            return 
        if self._checked_pin is not None:
            self._checked_pin.value = checked

    def initialize(self):
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

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
