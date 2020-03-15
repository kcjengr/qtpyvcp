from qtpy.QtCore import Qt, Property, QRectF, QSize
from qtpy.QtGui import QColor, QLinearGradient, QPainter, QPen
from qtpy.QtWidgets import QWidget, QSizePolicy

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)


class BarIndicator(QWidget):
    """docstring for BarIndicator"""
    def __init__(self, parent=None):
        super(BarIndicator, self).__init__(parent)

        self._value = 100
        self._minimum = 0.0
        self._maximum = 100.0
        self._format = '{p}%'
        self._orientation = Qt.Horizontal

        self._text_color = QColor(0, 0, 0)
        self._border_color = Qt.gray
        self._border_radius = 2
        self._border_width = 1

        self.barGradient = [u'0.0, 0, 255, 0',
                            u'0.8, 255, 255, 0',
                            u'1.0, 255, 0, 0',]

    def paintEvent(self, event):

        bw = float(self._border_width)
        br = self._border_radius

        val = self.value
        if self._orientation == Qt.Horizontal:
            w = self.sliderPositionFromValue(self.minimum, self.maximum, val, self.width())
            h = self.height()
            rect = QRectF(bw / 2, bw / 2, w - bw, h - bw)
        else:
            h = self.sliderPositionFromValue(self.minimum, self.maximum, val, self.height())
            rect = QRectF(0, self.height(), self.width(), - h)

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # draw the load meter value bar
        p.setPen(Qt.transparent)
        p.setBrush(self.gradient)
        p.drawRoundedRect(rect, br, br)

        # draw the border
        p.setBrush(Qt.transparent)
        border_pen = QPen()
        border_pen.setWidth(bw)
        border_pen.setColor(self._border_color)
        p.setPen(border_pen)
        rect = QRectF(bw / 2, bw / 2, self.width() - bw, self.height() - bw)
        p.drawRoundedRect(rect, br, br)

        # draw the load percentage text
        p.setPen(self._text_color)
        if self.orientation == Qt.Vertical:
            p.rotate(-90)
            p.drawText(-self.height(), 0, self.height(), self.width(), Qt.AlignCenter, self.text())
        else:
            p.drawText(0,0, self.width(), self.height(), Qt.AlignCenter, self.text())

    def minimumSizeHint(self):
        return QSize(30, 30)

    def resizeEvent(self, event):
        if self._orientation == Qt.Horizontal:
            self.gradient.setStart(0, 0)
            self.gradient.setFinalStop(self.width(), 0)
        else:
            self.gradient.setStart(0, self.height())
            self.gradient.setFinalStop(0, 0)

    def sliderPositionFromValue(self, min, max, val, span, upsideDown=False):
        return span * (val / max - min)

    def setValue(self, val):
        self.value = val

    @Property(float)
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value >= self.minimum and value <= self.maximum:
            self._value = value
            self.update()

    @Property(float)
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, min_val):
        self._minimum = min_val
        self.update()

    @Property(float)
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, max_val):
        self._maximum = max_val
        self.update()

    @Property(str)
    def format(self):
        return self._format

    @format.setter
    def format(self, fmt):
        self._format = fmt

    @Property(Qt.Orientation)
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, orient):
        if orient == self._orientation:
            return

        if orient == Qt.Horizontal:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        else:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self._orientation = orient
        self.update()

    def text(self):
        values = {'v': self._value,
                  'p': int((self._value * 100 / self._maximum) + .5)}
        try:
            return self.format.encode("utf-8").format(**values)
        except:
            return self.format

    # border width
    @Property('QStringList')
    def barGradient(self):
        return self._gradient_def

    @barGradient.setter
    def barGradient(self, gradient):
        grad = QLinearGradient(0, 0, 0, 0)
        try:
            for stop in gradient:
                pos, r, g, b = stop.split(',')[:4]
                color = QColor(int(r), int(g), int(b))
                grad.setColorAt(float(pos), color)
        except:
            LOG.exception('Invalid gradient.')
            return

        self._gradient_def = gradient
        self.gradient = grad
        self.resizeEvent(None)
        self.update()

    # text color
    @Property(QColor)
    def textColor(self):
        return self._text_color

    @textColor.setter
    def textColor(self, text_color):
        self._text_color = text_color
        self.update()

    # border color
    @Property(QColor)
    def borderColor(self):
        return self._border_color

    @borderColor.setter
    def borderColor(self, border_color):
        self._border_color = border_color
        self.update()

    # border radius
    @Property(int)
    def borderRadius(self):
        return self._border_radius

    @borderRadius.setter
    def borderRadius(self, border_radius):
        self._border_radius = border_radius
        self.update()

    # border width
    @Property(int)
    def borderWidth(self):
        return self._border_width

    @borderWidth.setter
    def borderWidth(self, border_width):
        self._border_width = border_width
        self.update()


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = BarIndicator()
    w.show()
    w.setValue(65)
    sys.exit(app.exec_())
