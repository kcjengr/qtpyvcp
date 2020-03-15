import os
import sys
import cv2

from qtpy.QtGui import QImage, QPixmap, QPainter, QPen
from qtpy.QtCore import Qt, QSize, QTimer
from qtpy.QtWidgets import QLabel

from qtpyvcp.widgets import VCPWidget

IN_DESIGNER = os.getenv('DESIGNER', False)


class OpenCVWidget(QLabel):

    def __init__(self, parent=None):
        super(OpenCVWidget, self).__init__(parent)

        self.video_size = QSize(320, 240)

        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        if not IN_DESIGNER:
            self.setup_camera()

    def setup_camera(self):
        """Initialize camera.
        """
        self.capture = cv2.VideoCapture('/dev/video0')

        w = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.video_size = QSize(w, h)

        self.setScaledContents(True)
        self.setMinimumSize(w, h)

        self.timer = QTimer()
        self.timer.timeout.connect(self.display_video_stream)
        self.timer.start(30)

    def minimumSizeHint(self):
        return self.video_size

    def timerEvent(self, QTimerEvent):
        print "hello"

    def display_video_stream(self):
        """Read frame from camera and repaint QLabel widget.
        """
        result, frame = self.capture.read()

        if result is True:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)
            image = QImage(frame, frame.shape[1], frame.shape[0],
                           frame.strides[0], QImage.Format_RGB888)

            image = self.draw_crosshairs(image)

            self.setPixmap(QPixmap.fromImage(image))

    def draw_crosshairs(self, image):
        pen = QPen()
        painter = QPainter(image)
        pen.setWidth(1)
        pen.setColor(Qt.yellow)
        painter.setPen(pen)

        w = self.video_size.width()
        h = self.video_size.height()

        painter.drawLine(w / 2, 0, w / 2, h)
        painter.drawLine(0, h / 2, w, h / 2)
        painter.drawEllipse((w / 2) - 25, (h / 2) - 25, 50, 50)
        painter.end()

        return image


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = OpenCVWidget()
    win.show()
    sys.exit(app.exec_())
