"""VTK-compatible mouse navigation for the Qt3D backplot.

Reproduces the VTK backplot's interaction model:

* left drag   -> orbit (or pan when ``pan_mode`` is active)
* middle drag -> pan (or orbit when ``pan_mode`` is active)
* right drag  -> dolly / zoom
* wheel       -> zoom in/out
* left click (no drag) -> program-line pick

The controller is installed as a Qt event filter on the Qt3D window container
so it sees raw mouse events before Qt3D's own input handling.
"""

from PySide6.QtCore import QEvent, QObject, Qt


class BackplotNavigation(QObject):
    """Turns mouse events on *target* into camera motions on *rig*."""

    DRAG_THRESHOLD_SQ = 4

    # Tunable feel. VTK uses 1 degree per pixel and a 1.02 ** (0.5 * dy)
    # dolly, which is brisk on a modern high-DPI mouse; the defaults below are
    # a notch gentler. Both are exposed as properties so a config can adjust
    # them without touching the code.
    DEFAULT_ORBIT_SENSITIVITY = 0.6
    DEFAULT_ZOOM_SENSITIVITY = 0.45

    def __init__(self, rig, target, viewport_size, parent=None):
        super().__init__(parent)
        self._rig = rig
        self._target = target
        self._viewport_size = viewport_size
        self._pan_mode = False
        self.orbit_sensitivity = self.DEFAULT_ORBIT_SENSITIVITY
        self.zoom_sensitivity = self.DEFAULT_ZOOM_SENSITIVITY

        self._rotating = False
        self._panning = False
        self._dollying = False
        self._last_pos = None
        self._press_pos = None
        self.dragged = False

    # -- configuration ------------------------------------------------------

    @property
    def pan_mode(self):
        return self._pan_mode

    @pan_mode.setter
    def pan_mode(self, enabled):
        self._pan_mode = bool(enabled)

    @staticmethod
    def is_left(button):
        return button == Qt.MouseButton.LeftButton

    @staticmethod
    def is_middle(button):
        return button == Qt.MouseButton.MiddleButton

    @staticmethod
    def is_right(button):
        return button == Qt.MouseButton.RightButton

    # -- state --------------------------------------------------------------

    def _active(self):
        return self._rotating or self._panning or self._dollying

    def end_navigation(self):
        self._rotating = self._panning = self._dollying = False
        self._last_pos = None

    def _viewport(self):
        try:
            width, height = self._viewport_size()
            return max(int(width), 1), max(int(height), 1)
        except (TypeError, ValueError, RuntimeError, AttributeError):
            return 1, 1

    @staticmethod
    def _event_pos(event):
        try:
            point = event.position()
        except AttributeError:
            point = event.pos()
        return point.x(), point.y()

    # -- event filter -------------------------------------------------------

    def eventFilter(self, obj, event):
        event_type = event.type()

        if event_type == QEvent.Type.MouseButtonPress:
            self._on_press(event)
            return False
        if event_type == QEvent.Type.MouseMove:
            self._on_move(event)
            return False
        if event_type == QEvent.Type.MouseButtonRelease:
            self._on_release(event)
            return False
        if event_type == QEvent.Type.Wheel:
            self._on_wheel(event)
            return False
        return False

    def _on_press(self, event):
        if self._active():
            return
        self._last_pos = self._event_pos(event)
        self._press_pos = self._last_pos
        self.dragged = False

        button = event.button()
        if self.is_left(button):
            if self._pan_mode:
                self._panning = True
            else:
                self._rotating = True
        elif self.is_middle(button):
            if self._pan_mode:
                self._rotating = True
            else:
                self._panning = True
        elif self.is_right(button):
            self._dollying = True

    def _on_move(self, event):
        if self._active() and not event.buttons():
            # A release event went missing (e.g. the cursor left the window
            # mid-drag); don't keep the camera glued to the mouse.
            self.end_navigation()
            return

        x, y = self._event_pos(event)
        if self._press_pos is not None and not self.dragged:
            dx = x - self._press_pos[0]
            dy = y - self._press_pos[1]
            self.dragged = (dx * dx + dy * dy) > self.DRAG_THRESHOLD_SQ

        if self._last_pos is None:
            self._last_pos = (x, y)
            return

        last_x, last_y = self._last_pos
        dx = x - last_x
        dy = y - last_y
        self._last_pos = (x, y)

        if not self._active() or (dx == 0 and dy == 0):
            return

        if self._rotating:
            # VTK: azimuth = lastX - x, elevation = lastY - y, scaled.
            scale = self.orbit_sensitivity
            self._rig.orbit(-dx * scale, -dy * scale)
        elif self._panning:
            width, height = self._viewport()
            self._rig.pan(dx, dy, width, height)
        elif self._dollying:
            # VTK: dollyFactor = pow(1.02, 0.5 * (y - lastY)).
            self._rig.dolly(1.02 ** (self.zoom_sensitivity * dy))

    def _on_release(self, event):
        if event.buttons():
            # A second button is still held; keep the current gesture.
            return
        self.end_navigation()

    def _on_wheel(self, event):
        try:
            delta = event.angleDelta().y()
        except AttributeError:
            delta = 0
        if delta == 0:
            return
        # VTK: scroll forward zooms in, backward zooms out.
        if delta > 0:
            self._rig.zoom(0.9)
        else:
            self._rig.zoom(1.1)
