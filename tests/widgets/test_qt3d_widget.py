"""Widget-level Qt3D backplot tests.

These build the real widget against a stubbed LinuxCNC datasource so the
render-surface lifetime paths (camera signals firing during/after teardown)
can be exercised without a live machine.
"""

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QtCore = pytest.importorskip("PySide6.QtCore")
shiboken6 = pytest.importorskip("shiboken6")

import qtpyvcp.widgets.display_widgets.qt3d_backplot.qt3d_backplot as module


class _FakeDatasource(QtCore.QObject):
    programLoaded = QtCore.Signal(str)
    positionChanged = QtCore.Signal(tuple)
    g5xOffsetChanged = QtCore.Signal(tuple)
    g92OffsetChanged = QtCore.Signal(tuple)
    g5xIndexChanged = QtCore.Signal(int)
    rotationXYChanged = QtCore.Signal(float)

    config_dir = None
    _inifile = None

    def isMachineLathe(self):
        return False

    def isMachineMetric(self):
        return True

    def isMachineFoam(self):
        return False

    def isMachineJet(self):
        return False

    def getAxisMotionOwners(self):
        return {axis: 'head' for axis in ('X', 'Y', 'Z', 'A', 'B', 'C')}

    def getArcDivision(self):
        return 64

    def getActiveWcsIndex(self):
        return 0

    def getToolOffset(self):
        return (0.0,) * 9

    def getRotaryAxisWrapped(self):
        return {'A': False, 'B': False, 'C': False}

    def getActiveWcsOffsets(self):
        return (0.0,) * 9

    def getWcsOffsets(self):
        return {0: (0, 0, 0, 0)}

    def getAxis(self):
        axis = {"min_position_limit": -100.0, "max_position_limit": 100.0}
        return [{"min_position_limit": -200.0, "max_position_limit": 200.0},
                axis, axis]

    def getProgramUnits(self):
        return 'G21'

    def getAxisMask(self):
        return 7

    def getToolTable(self):
        return []


class _FakeStat:
    def poll(self):
        pass


@pytest.fixture(scope="module")
def qt_app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def widget(qt_app, monkeypatch):
    monkeypatch.setattr(module, "LinuxCncDataSource", _FakeDatasource)
    monkeypatch.setattr(module.BaseBackPlot, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(module, "linuxcnc", SimpleNamespace(stat=lambda: _FakeStat()))
    monkeypatch.setattr(module, "connectSetting", lambda *a, **k: None)
    plot = module.Qt3DBackPlot()
    yield plot
    plot.deleteLater()


def test_view_preset_and_projection_switches_do_not_raise(widget):
    widget.setViewPersp()
    widget.setViewOrtho()
    widget.setViewP()
    widget.setViewX()
    widget.setViewMachine()
    widget.setViewProgram('p')


def test_access_after_container_deleted_is_safe(widget):
    # Simulate teardown ordering: the render surface is gone but Python still
    # holds the widget. Refresh paths that used to raise
    # "Internal C++ object already deleted" (the perspective-view crash).
    shiboken6.delete(widget.container)

    widget._update_gradient_background()
    widget.setViewPersp()
    widget.setViewOrtho()
    widget.setViewP()
    widget.clearLivePlot()
    widget.update_position((1.0, 2.0, 3.0))


def test_gradient_background_survives_background_color_change(widget):
    from PySide6.QtGui import QColor

    shiboken6.delete(widget.container)
    widget.backgroundColor = QColor(10, 20, 30)
    widget.backgroundColor2 = QColor(5, 6, 7)
