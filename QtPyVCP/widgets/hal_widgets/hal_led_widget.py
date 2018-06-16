#!/usr/bin/python2

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from QtPyVCP.widgets.base_widgets.led_widget import LEDWidget


class HalLedWidget(LEDWidget):
    def __init__(self, parent=None):
        super(HalLedWidget, self).__init__(parent)



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    led = LEDWidget()
    led.show()
    sys.exit(app.exec_())
