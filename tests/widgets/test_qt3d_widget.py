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
    toolInSpindleChanged = QtCore.Signal(int)
    toolTableChanged = QtCore.Signal(tuple)
    toolOffsetChanged = QtCore.Signal(tuple)
    offsetTableChanged = QtCore.Signal(object)

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
        return {0: (0.0, 0.0, 0.0, 0.0)}

    def getOffsetColumns(self):
        return {"X": 0, "Y": 1, "Z": 2, "R": 3}

    def getAxis(self):
        axis = {"min_position_limit": -100.0, "max_position_limit": 100.0}
        return [{"min_position_limit": -200.0, "max_position_limit": 200.0},
                axis, axis]

    def getProgramUnits(self):
        return 'G21'

    def getAxisMask(self):
        return 7

    def getToolTable(self):
        return [
            {"id": 0, "diameter": 0.0, "zoffset": 0.0},
            {"id": 1, "diameter": 6.0, "zoffset": 40.0},
            {"id": 2, "diameter": 12.0, "zoffset": 55.0},
        ]


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
    plot = module.Qt3D0()
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


def test_jog_position_updates_keep_a_stable_trail(widget):
    trail_entity = widget._trail_line.entity

    for step in range(500):
        widget.update_position((float(step), float(step) * 0.5, 0.0))

    # The trail entity must be reused, not rebuilt per jog update.
    assert widget._trail_line.entity is trail_entity
    assert widget._trail_line.position_attribute.count() == 2 * (500 - 1)
    assert widget._trail_line.entity.isEnabled()


def test_jog_position_updates_after_container_deleted_are_safe(widget):
    shiboken6.delete(widget.container)
    for step in range(50):
        widget.update_position((float(step), 0.0, 0.0))


def test_clear_live_plot_empties_the_trail(widget):
    for step in range(10):
        widget.update_position((float(step), 0.0, 0.0))
    widget.clearLivePlot()
    assert widget._trail_line.position_attribute.count() == 0
    assert not widget._trail_line.entity.isEnabled()


def test_offset_table_change_moves_path_transforms(widget):
    from PySide6.Qt3DCore import Qt3DCore

    transform = Qt3DCore.QTransform()
    widget._path_transforms[0] = transform

    widget.datasource.getWcsOffsets = lambda: {0: (10.0, 20.0, 30.0, 45.0)}
    widget.on_offset_table_changed({0: (10.0, 20.0, 30.0, 45.0)})

    translation = transform.translation()
    assert (translation.x(), translation.y(), translation.z()) == (10.0, 20.0, 30.0)
    assert transform.rotationZ() == pytest.approx(45.0)


def test_wcs_offsets_read_column_layout(widget):
    widget.datasource.getOffsetColumns = lambda: {"X": 3, "Y": 1, "Z": 0, "R": 2}
    widget._offset_columns_cache = None
    widget.datasource.getWcsOffsets = lambda: {0: (7.0, 8.0, 9.0, 11.0)}
    x, y, z, r = widget._wcs_offsets(0)
    assert (x, y, z, r) == (11.0, 8.0, 7.0, 9.0)


def test_tool_shape_cylinder_for_loaded_tool():
    from qtpyvcp.widgets.display_widgets.qt3d_backplot.tool import tool_shape

    table = [{"id": 1, "diameter": 6.0, "zoffset": 40.0}]
    shape = tool_shape(table, 1, metric=True)
    assert shape.kind == "cylinder"
    assert shape.radius == pytest.approx(3.0)
    assert shape.length == pytest.approx(40.0)
    assert shape.visible


def test_tool_shape_cone_when_no_tool_loaded():
    from qtpyvcp.widgets.display_widgets.qt3d_backplot.tool import tool_shape

    table = [{"id": 0, "diameter": 0.0, "zoffset": 0.0}]
    shape = tool_shape(table, 0, metric=True)
    assert shape.kind == "cone"
    assert shape.radius == pytest.approx(50.8 / 4.0)
    assert shape.length == pytest.approx(50.8 / 2.0)


def test_tool_shape_lathe_uses_diameter_and_offset():
    from qtpyvcp.widgets.display_widgets.qt3d_backplot.tool import tool_shape

    table = [{"id": 3, "diameter": 8.0, "zoffset": 20.0, "xoffset": 1.5}]
    shape = tool_shape(table, 3, metric=False, lathe=True)
    assert shape.kind == "cylinder"
    assert shape.radius == pytest.approx(4.0)
    assert shape.x_offset == pytest.approx(1.5)


def test_widget_builds_tool_from_tool_table(widget):
    widget.update_tool_number(2)
    assert widget._tool_shape.kind == "cylinder"
    assert widget._tool_shape.radius == pytest.approx(6.0)
    assert widget._tool_entity is not None
    assert widget._tool_entity.isEnabled()


def test_tool_body_offset_places_tip_at_origin():
    from qtpyvcp.widgets.display_widgets.qt3d_backplot.tool import (
        ToolShape,
        tool_body_offset,
    )

    offset = tool_body_offset(ToolShape(kind="cylinder", radius=3.0, length=40.0))
    assert offset == (0.0, 0.0, 20.0)


def test_gradient_background_survives_background_color_change(widget):
    from PySide6.QtGui import QColor

    shiboken6.delete(widget.container)
    widget.backgroundColor = QColor(10, 20, 30)
    widget.backgroundColor2 = QColor(5, 6, 7)
