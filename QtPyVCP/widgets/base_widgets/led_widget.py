#!/usr/bin/python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class LEDWidget(QWidget):

    def __init__(self, parent=None):

        super(LEDWidget, self).__init__(parent)

        self._diamX = 0
        self._diamY = 0
        self._diameter = 30
        self._color = QColor("red")
        self._alignment = Qt.AlignCenter
        self._state = True
        self._flashing = False
        self._flashRate = 200

        self._timer = QTimer()
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

        gradient = QRadialGradient(x + self._diameter / 2, y + self._diameter / 2,
                                   self._diameter * 0.3, self._diameter * 0, self._diameter * 0)
        gradient.setColorAt(0, Qt.white)

        # ensure the border/halo is same color as gradient
        pen_color = self._color;
        if self._state:
            gradient.setColorAt(1, self._color)
        else:
            # cut to black @ 75% for darker effect
            gradient.setColorAt(.70, Qt.black)
            pen_color = Qt.black

        painter.begin(self)
        brush = QBrush(gradient)
        painter.setPen(pen_color)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(brush)
        painter.drawEllipse(x + 1, y + 1, self._diameter - 2, self._diameter - 2)

        if self._flashRate > 0 and self._flashing:
            self._timer.start(self._flashRate)
        else:
            self._timer.stop()

        painter.end()

    def minimumSizeHint(self):
        return QSize(self._diameter, self._diameter)

    def sizeHint(self):
        return QSize(self._diameter, self._diameter)

    def getDiameter(self):
        return self._diameter

    @pyqtSlot(int)
    def setDiameter(self, value):
        self._diameter = value
        self.update()

    def getColor(self):
        return self._color

    @pyqtSlot(QColor)
    def setColor(self, value):
        self._color = value
        self.update()

    def getAlignment(self):
        return self._alignment

    @pyqtSlot(Qt.Alignment)
    def setAlignment(self, value):
        self._alignment = value
        self.update()

    def getState(self):
        return self._state

    @pyqtSlot(bool)
    def setState(self, value):
        self._state = value
        self.update()

    @pyqtSlot()
    def toggleState(self):
        self._state = not self._state
        self.update()

    def isFlashing(self):
        return self._flashing

    @pyqtSlot(bool)
    def setFlashing(self, value):
        self._flashing = value
        self.update()

    def getFlashRate(self):
        return self._flashRate

    @pyqtSlot(int)
    def setFlashRate(self, value):
        self._flashRate = value
        self.update()

    @pyqtSlot()
    def startFlashing(self):
        self.setFlashing(True)

    @pyqtSlot()
    def stopFlashing(self):
        self.setFlashing(False)

    diameter = pyqtProperty(int, getDiameter, setDiameter)
    color = pyqtProperty(QColor, getColor, setColor)
    alignment = pyqtProperty(Qt.Alignment, getAlignment, setAlignment)
    state = pyqtProperty(bool, getState, setState)
    flashing = pyqtProperty(bool, isFlashing, setFlashing)
    flashRate = pyqtProperty(int, getFlashRate, setFlashRate)

if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)
    led = LEDWidget()
    led.setState(False)
    led.setColor(QColor('green'))
    led.setDiameter(16)
    led.show()
    sys.exit(app.exec_())
