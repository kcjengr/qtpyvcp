#!/usr/bin/python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import time

class LoadMeter(QProgressBar):
    """docstring for LoadMeter"""
    def __init__(self, parent=None):
        super(LoadMeter, self).__init__(parent)

        self.gradient = self.makeGradient()

    def makeGradient(self):
        g = QLinearGradient(0, 0, self.width(), self.height())
        # g.setColorAt(0, Qt.green)
        # g.setColorAt(.8, Qt.yellow)
        # g.setColorAt(1, Qt.red)

        g.setColorAt(0, QColor(85, 117, 197))
        g.setColorAt(0.39, QColor(130, 159, 210))
        g.setColorAt(0.46, QColor(150, 177, 215))
        g.setColorAt(0.5, QColor(169, 195, 220))
        g.setColorAt(0.55, QColor(207, 224, 202))
        g.setColorAt(0.60, QColor(249, 255, 180))

        g.setColorAt(0.70, QColor(254, 162, 55))
        g.setColorAt(.8, QColor(254, 162, 55))

        g.setColorAt(.9, QColor(231, 87, 29))
        g.setColorAt(1, QColor(204, 0, 0))

        return g

    def paintEvent(self, event):

        val = self.value()
        pos = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), val, self.width())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing);

        # draw the load meter value bar
        p.setPen(Qt.transparent)
        self.gradient.setFinalStop(self.width(), self.height())
        p.setBrush(self.gradient)
        rect = QRectF(.5, .5, pos - 1, self.height() - 1)
        p.drawRoundedRect(rect, 2.0, 2.0)

        # draw the border
        p.setBrush(Qt.transparent)
        border_pen = QPen()
        border_pen.setWidth(1)
        border_pen.setColor(Qt.gray)
        p.setPen(border_pen)
        rect = QRectF(.5, .5, self.width() - 1, self.height() - 1)
        p.drawRoundedRect(rect, 2.0, 2.0)

        # draw the load percentage text
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
