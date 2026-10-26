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


def test_insert_record_falls_back_to_tool_entry_fields():
    from types import SimpleNamespace

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.tool import (
        resolve_insert_record,
    )

    entry = SimpleNamespace(
        toolno=4, diameter=6.35, type="turning", insert_shape="C",
        insert_size_mode="IC", insert_size=6.35, insert_thickness=3.18,
        holder_style="SCLCR", holder_hand="R")
    record = resolve_insert_record(object(), 4, entry)
    assert record is not None
    assert record["tool_no"] == 4
    assert record["type"] == "turning"


def test_lathe_insert_polygon_is_ccw_and_triangulates():
    from qtpyvcp.lib.db_tool.insert_profile import insert_record
    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.tool import (
        insert_mesh,
        insert_polygon,
        triangulate_polygon,
    )

    record = insert_record(
        {"T": 2, "D": 6.35},
        {"type": "turning", "insert_shape": "C", "insert_size_mode": "IC",
         "insert_size": 6.35, "insert_thickness": 3.18,
         "holder_style": "SCLCR", "holder_hand": "R"})
    polygon = insert_polygon(record, {"orientation": 2})
    assert polygon is not None
    assert len(polygon) >= 4

    area2 = 0.0
    for index, (x1, z1) in enumerate(polygon):
        x2, z2 = polygon[(index + 1) % len(polygon)]
        area2 += x1 * z2 - x2 * z1
    assert area2 >= 0.0

    triangles = triangulate_polygon(polygon)
    assert triangles
    mesh = insert_mesh(polygon)
    assert mesh is not None
    vertices, normals = mesh
    # Front and back faces, three vertices per triangle.
    assert len(vertices) == len(triangles) * 6
    assert len(normals) == len(vertices)
    assert set(map(tuple, normals)) == {(0.0, 0.0, 1.0), (0.0, 0.0, -1.0)}


def test_per_tool_model_path_is_resolved_relative_to_config_dir(tmp_path):
    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.tool import (
        resolve_tool_model_path,
    )

    model = tmp_path / "tool.stl"
    model.write_text("solid x\nendsolid x\n")
    datasource = type("DS", (), {"config_dir": str(tmp_path)})()
    assert resolve_tool_model_path(
        datasource, {"id": 1, "model": "tool.stl"}, 1) == str(model)
    assert resolve_tool_model_path(
        datasource, {"id": 1, "model": "missing.stl"}, 1) is None


def test_cone_body_offset_puts_the_tip_at_the_tool_position():
    # The built-in #Cone is authored with its origin at the base and is
    # rotated 180 degrees in QML; the tip is therefore one full length below
    # the model origin.
    offset = tool_body_offset(
        ToolShape(kind="cone", radius=12.7, length=25.4))
    assert offset == (0.0, 0.0, 25.4)
