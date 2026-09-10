
from PySide6.QtCore import Property, QTimer
from PySide6.QtWidgets import QPushButton

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget, VCPWidget

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin


LOG = getLogger(__name__)
STATUS = getPlugin('status')


class HalButton(QPushButton, HALWidget, VCPWidget):
    """HAL Button

    Button for setting `bit` HAL pin values.

    .. table:: Generated HAL Pins

        ========================= ===== =========
        HAL Pin Name              Type  Direction
        ========================= ===== =========
        qtpyvcp.button.enable     bit   in
        qtpyvcp.button.out        bit   out
        qtpyvcp.button.checked    bit   out
        qtpyvcp.button.io         bit   io
        ========================= ===== =========

    .. note::

        The `qtpyvcp.button.checked` halpin is only present if the :class:`.checkable` property is set to true.

    """
    def __init__(self, parent=None):
        super(HalButton, self).__init__(parent)

        self.setText("HAL Button")

        self._enable_pin = None
        self._pressed_pin = None
        self._checked_pin = None
        self._activated_pin = None

        self._pulse = False
        self._pulse_duration = 100
        self.pulse_timer = None

        # Flash-while-checked. The checked state itself is never touched --
        # toggling it would fight the .check HAL pin and re-emit toggled --
        # so a `flashState` dynamic property is alternated instead and the
        # stylesheet selects on it.
        self._flash_on_checked = False
        self._flash_rate = 500
        self._flash_state = True
        self._flash_timer = QTimer(self)
        self._flash_timer.setInterval(self._flash_rate)
        self._flash_timer.timeout.connect(self._toggleFlashState)

        self.pressed.connect(self.onPress)
        self.released.connect(self.onRelease)
        self.toggled.connect(self.onCheckedStateChanged)
        self.toggled.connect(self._updateFlashing)

        self._setFlashState(True)

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


    def onPress(self):
        if self._pressed_pin is not None:
            self._pressed_pin.value = True
        if self._activated_pin is not None:
            self._activated_pin.value = True
        if self._pulse:
            self.pulse_timer.start(self._pulse_duration)

    def onRelease(self):
        if self._pressed_pin is not None:
            self._pressed_pin.value = False
        if self._activated_pin is not None:
            self._activated_pin.value = False

    def onCheckedStateChanged(self, checked):
        if STATUS.isLocked():
            LOG.debug('Skip HAL onCheckedStateChanged')
            return 
        if self._checked_pin is not None:
            self._checked_pin.value = checked

    # ------------------------------------------------------------ flashing

    def _setFlashState(self, on):
        """Set the `flashState` dynamic property and repolish.

        Qt only re-evaluates a stylesheet against a dynamic property when the
        widget is unpolished and polished again, so that has to be explicit.
        """
        self._flash_state = bool(on)
        self.setProperty('flashState', 'true' if on else 'false')
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)

    def _toggleFlashState(self):
        self._setFlashState(not self._flash_state)

    def _updateFlashing(self, checked=None):
        """Run the timer only while checked and flashing is enabled, and
        always leave the widget on flashState=true so a stopped flash is
        never left mid-blink."""
        if checked is None:
            checked = self.isChecked()
        if checked and self._flash_on_checked:
            self._setFlashState(True)
            self._flash_timer.start(self._flash_rate)
        else:
            self._flash_timer.stop()
            self._setFlashState(True)

    @Property(bool)
    def flashOnChecked(self):
        """Flash the button while it is checked.

        Alternates the `flashState` dynamic property between `true` and
        `false`. Style both in the stylesheet, e.g.::

            QPushButton:checked[flashState="true"]  { background: red; }
            QPushButton:checked[flashState="false"] { background: green; }

        Returns:
            bool
        """
        return self._flash_on_checked

    @flashOnChecked.setter
    def flashOnChecked(self, flash):
        self._flash_on_checked = bool(flash)
        self._updateFlashing()

    @Property(int)
    def flashRate(self):
        """Flash half-period in milliseconds. Default 500.

        Returns:
            int
        """
        return self._flash_rate

    @flashRate.setter
    def flashRate(self, rate):
        self._flash_rate = max(50, int(rate))
        self._flash_timer.setInterval(self._flash_rate)
        if self._flash_timer.isActive():
            self._flash_timer.start(self._flash_rate)

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
        comp = hal.getComponent()
        obj_name = self.getPinBaseName()

        # add button.enable HAL pin
        self._enable_pin = comp.addPin(obj_name + ".enable", "bit", "in")
        self._enable_pin.value = self.isEnabled()
        self._enable_pin.valueChanged.connect(self.setEnabled)

        # add button.out HAL pin
        self._pressed_pin = comp.addPin(obj_name + ".out", "bit", "out")
        
        # add button.activated HAL pin
        self._activated_pin = comp.addPin(obj_name + ".io", "bit", "io")
        self._activated_pin.value = self.isDown()
        self._activated_pin.valueChanged.connect(self.setDown)

        if self.isCheckable():
            # add button.check HAL pin -- lets HAL drive the checked state,
            # matching HalCheckBox and HalGroupBox. .checked is an output and
            # cannot be written to, so without this nothing in HAL can set the
            # button's appearance.
            self._check_pin = comp.addPin(obj_name + ".check", "bit", "in")
            self._check_pin.value = self.isChecked()
            self._check_pin.valueChanged.connect(self.setChecked)

            # add button.checked HAL pin
            self._checked_pin = comp.addPin(obj_name + ".checked", "bit", "out")
            self._checked_pin.value = self.isChecked()

        if self._pulse:
            self.pulse_timer = QTimer()
            self.pulse_timer.setSingleShot(True)
            self.pulse_timer.timeout.connect(self.onRelease)

