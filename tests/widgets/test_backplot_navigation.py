"""Tests for the VTK-compatible Qt3D backplot navigation.

Covers the camera math (orbit/pan/dolly) and the mouse state machine
(left-rotate, middle-pan, right-zoom, pan-mode swap, wheel zoom).
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
Qt3DRender = pytest.importorskip("PySide6.Qt3DRender").Qt3DRender
QtCore = pytest.importorskip("PySide6.QtCore")
QVector3D = pytest.importorskip("PySide6.QtGui").QVector3D

from qtpyvcp.widgets.display_widgets.qt3d_backplot.camera import CameraRig
from qtpyvcp.widgets.display_widgets.qt3d_backplot.navigation import (
    BackplotNavigation,
)

QEvent = QtCore.QEvent
Qt = QtCore.Qt
QPointF = QtCore.QPointF
QPoint = QtCore.QPoint


@pytest.fixture(scope="module")
def qt_app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def make_rig():
    camera = Qt3DRender.QCamera()
    rig = CameraRig(camera)
    rig.look_at((0.0, 0.0, 0.0), (1.0, -1.0, 1.0), (0.0, 0.0, 1.0), distance=100.0)
    return rig


# -- camera math -----------------------------------------------------------

def test_orbit_preserves_distance_and_keeps_up_unit(qt_app):
    rig = make_rig()
    before = (rig.camera.position() - rig.camera.viewCenter()).length()

    rig.orbit(30.0, 15.0)

    after = (rig.camera.position() - rig.camera.viewCenter()).length()
    assert after == pytest.approx(before, rel=1e-4)
    assert rig.camera.upVector().length() == pytest.approx(1.0, rel=1e-4)
    assert rig.camera.position() != QVector3D(100.0, -100.0, 100.0)


def test_orbit_keeps_up_perpendicular_to_view(qt_app):
    rig = make_rig()
    for _ in range(40):
        rig.orbit(17.0, -9.0)
        forward = (rig.camera.viewCenter() - rig.camera.position()).normalized()
        up = rig.camera.upVector()
        assert QVector3D.dotProduct(up, forward) == pytest.approx(0.0, abs=1e-4)
        assert up.length() == pytest.approx(1.0, rel=1e-4)


def test_many_orbits_do_not_destabilize_camera(qt_app):
    rig = make_rig()
    for _ in range(200):
        rig.orbit(23.0, 31.0)
    position = rig.camera.position()
    assert all(value == value for value in (position.x(), position.y(), position.z()))
    distance = (position - rig.camera.viewCenter()).length()
    assert distance > 0.0


def test_pan_translates_position_and_center_together(qt_app):
    rig = make_rig()
    center_before = rig.camera.viewCenter()
    position_before = rig.camera.position()

    rig.pan(40.0, -25.0, 800, 600)

    center_delta = rig.camera.viewCenter() - center_before
    position_delta = rig.camera.position() - position_before
    assert (center_delta - position_delta).length() == pytest.approx(0.0, abs=1e-5)
    assert center_delta.length() > 0.0


def test_dolly_factor_above_one_zooms_in(qt_app):
    rig = make_rig()
    before = (rig.camera.position() - rig.camera.viewCenter()).length()

    rig.dolly(2.0)

    after = (rig.camera.position() - rig.camera.viewCenter()).length()
    assert after == pytest.approx(before / 2.0, rel=1e-4)


def test_orthographic_dolly_scales_projection(qt_app):
    rig = make_rig()
    rig.set_orthographic()
    rig.camera.setTop(10.0)
    rig.camera.setBottom(-10.0)

    rig.dolly(2.0)

    assert rig.camera.top() == pytest.approx(5.0)


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


def make_navigation(pan_mode=False):
    rig = make_rig()
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


def test_left_drag_orbits_and_release_ends(qt_app):
    rig, nav = make_navigation()
    before = rig.camera.position()

    press(nav, Qt.MouseButton.LeftButton)
    move(nav, Qt.MouseButton.LeftButton, (160, 130))
    assert nav.dragged
    assert rig.camera.position() != before

    release(nav, Qt.MouseButton.LeftButton)
    assert not nav._active()


def test_middle_drag_pans_by_default(qt_app):
    rig, nav = make_navigation()
    center_before = rig.camera.viewCenter()

    press(nav, Qt.MouseButton.MiddleButton)
    move(nav, Qt.MouseButton.MiddleButton, (150, 140))
    release(nav, Qt.MouseButton.MiddleButton)

    assert rig.camera.viewCenter() != center_before


def test_pan_mode_swaps_left_and_middle(qt_app):
    rig, nav = make_navigation(pan_mode=True)
    center_before = rig.camera.viewCenter()

    press(nav, Qt.MouseButton.LeftButton)
    move(nav, Qt.MouseButton.LeftButton, (150, 140))
    assert rig.camera.viewCenter() != center_before
    release(nav, Qt.MouseButton.LeftButton)

    rig2, nav2 = make_navigation(pan_mode=True)
    position_before = rig2.camera.position()
    press(nav2, Qt.MouseButton.MiddleButton)
    move(nav2, Qt.MouseButton.MiddleButton, (150, 140))
    # Middle in pan-mode orbits, which moves the camera position too.
    assert (rig2.camera.position() - position_before).length() > 0.0


def test_right_drag_dollies(qt_app):
    rig, nav = make_navigation()
    before = (rig.camera.position() - rig.camera.viewCenter()).length()

    press(nav, Qt.MouseButton.RightButton)
    move(nav, Qt.MouseButton.RightButton, (100, 160))  # drag down -> zoom in
    release(nav, Qt.MouseButton.RightButton)

    after = (rig.camera.position() - rig.camera.viewCenter()).length()
    assert after < before


def test_wheel_zooms_in_and_out(qt_app):
    rig, nav = make_navigation()
    start = (rig.camera.position() - rig.camera.viewCenter()).length()

    nav.eventFilter(None, FakeWheelEvent(120))
    zoomed_in = (rig.camera.position() - rig.camera.viewCenter()).length()
    assert zoomed_in < start

    nav.eventFilter(None, FakeWheelEvent(-120))
    zoomed_out = (rig.camera.position() - rig.camera.viewCenter()).length()
    assert zoomed_out > zoomed_in


def test_click_without_drag_is_not_flagged_as_drag(qt_app):
    _, nav = make_navigation()
    press(nav, Qt.MouseButton.LeftButton)
    move(nav, Qt.MouseButton.LeftButton, (101, 100))
    assert not nav.dragged
    release(nav, Qt.MouseButton.LeftButton)
