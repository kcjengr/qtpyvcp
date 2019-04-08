"""
HAL CheckBox
------------

CheckBox used for displaying and setting BIT HAL pin values.

Generates two I/O pins, ``qtpyvcp.checkbox-name.enabled`` which indicates
if the checkbox is enabled, and ``qtpyvcp.checkbox-name.checked`` which
indicates if the checkbox is checked.
"""

from qtpy.QtWidgets import QCheckBox
from qtpy.QtCore import Property, QEvent

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalCheckBox(QCheckBox, HALWidget):
    """HAL CheckBox"""
    def __init__(self, parent=None, pin_name=None):
        super(HalCheckBox, self).__init__(parent)

        self._enabled_pin = None
        self._checked_pin = None

        self.toggled.connect(self.onCheckedStateChanged)

    def changeEvent(self, event):
        super(HalCheckBox, self).changeEvent(event)
        if event == QEvent.EnabledChange and self._enabled_pin is not None:
            print "enabled changed:", self.isEnabled()
            self._enabled_pin.value = self.isEnabled()

    def onCheckedStateChanged(self, checked):
        print "checked changed:", checked
        if self._checked_pin is not None:
            self._checked_pin.value = checked

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add checkbox.enabled HAL pin
        self._enabled_pin = comp.addPin(obj_name + ".enabled", "bit", "io")
        self._enabled_pin.value = self.isEnabled()
        self._enabled_pin.valueChanged.connect(lambda enable: self.setEnabled(enable))

        # add checkbox.checked HAL pin
        self._checked_pin = comp.addPin(obj_name + ".checked", "bit", "io")
        self._checked_pin.value = self.isChecked()
        self._checked_pin.valueChanged.connect(lambda check: self.setChecked(check))
