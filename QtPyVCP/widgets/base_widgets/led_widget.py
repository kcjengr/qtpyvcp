#!/usr/bin/python

from PyQt5 import Qt

class LEDWidget(Qt.QWidget):

    def __init__(self, parent=None):

        super(LEDWidget, self).__init__(parent)

        self._diamX = 0
        self._diamY = 0
        self._diameter = 30
        self._color = Qt.QColor("red")
        self._alignment = Qt.Qt.AlignCenter
        self._state = True
        self._flashing = False
        self._flashRate = 200

        self._timer = Qt.QTimer()
        self._timer.timeout.connect(self.toggleState)

        self.setDiameter(self._diameter)

    def paintEvent(self, event):
        painter = QPainter()
        x = 0
        y = 0
        if self._alignment & Qt.AlignLeft:
            x = 0
        elif self._alignment & Qt.AlignRight:
            x = self.width() - self._diameter
        elif self._alignment & Qt.AlignHCenter:
            x = (self.width() - self._diameter) / 2
        elif self._alignment & Qt.AlignJustify:
            x = 0

        if self._alignment & Qt.AlignTop:
            y = 0
        elif self._alignment & Qt.AlignBottom:
            y = self.height() - self._diameter
        elif self._alignment & Qt.AlignVCenter:
            y = (self.height() - self._diameter) / 2

        gradient = Qt.QRadialGradient(x + self._diameter / 2, y + self._diameter / 2,
                                   self._diameter * 0.4, self._diameter * 0.4, self._diameter * 0.4)
        gradient.setColorAt(0, Qt.white)

        if self._state:
            gradient.setColorAt(1, self._color)
        else:
            gradient.setColorAt(1, Qt.black)

        painter.begin(self)
        brush = Qt.QBrush(gradient)
        painter.setPen(self._color)
        painter.setRenderHint(Qt.QPainter.Antialiasing, True)
        painter.setBrush(brush)
        painter.drawEllipse(x + 1, y + 1, self._diameter - 2, self._diameter - 2)

        if self._flashRate > 0 and self._flashing:
            self._timer.start(self._flashRate)
        else:
            self._timer.stop()

        painter.end()

    def minimumSizeHint(self):
        return Qt.QSize(self._diameter, self._diameter)

    def sizeHint(self):
        return Qt.QSize(self._diameter, self._diameter)

    def getDiameter(self):
        return self._diameter

    @Qt.pyqtSlot(int)
    def setDiameter(self, value):
        self._diameter = value
        self.update()

    def getColor(self):
        return self._color

    @Qt.pyqtSlot(Qt.QColor)
    def setColor(self, value):
        self._color = value
        self.update()

    def getAlignment(self):
        return self._alignment

    @Qt.pyqtSlot(Qt.Qt.Alignment)
    def setAlignment(self, value):
        self._alignment = value
        self.update()

    def getState(self):
        return self._state

    @Qt.pyqtSlot(bool)
    def setState(self, value):
        self._state = value
        self.update()

    @Qt.pyqtSlot()
    def toggleState(self):
        self._state = not self._state
        self.update()

    def isFlashing(self):
        return self._flashing

    @Qt.pyqtSlot(bool)
    def setFlashing(self, value):
        self._flashing = value
        self.update()

    def getFlashRate(self):
        return self._flashRate

    @Qt.pyqtSlot(int)
    def setFlashRate(self, value):
        self._flashRate = value
        self.update()

    @Qt.pyqtSlot()
    def startFlashing(self):
        self.setFlashing(True)

    @Qt.pyqtSlot()
    def stopFlashing(self):
        self.setFlashing(False)

    diameter = Qt.pyqtProperty(int, getDiameter, setDiameter)
    color = Qt.pyqtProperty(Qt.QColor, getColor, setColor)
    alignment = Qt.pyqtProperty(Qt.Qt.Alignment, getAlignment, setAlignment)
    state = Qt.pyqtProperty(bool, getState, setState)
    flashing = Qt.pyqtProperty(bool, isFlashing, setFlashing)
    flashRate = Qt.pyqtProperty(int, getFlashRate, setFlashRate)

if __name__ == "__main__":
    import sys
    app = Qt.QApplication(sys.argv)
    led = LEDWidget()
    led.show()
    sys.exit(app.exec_())
