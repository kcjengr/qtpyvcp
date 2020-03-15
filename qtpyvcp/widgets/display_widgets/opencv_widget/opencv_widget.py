import sys

from qtpy.QtGui import QImage, QPixmap
from qtpy.QtCore import QSize, QTimer
from qtpy.QtWidgets import QLabel, QWidget, QVBoxLayout, QApplication

import cv2
import os

from qtpyvcp.widgets import VCPWidget

IN_DESIGNER = os.getenv('DESIGNER', False)


class OpenCVWidget(QWidget):

    def __init__(self, parent=None):
        super(OpenCVWidget, self).__init__()
        if not IN_DESIGNER:
            self.video_size = QSize(320, 240)
            self.setup_ui()
            self.setup_camera()

    def setup_ui(self):
        """Initialize widgets.
        """
        self.image_label = QLabel()
        self.image_label.setFixedSize(self.video_size)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.image_label)

        self.setLayout(self.main_layout)

    def setup_camera(self):
        """Initialize camera.
        """
        self.capture = cv2.VideoCapture('/dev/video0')
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_size.width())
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_size.height())

        self.timer = QTimer()
        self.timer.timeout.connect(self.display_video_stream)
        self.timer.start(30)

    def display_video_stream(self):
        """Read frame from camera and repaint QLabel widget.
        """
        result, frame = self.capture.read()

        if result is True:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)
            image = QImage(frame, frame.shape[1], frame.shape[0],
                           frame.strides[0], QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(image))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = OpenCVWidget()
    win.show()
    sys.exit(app.exec_())
