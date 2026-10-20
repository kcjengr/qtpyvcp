"""Tests for the Qt Quick 3D backplot camera rig and navigation filter.

The Qt Quick 3D rig has no ``QCamera`` object: it drives the QML cameras
through a provider and keeps the authoritative state in Python, which makes the
math directly testable without a render window.
"""

import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtCore = pytest.importorskip("PySide6.QtCore")
pytest.importorskip("PySide6.QtGui")
pytest.importorskip("PySide6.QtQuick3D")

from PySide6.QtGui import QVector3D

from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.geometry import (
    Quick3DPlotData,
)
from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.navigation import (
    BackplotNavigation,
)
from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.qtquick3d_backplot import (
    QuickCameraRig,
)

QEvent = QtCore.QEvent
Qt = QtCore.Qt
QPointF = QtCore.QPointF
QPoint = QtCore.QPoint


def make_rig(viewport=(800, 600)):
    data = Quick3DPlotData()
    rig = QuickCameraRig(data, lambda: (), lambda: viewport)
    rig.set_view("P", (0.0, 0.0, 0.0), distance=100.0)
    return rig


# -- camera math -----------------------------------------------------------

def test_orbit_preserves_distance_and_keeps_up_unit():
    rig = make_rig()
    before = rig._offset.length()
    up_before = QVector3D(rig._up)

    rig.orbit(30.0, 15.0)

    assert rig._offset.length() == pytest.approx(before, rel=1e-6)
    assert rig._up.length() == pytest.approx(1.0, rel=1e-6)
    assert rig._up != up_before


def test_orbit_keeps_up_perpendicular_to_view():
    rig = make_rig()
    for _ in range(40):
        rig.orbit(17.0, -9.0)
        forward = (-rig._offset).normalized()
        assert QVector3D.dotProduct(rig._up, forward) == pytest.approx(
            0.0, abs=1e-6)
        assert rig._up.length() == pytest.approx(1.0, rel=1e-5)


def test_many_orbits_do_not_destabilize_camera():
    rig = make_rig()
    for _ in range(200):
        rig.orbit(23.0, 31.0)
    assert np.isfinite([rig._offset.x(), rig._offset.y(), rig._offset.z()]).all()
    assert rig._offset.length() > 0.0


def test_pan_moves_center_at_one_pixel_per_magnification():
    rig = make_rig()
    rig.set_orthographic()
    rig.data.orthoMagnification = 2.0       # 2 pixels per world unit
    before = QVector3D(rig._center)

    rig.pan(40.0, 0.0, 800, 600)

    moved = (rig._center - before).length()
    assert moved == pytest.approx(40.0 / 2.0, rel=1e-6)


def test_pan_uses_the_viewport_height_for_orthographic_scale():
    rig = make_rig()
    rig.set_orthographic()
    rig.data.orthoMagnification = 1.0
    before = QVector3D(rig._center)

    rig.pan(10.0, 0.0, 1600, 800)          # 800 px tall -> 1 px per unit

    assert (rig._center - before).length() == pytest.approx(10.0, rel=1e-6)


def test_orthographic_dolly_and_zoom_scale_magnification():
    rig = make_rig()
    rig.set_orthographic()
    rig.data.orthoMagnification = 1.0

    rig.dolly(2.0)                          # dolly > 1 zooms in
    assert rig.data.orthoMagnification == pytest.approx(2.0)

    rig.zoom(0.5)                           # zoom < 1 zooms in
    assert rig.data.orthoMagnification == pytest.approx(4.0)


def test_perspective_dolly_and_zoom_change_eye_distance():
    rig = make_rig()
    rig.set_perspective()
    rig.look_at((0.0, 0.0, 0.0), (1.0, -1.0, 1.0), distance=100.0)

    rig.dolly(2.0)
    assert rig._offset.length() == pytest.approx(50.0)

    rig.zoom(2.0)
    assert rig._offset.length() == pytest.approx(100.0)


def test_fit_bounds_uses_pixels_per_world_unit():
    rig = make_rig(viewport=(800, 600))
    bounds = (0.0, 100.0, 0.0, 100.0, 0.0, 100.0)

    rig.fit_bounds(bounds, padding=1.1)

    span = 100.0 * 1.1
    assert rig.data.orthoMagnification == pytest.approx(600.0 / span)
    assert rig._scene_radius == pytest.approx(
        100.0 * (3 ** 0.5) * 0.5 * (1.0 + 0.6))


def test_fit_bounds_without_bounds_still_sets_a_view():
    rig = make_rig()
    rig.data.orthoMagnification = 0.0

    rig.fit_bounds(None)

    assert rig.data.orthoMagnification > 0.0


# -- mouse state machine ---------------------------------------------------

