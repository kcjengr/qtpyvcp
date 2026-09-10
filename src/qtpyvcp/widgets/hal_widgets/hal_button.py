
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

        # Flash-while-checked. The mechanism is on VCPBaseWidget; this is
        # only the trigger. The checked state itself is never toggled --
        # that would fight the .check HAL pin and re-emit toggled.
        self._flash_on_checked = False

        self.pressed.connect(self.onPress)
        self.released.connect(self.onRelease)
        self.toggled.connect(self.onCheckedStateChanged)
        self.toggled.connect(self._updateFlashing)

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
    #
    # The flash mechanism itself lives on VCPBaseWidget so every widget can
    # use it, driven either by a rule or directly. This only adds the
    # checked-state trigger, which is specific to a button.

    def _updateFlashing(self, checked=None):
        if checked is None:
            checked = self.isChecked()
        self.setFlashing(bool(checked) and self._flash_on_checked)

    @Property(bool)
    def flashOnChecked(self):
        """Flash the button while it is checked.

        Alternates the `flashState` dynamic property between `true` and
        `false`. Style both, e.g.::

            QPushButton:checked[flashState="true"]  { background: red; }
            QPushButton:checked[flashState="false"] { background: yellow; }

        Returns:
            bool
        """
        return self._flash_on_checked

    @flashOnChecked.setter
    def flashOnChecked(self, flash):
        self._flash_on_checked = bool(flash)
        self._updateFlashing()

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

