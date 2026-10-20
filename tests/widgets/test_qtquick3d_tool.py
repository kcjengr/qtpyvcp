"""Tool-body sizing tests for the Qt Quick 3D backplot."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtCore")

from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.tool import (
    ToolShape,
    resolve_tool_entry,
    tool_body_offset,
    tool_shape,
)


def test_cylinder_for_loaded_metric_tool():
    table = [{"id": 1, "diameter": 6.0, "zoffset": 40.0}]
    shape = tool_shape(table, 1, metric=True)
    assert shape.kind == "cylinder"
    assert shape.radius == pytest.approx(3.0)
    assert shape.length == pytest.approx(40.0)
    assert shape.visible


def test_cone_when_no_tool_is_loaded():
    table = [{"id": 0, "diameter": 0.0, "zoffset": 0.0}]
    shape = tool_shape(table, 0, metric=True)
    assert shape.kind == "cone"
    assert shape.radius == pytest.approx(50.8 / 4.0)
    assert shape.length == pytest.approx(50.8 / 2.0)


def test_lathe_uses_diameter_and_x_offset():
    table = [{"id": 3, "diameter": 8.0, "zoffset": 20.0, "xoffset": 1.5}]
    shape = tool_shape(table, 3, metric=False, lathe=True)
    assert shape.kind == "cylinder"
    assert shape.radius == pytest.approx(4.0)
    assert shape.x_offset == pytest.approx(1.5)


def test_robot_foam_and_jet_draw_no_generic_body():
    for flag in ("robot", "foam", "jet"):
        shape = tool_shape([], 1, metric=True, **{flag: True})
        assert shape.kind == "none"
        assert not shape.visible


def test_resolve_tool_entry_handles_number_keyed_dict():
    table = {7: {"id": 7, "diameter": 12.0}}
    assert resolve_tool_entry(table, 7) == table[7]
    assert resolve_tool_entry(table, 99) == table[7]


def test_tool_body_offset_places_tip_at_origin():
    offset = tool_body_offset(ToolShape(kind="cylinder", radius=3.0, length=40.0))
    assert offset == (0.0, 0.0, 20.0)


def test_tool_body_offset_includes_lathe_x_offset():
    offset = tool_body_offset(
        ToolShape(kind="cylinder", radius=3.0, length=20.0, x_offset=1.5))
    assert offset == (1.5, 0.0, 10.0)
