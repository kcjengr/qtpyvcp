#!/usr/bin/python

from qtpy.QtCore import Qt, Slot, Property, QTimer, QSize
from qtpy.QtGui import QColor, QPainter, QRadialGradient, QBrush
from qtpy.QtWidgets import QWidget


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
                                   self._diameter * 0.3, self._diameter * 0.1, self._diameter * 0.1)
        gradient.setColorAt(0, Qt.white)

        # ensure the border/halo is same color as gradient
        draw_color = QColor(self._color)

        if not self._state:
            # cut to black @ 70% for darker effect
            draw_color = QColor(Qt.black)

        if not self.isEnabled():
            draw_color.setAlpha(30)

        pen_color = draw_color
        gradient.setColorAt(0.7, draw_color)

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

    @Slot(int)
    def setDiameter(self, value):
        self._diameter = value
        self.adjustSize()
        self.update()

    def getColor(self):
        return self._color

    @Slot(QColor)
    def setColor(self, value):
        self._color = value
        self._disabledColor = QColor(self._color)
        self._disabledColor.setAlpha(30)
        self.update()

    def getAlignment(self):
        return self._alignment

    @Slot(Qt.Alignment)
    def setAlignment(self, value):
        self._alignment = value
        self.update()

    def getState(self):
        return self._state

    @Slot(bool)
    def setState(self, value):
        self._state = value
        self.update()

    @Slot()
    def toggleState(self):
        self._state = not self._state
        self.update()

    def isFlashing(self):
        return self._flashing

    @Slot(bool)
    def setFlashing(self, value):
        self._flashing = value
        self.update()

    def getFlashRate(self):
        return self._flashRate

    @Slot(int)
    def setFlashRate(self, value):
        self._flashRate = value
        self.update()

    @Slot()
    def startFlashing(self):
        self.setFlashing(True)

    @Slot()
    def stopFlashing(self):
        self.setFlashing(False)

    diameter = Property(int, getDiameter, setDiameter)
    color = Property(QColor, getColor, setColor)
    alignment = Property(Qt.Alignment, getAlignment, setAlignment)
    state = Property(bool, getState, setState)
    flashing = Property(bool, isFlashing, setFlashing)
    flashRate = Property(int, getFlashRate, setFlashRate)

if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)
    led = LEDWidget()
    # led.setState(False)
    led.setColor(QColor('green'))
    led.setDiameter(16)
    led.show()
    sys.exit(app.exec_())
