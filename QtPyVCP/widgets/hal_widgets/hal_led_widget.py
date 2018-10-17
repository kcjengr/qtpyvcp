#!/usr/bin/python

from qtpy.QtCore import Slot, Property

from qtpyvcp.widgets.base_widgets.led_widget import LEDWidget
from qtpyvcp.utilities.obj_status import HALStatus

# Setup logging
from qtpyvcp.utilities import logger
log = logger.getLogger(__name__)


class HalLedWidget(LEDWidget):

    # one to rule them all
    hal_status = HALStatus()

    def __init__(self, parent=None):
        super(HalLedWidget, self).__init__(parent)

        self._hal_pin = ''

    def getHalPin(self):
        return self._hal_pin

    @Slot(str)
    def setHalPin(self, hal_pin):
        self._hal_pin = hal_pin
        try:
            pin = self.hal_status.getHALPin(hal_pin)
        except ValueError as e:
            log.warning(e)
            return
        pin.valueChanged[bool].connect(self.setState)
        self.setState(pin.getValue())
        log.debug("HAL LED connected to yellow<{}>".format(hal_pin))

    hal_pin_name = Property(str, getHalPin, setHalPin)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    led = HalLedWidget()
    led.show()
    sys.exit(app.exec_())
