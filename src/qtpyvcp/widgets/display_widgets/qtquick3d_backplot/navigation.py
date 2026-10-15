"""Mouse controls shared by the Qt Quick 3D backplot camera."""

from PySide6.QtCore import QEvent, QObject, Qt


class BackplotNavigation(QObject):
    """VTK-style orbit, pan, and zoom controller installed on a Quick widget."""

    DRAG_THRESHOLD_SQ = 4
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
        self._rotating = self._panning = self._dollying = False
        self._last_pos = self._press_pos = None
        self.dragged = False

    @property
    def pan_mode(self):
        return self._pan_mode

    @pan_mode.setter
    def pan_mode(self, enabled):
        self._pan_mode = bool(enabled)

    def _active(self):
        return self._rotating or self._panning or self._dollying

    def end_navigation(self):
        self._rotating = self._panning = self._dollying = False
        self._last_pos = None

    @staticmethod
    def _event_pos(event):
        try:
            point = event.position()
        except AttributeError:
            point = event.pos()
        return point.x(), point.y()

    def eventFilter(self, obj, event):
        event_type = event.type()
        if event_type == QEvent.Type.MouseButtonPress:
            self._on_press(event)
        elif event_type == QEvent.Type.MouseMove:
            self._on_move(event)
        elif event_type == QEvent.Type.MouseButtonRelease:
            self._on_release(event)
        elif event_type == QEvent.Type.Wheel:
            self._on_wheel(event)
        return False

    def _on_press(self, event):
        if self._active():
            return
        self._last_pos = self._press_pos = self._event_pos(event)
        self.dragged = False
        button = event.button()
        if button == Qt.MouseButton.LeftButton:
            self._panning = self._pan_mode
            self._rotating = not self._pan_mode
        elif button == Qt.MouseButton.MiddleButton:
            self._rotating = self._pan_mode
            self._panning = not self._pan_mode
        elif button == Qt.MouseButton.RightButton:
            self._dollying = True

    def _on_move(self, event):
        if self._active() and not event.buttons():
            self.end_navigation()
            return
        x, y = self._event_pos(event)
        if self._press_pos is not None and not self.dragged:
            dx = x - self._press_pos[0]
            dy = y - self._press_pos[1]
            self.dragged = dx * dx + dy * dy > self.DRAG_THRESHOLD_SQ
        if self._last_pos is None:
            self._last_pos = (x, y)
            return
        last_x, last_y = self._last_pos
        dx, dy = x - last_x, y - last_y
        self._last_pos = (x, y)
        if not self._active() or (dx == 0 and dy == 0):
            return
        if self._rotating:
            self._rig.orbit(-dx * self.orbit_sensitivity,
                            -dy * self.orbit_sensitivity)
        elif self._panning:
            width, height = self._viewport_size()
            self._rig.pan(dx, dy, width, height)
        elif self._dollying:
            self._rig.dolly(1.02 ** (self.zoom_sensitivity * dy))

    def _on_release(self, event):
        if not event.buttons():
            self.end_navigation()

    def _on_wheel(self, event):
        delta = event.angleDelta().y()
        if delta:
            self._rig.zoom(0.9 if delta > 0 else 1.1)
