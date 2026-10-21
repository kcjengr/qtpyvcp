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


def test_linuxcnc_tool_table_uses_toolno_field():
    from types import SimpleNamespace

    # LinuxCNC stat.tool_table entries expose toolno/pocketno, not id/tool.
    table = [
        SimpleNamespace(toolno=0, pocketno=0, diameter=0.0, zoffset=0.0,
                        xoffset=0.0),
        SimpleNamespace(toolno=1, pocketno=7, diameter=8.0, zoffset=40.0,
                        xoffset=0.0),
    ]
    shape = tool_shape(table, 1, metric=True)
    assert shape.kind == "cylinder"
    assert shape.radius == pytest.approx(4.0)
    assert shape.length == pytest.approx(40.0)
    assert shape.tool_number == 1


def test_tool_lookup_is_by_tool_number_not_pocket_index():
    from types import SimpleNamespace

    table = [
        SimpleNamespace(toolno=0, pocketno=0, diameter=0.0, zoffset=0.0),
        SimpleNamespace(toolno=5, pocketno=1, diameter=10.0, zoffset=30.0),
    ]

    shape = tool_shape(table, 5, metric=True)
    assert shape.kind == "cylinder"
    assert shape.radius == pytest.approx(5.0)

    # A tool that is not in the table must not silently use another pocket.
    missing = tool_shape(table, 6, metric=True)
    assert missing.kind == "cone"
    assert missing.tool_number == 0


def test_tool_lookup_accepts_db_style_field_names():
    from types import SimpleNamespace

    for entry in (
        SimpleNamespace(tool=3, diameter=6.0, zoffset=20.0),
        SimpleNamespace(tool_no=3, diameter=6.0, zoffset=20.0),
        SimpleNamespace(number=3, diameter=6.0, zoffset=20.0),
        {"id": 3, "diameter": 6.0, "zoffset": 20.0},
    ):
        shape = tool_shape([entry], 3, metric=True)
        assert shape.kind == "cylinder"
        assert shape.radius == pytest.approx(3.0)


def test_linuxcnc_offset_pose_sets_tool_length():
    from types import SimpleNamespace

    table = [SimpleNamespace(
        toolno=1, pocketno=1, diameter=0.125,
        offset=SimpleNamespace(x=0.0, y=0.0, z=0.6234))]
    shape = tool_shape(table, 1, metric=False)
    assert shape.kind == "cylinder"
    assert shape.radius == pytest.approx(0.0625)
    assert shape.length == pytest.approx(0.6234)
