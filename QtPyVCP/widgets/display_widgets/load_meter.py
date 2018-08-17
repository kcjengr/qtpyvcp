#!/usr/bin/python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class LoadMeter(QProgressBar):
    """docstring for LoadMeter"""
    def __init__(self, parent=None):
        super(LoadMeter, self).__init__(parent)

    def paintEvent(self, event):

        val = self.value()
        pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), val, self.width())
        pos60 = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), 100, self.width())
        pos80 = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), 120, self.width())

        p = QPainter(self)
        p.setPen(Qt.blue)
        p.setBrush(QBrush(Qt.blue))

        if val >= 0 and val <= 100:
            p.drawRect(0, 0, pos, self.height())

        elif val > 90 and val <= 120:

            p.drawRect(0,0,pos60, self.height())
            p.setPen(Qt.yellow)
            p.setBrush(QBrush(Qt.yellow))
            p.drawRect(pos60, 0, pos - pos60, self.height())

        else:
            p.drawRect(0,0,pos60, self.height())
            p.setPen(Qt.yellow)
            p.setBrush(QBrush(Qt.yellow))
            p.drawRect(pos60, 0, pos80 - pos60, self.height())
            p.setPen(Qt.red)
            p.setBrush(QBrush(Qt.red))
            p.drawRect(pos80, 0, pos - pos80, self.height())

        p.setPen(QColor(235, 235, 238))
        p.setBrush(QBrush(QColor(235, 235, 238)))
        p.drawRect(pos, 0, self.width(), self.height())


        p.setPen(Qt.black)
        p.setBrush(QBrush(Qt.black))
        p.drawText(0,0, self.width(), self.height(), Qt.AlignCenter, str(val) + "%")


if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)
    w = LoadMeter()
    w.show()
    w.setValue(100)
    sys.exit(app.exec_())
