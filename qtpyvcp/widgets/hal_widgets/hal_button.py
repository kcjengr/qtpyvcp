
from qtpy.QtCore import Property, QTimer
from qtpy.QtWidgets import QPushButton

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget


class HalButton(QPushButton, HALWidget):
    """HAL Button

    Button for setting `bit` HAL pin values.

    .. table:: Generated HAL Pins

        ========================= ===== =========
        HAL Pin Name              Type  Direction
        ========================= ===== =========
        qtpyvcp.button.enable     bit   in
        qtpyvcp.button.out        bit   out
        ========================= ===== =========
    """
    def __init__(self, parent=None):
        super(HalButton, self).__init__(parent)

        self.setText("HAL Button")

        self._enable_pin = None
        self._pressed_pin = None
        self._checked_pin = None

        self._pulse = False
        self._pulse_duration = 100
        self.pulse_timer = None

        self.pressed.connect(self.onPress)
        self.released.connect(self.onRelease)
        self.toggled.connect(self.onCheckedStateChanged)

    def onPress(self):
        if self._pressed_pin is not None:
            self._pressed_pin.value = True
        if self._pulse:
            self.pulse_timer.start(self._pulse_duration)

    def onRelease(self):
        if self._pressed_pin is not None:
            self._pressed_pin.value = False

    def onCheckedStateChanged(self, checked):
        if self._checked_pin is not None:
            self._checked_pin.value = checked

    @Property(bool)
    def pulseOnPress(self):
        """If active, when the button is pressed the ``out`` pin will be `True`
        for :class:`.pulseDuration` ms, otherwise the ``out`` pin will
        be `True` for the duration of the button press.
        """
        return self._pulse

    @pulseOnPress.setter
    def pulseOnPress(self, pulse):
        self._pulse = pulse

    @Property(int)
    def pulseDuration(self):
        """Pulse duration in ms used when :class:`.pulseOnPress` is active."""
        return self._pulse_duration

    @pulseDuration.setter
    def pulseDuration(self, duration):
        self._pulse_duration = duration

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add button.enable HAL pin
        self._enable_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add button.out HAL pin
        self._pressed_pin = comp.addPin(obj_name + ".out", "bit", "out")

        # add checkbox.checked HAL pin
        self._checked_pin = comp.addPin(obj_name + ".checked", "bit", "out")
        self._checked_pin.value = self.isChecked()

        if self._pulse:
            self.pulse_timer = QTimer()
            self.pulse_timer.setSingleShot(True)
            self.pulse_timer.timeout.connect(self.onRelease)
