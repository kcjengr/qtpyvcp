import os
import sys
import cv2

from qtpy.QtGui import QImage, QPixmap
from qtpy.QtCore import Qt, QSize, QTimer, Slot
from qtpy.QtWidgets import QLabel


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

        # Green color in RGB
        self.line_color = (255, 127, 0)

        # Line thickness of 9 px
        self.line_thickness = 1

        self._h_lines = 0
        self._v_lines = 0
        self._c_radius = 25

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

            self.draw_crosshairs(frame)

            image = QImage(frame, frame.shape[1], frame.shape[0],
                           frame.strides[0], QImage.Format_RGB888)

            self.setPixmap(QPixmap.fromImage(image))

    def draw_crosshairs(self, frame):

        w = self.video_size.width()
        h = self.video_size.height()

        cv2.line(frame,
                 ((w / 2) + self._v_lines, 0),
                 ((w / 2) + self._v_lines, h),
                 self.line_color, self.line_thickness)

        cv2.line(frame,
                 (0, (h / 2) - self._h_lines),
                 (w, (h / 2) - self._h_lines),
                 self.line_color, self.line_thickness)

        if self._c_radius > 1:
            cv2.circle(frame, ((w / 2) + self._v_lines, (h / 2) - self._h_lines), self._c_radius, self.line_color, self.line_thickness)

    @Slot(int)
    def setHorizontalLine(self, value):
        self._h_lines = value

    @Slot(int)
    def setVerticalLine(self, value):
        self._v_lines = value

    @Slot(int)
    def setCenterRadius(self, value):
        self._c_radius = value


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = OpenCVWidget()
    win.show()
    sys.exit(app.exec_())
