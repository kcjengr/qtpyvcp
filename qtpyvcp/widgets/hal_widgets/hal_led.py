
from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget
from qtpyvcp.widgets.base_widgets.led_widget import LEDWidget

# Setup logging
from qtpyvcp.utilities.logger import getLogger
log = getLogger(__name__)


class HalLedIndicator(LEDWidget, HALWidget):
    """HAL LED

    LED for indicated the state of `bit` HAL pins.

    .. table:: Generated HAL Pins

        ========================= ========= =========
        HAL Pin Name              Type      Direction
        ========================= ========= =========
        qtpyvcp.led.on            bit       in
        qtpyvcp.led.flash         bit       in
        qtpyvcp.led.flash-rate    u32       out
        ========================= ========= =========
    """
    def __init__(self, parent=None):
        super(HalLedIndicator, self).__init__(parent)

        self._value_pin = None
        self._enabled_pin = None

    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add led.on HAL pin
        self._on_pin = comp.addPin(obj_name + ".on", "bit", "in")
        # self._on_pin.value = self.isO()
        self._on_pin.valueChanged.connect(lambda state: self.setState(state))

        # add led.flash HAL pin
        self._flash_pin = comp.addPin(obj_name + ".flash", "bit", "in")
        self._flash_pin.valueChanged.connect(lambda flash: self.setFlashing(flash))

        # add led.flash-rate HAL pin
        self._flash_rate_pin = comp.addPin(obj_name + ".flash-rate", "u32", "in")
        self._flash_rate_pin.valueChanged.connect(lambda rate: self.setFlashRate(rate))
