from qtpy.QtCore import Qt, Property, Slot, QRectF, QSize
from qtpy.QtGui import QColor, QLinearGradient, QPainter, QPen
from qtpy.QtWidgets import QWidget, QSizePolicy, QWIDGETSIZE_MAX

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)


class BarIndicatorBase(QWidget):
    """docstring for BarIndicator"""
    def __init__(self, parent=None):
        super(BarIndicatorBase, self).__init__(parent)

        self._value = 100
        self._minimum = 0.0
        self._maximum = 100.0
        self._format = '{p}%'

        self._text_color = QColor(0, 0, 0)
        self._border_color = Qt.gray
        self._border_radius = 2
        self._border_width = 1

        self._painter = QPainter()

        self._orientation = Qt.Horizontal
        self._bar_width = self.height()
        self._bar_length = self.width()

        self._painter_rotation = None
        self._painter_translation_y = None
        self._painter_translation_x = None
        self._painter_scale_x = None
        self._flip_translation_y = None
        self._flip_scale_y = None

        self._inverted_appearance = False
        self._flip_scale = False
        self._origin_at_zero = False
        self._origin_position = 0

        self.barGradient = [u'0.0, 0, 255, 0',
                            u'0.8, 255, 255, 0',
                            u'1.0, 255, 0, 0',]

    def adjustTransformation(self):
        """This method sets parameters for the widget transformations (needed
        for orientation, flipping and appearance inversion).
        """
        if self._orientation == Qt.Horizontal:
            self._bar_width = self.height()
            self._bar_length = self.width()
            self._painter_translation_y = 0
            self._painter_rotation = 0

        elif self._orientation == Qt.Vertical:
            # Invert dimensions for paintEvent()
            self._bar_width = self.width()
            self._bar_length = self.height()
            self._painter_translation_y = self._bar_length
            self._painter_rotation = -90

        if self._inverted_appearance:
            self._painter_translation_x = self._bar_width
            self._painter_scale_x = -1
        else:
            self._painter_translation_x = 0
            self._painter_scale_x = 1

        if self._flip_scale:
            self._flip_translation_y = self._bar_length
            self._flip_scale_y = -1
        else:
            self._flip_translation_y = 0
            self._flip_scale_y = 1

    def paintEvent(self, event):

        self.adjustTransformation()
        self._painter.begin(self)
        self._painter.translate(0, self._painter_translation_y) # Draw vertically if needed
        self._painter.rotate(self._painter_rotation)
        self._painter.translate(self._painter_translation_x, 0) # Invert appearance if needed
        self._painter.scale(self._painter_scale_x, 1)

        self._painter.translate(0, self._flip_translation_y)    # Invert scale if needed
        self._painter.scale(1, self._flip_scale_y)

        self._painter.setRenderHint(QPainter.Antialiasing)

        self.drawBackground()

        if self._border_width > 0:
            self.drawBorder()

        if self._format is not '':
            self.drawText()

        self._painter.end()

    def drawBackground(self):

        bw = float(self._border_width)
        br = self._border_radius

        w = self.sliderPositionFromValue(self.minimum, self.maximum, self._value, self._bar_length)
        h = self._bar_width
        rect = QRectF(bw / 2, bw / 2, w - bw, h - bw)

        p = self._painter

        # draw the load meter value bar
        p.setPen(Qt.transparent)
        p.setBrush(self.gradient)

        p.drawRoundedRect(rect, br, br)

    def drawBorder(self):
        p = self._painter

        bw = float(self._border_width)
        br = self._border_radius

        p.setBrush(Qt.transparent)
        border_pen = QPen()
        border_pen.setWidth(bw)
        border_pen.setColor(self._border_color)
        p.setPen(border_pen)

        # deal with orientation
        if self._orientation == Qt.Horizontal:
            rect = QRectF(bw / 2, bw / 2, self.width() - bw, self.height() - bw)
        else:
            # must be Qt.Vertical
            rect = QRectF(bw / 2, bw / 2, self.height() - bw, self.width() - bw)

        p.drawRoundedRect(rect, br, br)

    def drawText(self):
        p = self._painter

        # draw the load percentage text
        p.setPen(self._text_color)
        if self.orientation == Qt.Vertical:
            p.drawText(0, 0, self.height(), self.width(), Qt.AlignCenter, self.text())
        else:
            p.drawText(0, 0, self.width(), self.height(), Qt.AlignCenter, self.text())

    def minimumSizeHint(self):
        return QSize(30, 30)

    def resizeEvent(self, event):
        if self._orientation == Qt.Horizontal:
            self.gradient.setStart(0, 0)
            self.gradient.setFinalStop(self.width(), 0)
        else:
            self.gradient.setStart(0, 0)
            self.gradient.setFinalStop(self.height(), 0)

    def sliderPositionFromValue(self, min, max, val, span, upsideDown=False):
        return span * (val / max - min)

    @Slot(int)
    @Slot(float)
    @Slot(object)
    def setValue(self, val):
        self.value = val

    @Slot(int)
    @Slot(float)
    def setMinimum(self, min):
        self.minimum = min

    @Slot(int)
    @Slot(float)
    def setMaximum(self, max):
        self.maximum = max

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
        self.update()

    @Property(Qt.Orientation)
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, orient):
        if orient == self._orientation:
            return

        self._orientation = orient
        self.adjustTransformation()
        self.update()

    def text(self):
        values = {'v': self._value,
                  'p': int((self._value * 100 / self._maximum) + .5)}
        try:
            return self.format.encode("utf-8").format(**values)
        except:
            return self.format

    # ToDo: Make this a QLinearGradient
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
    w = BarIndicatorBase()
    #w.orientation = Qt.Vertical
    w.show()
    w.setValue(65)
    sys.exit(app.exec_())