class FakeMouseEvent:
    def __init__(self, event_type, button=Qt.MouseButton.NoButton,
                 buttons=Qt.MouseButton.NoButton, pos=(0, 0)):
        self._type = event_type
        self._button = button
        self._buttons = buttons
        self._pos = pos

    def type(self):
        return self._type

    def button(self):
        return self._button

    def buttons(self):
        return self._buttons

    def position(self):
        return QPointF(*self._pos)


class FakeWheelEvent:
    def __init__(self, delta):
        self._delta = delta

    def type(self):
        return QEvent.Type.Wheel

    def angleDelta(self):
        return QPoint(0, self._delta)


class RecordingRig:
    def __init__(self):
        self.calls = []

    def orbit(self, azimuth, elevation):
        self.calls.append(("orbit", azimuth, elevation))

    def pan(self, dx, dy, width, height):
        self.calls.append(("pan", dx, dy, width, height))

    def dolly(self, factor):
        self.calls.append(("dolly", factor))

    def zoom(self, factor):
        self.calls.append(("zoom", factor))


def make_navigation(pan_mode=False):
    rig = RecordingRig()
    navigation = BackplotNavigation(rig, None, lambda: (800, 600))
    navigation.pan_mode = pan_mode
    return rig, navigation


def press(nav, button, pos=(100, 100)):
    nav.eventFilter(None, FakeMouseEvent(QEvent.Type.MouseButtonPress,
                                         button=button, buttons=button, pos=pos))


def move(nav, button, pos):
    nav.eventFilter(None, FakeMouseEvent(QEvent.Type.MouseMove,
                                         button=Qt.MouseButton.NoButton,
                                         buttons=button, pos=pos))


def release(nav, button):
    nav.eventFilter(None, FakeMouseEvent(QEvent.Type.MouseButtonRelease,
                                         button=button,
                                         buttons=Qt.MouseButton.NoButton))


def test_left_drag_orbits_and_release_ends():
    rig, nav = make_navigation()

    press(nav, Qt.MouseButton.LeftButton)
    move(nav, Qt.MouseButton.LeftButton, (160, 130))
    assert nav.dragged
    assert rig.calls and rig.calls[0][0] == "orbit"

    release(nav, Qt.MouseButton.LeftButton)
    assert not nav._active()


def test_middle_drag_pans_by_default():
    rig, nav = make_navigation()

    press(nav, Qt.MouseButton.MiddleButton)
    move(nav, Qt.MouseButton.MiddleButton, (150, 140))
    release(nav, Qt.MouseButton.MiddleButton)

    assert [call[0] for call in rig.calls] == ["pan"]


def test_pan_mode_swaps_left_and_middle():
    rig, nav = make_navigation(pan_mode=True)
    press(nav, Qt.MouseButton.LeftButton)
    move(nav, Qt.MouseButton.LeftButton, (150, 140))
    release(nav, Qt.MouseButton.LeftButton)
    assert [call[0] for call in rig.calls] == ["pan"]

    rig2, nav2 = make_navigation(pan_mode=True)
    press(nav2, Qt.MouseButton.MiddleButton)
    move(nav2, Qt.MouseButton.MiddleButton, (150, 140))
    release(nav2, Qt.MouseButton.MiddleButton)
    assert [call[0] for call in rig2.calls] == ["orbit"]


def test_right_drag_dollies():
    rig, nav = make_navigation()

    press(nav, Qt.MouseButton.RightButton)
    move(nav, Qt.MouseButton.RightButton, (100, 160))
    release(nav, Qt.MouseButton.RightButton)

    kind, factor = rig.calls[0]
    assert kind == "dolly"
    assert factor > 1.0                     # dragging down zooms in


def test_wheel_zooms_in_and_out():
    rig, nav = make_navigation()

    nav.eventFilter(None, FakeWheelEvent(120))
    nav.eventFilter(None, FakeWheelEvent(-120))

    assert [call[0] for call in rig.calls] == ["zoom", "zoom"]
    assert rig.calls[0][1] < 1.0
    assert rig.calls[1][1] > 1.0


def test_click_without_drag_is_not_flagged_as_drag():
    _, nav = make_navigation()
    press(nav, Qt.MouseButton.LeftButton)
    move(nav, Qt.MouseButton.LeftButton, (101, 100))
    assert not nav.dragged
    release(nav, Qt.MouseButton.LeftButton)


def test_missing_release_ends_navigation_on_move_without_buttons():
    _, nav = make_navigation()
    press(nav, Qt.MouseButton.LeftButton)
    nav.eventFilter(None, FakeMouseEvent(QEvent.Type.MouseMove,
                                         buttons=Qt.MouseButton.NoButton,
                                         pos=(120, 120)))
    assert not nav._active()
