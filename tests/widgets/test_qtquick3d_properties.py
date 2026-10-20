"""Meta-property compatibility for the Qt Quick 3D backplot widget."""

from types import SimpleNamespace

import numpy as np
import pytest

QtCore = pytest.importorskip("PySide6.QtCore")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
pytest.importorskip("PySide6.QtQuick3D")
try:
    import qtpyvcp.widgets.display_widgets.qtquick3d_backplot.qtquick3d_backplot as module
    Qt3D0 = module.Qt3D0
except ImportError as exc:
    pytest.skip(f"Qt Quick 3D backplot runtime dependencies unavailable: {exc}",
                allow_module_level=True)


class _FakeDatasource(QtCore.QObject):
    programLoaded = QtCore.Signal(str)
    positionChanged = QtCore.Signal(tuple)
    motionTypeChanged = QtCore.Signal(int)
    g5xOffsetChanged = QtCore.Signal(tuple)
    g92OffsetChanged = QtCore.Signal(tuple)
    g5xIndexChanged = QtCore.Signal(int)
    rotationXYChanged = QtCore.Signal(float)
    offsetTableChanged = QtCore.Signal(object)
    activeOffsetChanged = QtCore.Signal(int)
    runStateChanged = QtCore.Signal(bool)
    toolInSpindleChanged = QtCore.Signal(int)
    toolTableChanged = QtCore.Signal(tuple)
    toolOffsetChanged = QtCore.Signal(tuple)

    machine_position = (0.0, 0.0, 0.0)
    program_running = False

    def isMachineMetric(self):
        return True

    def isMachineLathe(self):
        return False

    def isMachineFoam(self):
        return False

    def isMachineJet(self):
        return False

    def isProgramRunning(self):
        return self.program_running

    def getMachinePosition(self):
        return self.machine_position

    def getG92_offset(self):
        return (0.0,) * 9

    def getToolTable(self):
        return [{"id": 0, "diameter": 0.0, "zoffset": 0.0},
                {"id": 1, "diameter": 6.0, "zoffset": 40.0}]

    def getAxis(self):
        return [
            {"min_position_limit": -100.0, "max_position_limit": 100.0},
            {"min_position_limit": -100.0, "max_position_limit": 100.0},
            {"min_position_limit": -50.0, "max_position_limit": 0.0},
        ]

    def getArcDivision(self):
        return 8

    def getAxisMask(self):
        return 7

    def getAxisMotionOwners(self):
        return {"A": "head", "B": "head", "C": "head"}

    def getProgramUnits(self):
        return "G21"

    def getActiveWcsIndex(self):
        return 0

    def getActiveWcsOffsets(self):
        return (0.0,) * 9

    def getRotationOfActiveWcs(self):
        return 0.0

    def getWcsOffsets(self):
        return {}

    def getOffsetColumns(self):
        return {"X": 0, "Y": 1, "Z": 2, "A": 3, "B": 4, "C": 5,
                "U": 6, "V": 7, "W": 8, "R": 9}


class _FakeStat:
    file = ""
    tool_in_spindle = 0
    tool_offset = [0.0] * 9

    def poll(self):
        pass


class _OffsetDatasource(_FakeDatasource):
    """Datasource with a live active-WCS offset but an empty offset table."""

    def getActiveWcsIndex(self):
        return 0

    def getActiveWcsOffsets(self):
        return (10.0, 20.0, 30.0, 0, 0, 0, 0, 0, 0)

    def getRotationOfActiveWcs(self):
        return 0.0

    def getWcsOffsets(self):
        return {}

    def getOffsetColumns(self):
        return {"X": 0, "Y": 1, "Z": 2, "A": 3, "B": 4, "C": 5,
                "U": 6, "V": 7, "W": 8, "R": 9}


def test_qt3d0_exposes_backplot_properties():
    names = (
        "backgroundColor", "backgroundColor2", "enableProgramTicks",
        "traverseColor", "arcfeedColor", "feedColor", "dwellColor", "userColor",
        "gridVisible",
        "navHelperEnabled", "navHelperAnimate", "navHelperShouldResetCamera",
        "navHelperKeyActivation", "navHelperAnchor", "navHelperPadding",
        "navHelperSize", "navHelperTotalLength", "navHelperHandleSize",
        "navHelperNormalizedHandleDia", "navHelperContainerVisibility",
        "navHelperDragable", "navHelperPickable", "navHelperShaftResolution",
        "navHelperHandleResolution", "navHelperXAxisColor", "navHelperYAxisColor",
        "navHelperZAxisColor", "navHelperHandleVisibility", "navHelperLabelsVisible",
        "navHelperLabels", "navHelperAxisColor",
        "navHelperContainerCircumferentialResolution",
        "navHelperContainerRadialResolution", "navHelperAnimatorTotalFrames",
        "navHelperProcessEvents", "navHelperManagesCursor", "navHelperPriority",
    )
    meta = Qt3D0.staticMetaObject
    missing = [name for name in names if meta.indexOfProperty(name) < 0]
    assert not missing, f"Qt3D0 is missing properties: {missing}"

    for name in names:
        prop = meta.property(meta.indexOfProperty(name))
        assert prop.isResettable(), f"{name} should preserve Designer reset behavior"


def test_view_slots_are_safe_before_a_program_is_loaded(monkeypatch):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.setattr(module, "LinuxCncDataSource", _FakeDatasource)
    monkeypatch.setattr(module, "linuxcnc", SimpleNamespace(stat=_FakeStat))
    monkeypatch.setattr(module, "connectSetting", lambda *args, **kwargs: None)

    widget = Qt3D0()
    try:
        # No program has been loaded yet; every view slot must still work.
        widget.setViewProgram("p")
        widget.setViewOrtho()
        widget.setViewPersp()
        widget.setViewMachine()
        widget.setViewP()
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_qt3d0_exposes_the_expected_slots():
    """Slots kept for .ui/programmatic compatibility must exist on Qt3D0."""
    backplot_slots = (
        "alphaBlend", "clearLivePlot", "enableBreadcrumbs", "enableMultiTouch",
        "enable_panning", "on_run_state_changed", "printView",
        "reapplyNavHelperConfig", "reload_program",
        "setProgramViewWhenLoadingProgram", "setView", "setViewMachine",
        "setViewOrtho", "setViewP", "setViewPath", "setViewPersp",
        "setViewProgram", "setViewX", "setViewXZ", "setViewXZ2", "setViewY",
        "setViewZ", "setViewZ2", "showFPS", "showGrid", "showMachine",
        "showMachineBounds", "showMachineLabels", "showMachineTicks",
        "showMultiColorPath", "showProgramBounds", "showSpindle", "showSurface",
        "toggleMachineBounds", "toggleMachineLabels", "toggleMachineTicks",
        "toggleMultiColorPath", "toggleProgramBounds", "viewPerspective",
        "zoomIn", "zoomOut",
    )
    backplot_properties = (
        "backgroundColor", "backgroundColor2", "enableProgramTicks",
        "traverseColor", "arcfeedColor", "feedColor", "dwellColor", "userColor",
    )

    meta = Qt3D0.staticMetaObject
    method_names = {
        bytes(meta.method(i).name()).decode()
        for i in range(meta.methodCount())
    }
    missing_slots = [n for n in backplot_slots if n not in method_names]
    missing_props = [n for n in backplot_properties if meta.indexOfProperty(n) < 0]
    assert not missing_slots, f"Missing slots on Qt3D0: {missing_slots}"
    assert not missing_props, f"Missing properties on Qt3D0: {missing_props}"


def test_machine_parts_model_composes_and_animates():
    from PySide6.QtGui import QQuaternion, QVector3D

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.machine import (
        MachinePartsModel,
    )

    model = MachinePartsModel()
    model.load({
        "base": {"position": [10.0, 0.0, 0.0]},
        "table": {"position": [0.0, 0.0, 0.0], "axis": "C", "joint": 0,
                  "origin": [0.0, 0.0, 0.0]},
    })
    assert model.rowCount() == 2
    assert model.data(model.index(0, 0), model.PosRole) == QVector3D(10.0, 0.0, 0.0)

    before = model.data(model.index(1, 0), model.RotRole)
    model.apply_joint_values([90.0])
    after = model.data(model.index(1, 0), model.RotRole)
    assert isinstance(after, QQuaternion)
    assert after != before
    # CNC Z rotation maps to the scene's Y-up axis, so ~90 deg about Y.
    assert abs(abs(after.y()) - 0.7071) < 1e-3

    model.set_enabled(False)
    assert model.data(model.index(0, 0), model.VisibleRole) is False


def test_gltf_geometry_loads_from_glb(tmp_path):
    import json
    import struct

    import numpy as np

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot import machine

    positions = np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0]], dtype="<f4")
    indices = np.array([0, 1, 2], dtype="<u2")
    blob = positions.tobytes() + indices.tobytes()
    blob += b"\x00" * ((4 - len(blob) % 4) % 4)

    document = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [
            {"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}]}],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36},
            {"buffer": 0, "byteOffset": 36, "byteLength": 6},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
    }
    json_chunk = json.dumps(document).encode()
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    body = (struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk
            + struct.pack("<II", len(blob), 0x004E4942) + blob)
    glb = struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body
    path = tmp_path / "tri.glb"
    path.write_bytes(glb)

    from PySide6.QtGui import QVector3D

    geometry = machine._gltf_geometry(str(path))
    assert geometry is not None
    assert len(bytes(geometry.vertexData())) // geometry.stride() == 3
    assert geometry.stride() == 24        # position + normal, interleaved
    assert geometry.boundsMax() == QVector3D(10, 10, 0)


def test_machine_parts_dh_animation_moves_links():
    import numpy as np

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.machine import (
        MachinePartsModel,
    )

    model = MachinePartsModel()
    model.load({
        "root": {"position": [0, 0, 0, 0, 0, 0]},
        "link1": {"type": "angular", "joint": 0, "position": [0, 0, 0, 0, 0, 0],
                  "mount": [100.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
    })
    assert model._dh_params == {0: (0.0, 100.0, 0.0)}

    link = next(p for p in model._parts if p.type == "angular")
    home = link.world.copy()
    assert np.allclose(home, np.eye(4))

    model.apply_joint_values([30.0])
    assert not np.allclose(link.world, home)
    # A pure rotation about the DH frame keeps the link's X offset.
    assert abs(link.world[0, 3] - 100.0) < 1e-6 or abs(link.world[1, 3]) > 1e-6


def test_machine_parts_skip_spindle_and_attach_ini_spindle():
    import numpy as np

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot import machine

    model = machine.MachinePartsModel()
    model.load({
        "root": {"position": [0, 0, 0, 0, 0, 0]},
        "link1": {"type": "angular", "joint": 0, "position": [0, 0, 0, 0, 0, 0],
                  "mount": [100.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
        "spindle": {"id": "spindle_htnc_0", "type": "static",
                    "model": "models/spindle_htnc_0.stl"},
    }, skip_ids=("spindle",))
    assert not any("spindle" in str(getattr(p, "type", "")) for p in model._parts)
    assert model.rowCount() == 2

    geometry = machine._geometry_from_arrays(
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype="float32"))
    model.set_spindle(geometry)
    assert model._spindle is not None
    assert model.rowCount() == 3

    model.apply_joint_values([45.0])
    link = next(p for p in model._parts if p.type == "angular")
    assert np.allclose(model._spindle.world, link.world)


def test_machine_part_position_is_mapped_to_z_up_scene():
    from PySide6.QtGui import QVector3D

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.machine import (
        MachinePartsModel,
    )

    model = MachinePartsModel()
    model.load({"a": {"type": "static", "position": [0, 0, 400, 0, 0, 0]}})
    index = model.index(0, 0)
    # CNC (0, 0, 400) -> scene Y-up (0, 400, 0): Z points up.
    assert model.data(index, model.PosRole) == QVector3D(0.0, 400.0, 0.0)


def test_machine_parts_world_bounds_include_arm_extent():
    import numpy as np

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot import machine

    model = machine.MachinePartsModel()
    model.load({"a": {"type": "angular", "joint": 0,
                      "position": [0, 0, 0, 0, 0, 0],
                      "mount": [0, 0, 0, 0, 0, 0]}})
    part = next(p for p in model._parts if p.type == "angular")
    part.geometry = machine._geometry_from_arrays(
        np.array([[-50, -50, 0], [50, 50, 0], [0, 0, 400]], dtype="float32"))
    model.apply_joint_values([0.0])

    low, high = model.world_bounds()
    assert low[2] == 0.0
    assert high[2] == 400.0
    assert high[2] > 1.0  # beyond a small cartesian machine box


def test_ray_segment_distances_picks_nearest():
    import numpy as np

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.paths import (
        ray_segment_distances,
    )

    origin = np.array([1.0, 0.5, 10.0], dtype=np.float64)
    direction = np.array([0.0, 0.0, -1.0], dtype=np.float64)
    starts = np.array([[0.0, 0.0, 0.0], [10.0, 10.0, 0.0]], dtype=np.float64)
    ends = np.array([[2.0, 0.0, 0.0], [12.0, 10.0, 0.0]], dtype=np.float64)

    distances, ray_t = ray_segment_distances(origin, direction, starts, ends)

    assert int(np.argmin(distances)) == 0
    assert distances[0] == pytest.approx(0.5)
    assert ray_t[0] == pytest.approx(10.0)


def test_ray_segment_distances_clamps_points_behind_the_ray():
    import numpy as np

    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.paths import (
        ray_segment_distances,
    )

    origin = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    direction = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    starts = np.array([[0.0, 0.0, -5.0]], dtype=np.float64)
    ends = np.array([[2.0, 0.0, -5.0]], dtype=np.float64)

    distances, ray_t = ray_segment_distances(origin, direction, starts, ends)

    assert distances[0] == pytest.approx(5.0)
    assert ray_t[0] == 0.0


def test_clip_planes_scale_with_scene_radius():
    rig = module.QuickCameraRig(module.Quick3DPlotData(), lambda: (), lambda: (1, 1))

    rig.set_scene_radius(5.0)          # inch-ish machine
    near_inch, far_inch = rig._clip_planes()
    rig.set_scene_radius(300.0)        # metric machine
    near_metric, far_metric = rig._clip_planes()

    for near, far in ((near_inch, far_inch), (near_metric, far_metric)):
        assert 0.0 < near < far
    # Larger scene -> larger far plane (proportional, not a fixed 1e6 span).
    assert far_metric > far_inch


def test_fit_bounds_adds_a_margin_around_the_bounds():
    import math

    rig = module.QuickCameraRig(module.Quick3DPlotData(), lambda: (), lambda: (1, 1))
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    rig.fit_bounds(bounds)

    half = math.sqrt(3 * 10.0 ** 2) * 0.5
    assert rig._scene_radius == pytest.approx(half * (1.0 + module.BOUNDS_MARGIN))


def test_tool_tip_applies_runtime_tool_offset(monkeypatch):
    from types import SimpleNamespace

    from PySide6.QtGui import QVector3D

    monkeypatch.setattr(module, "LinuxCncDataSource", _FakeDatasource)
    monkeypatch.setattr(module.Qt3D0, "_current_tool_number", lambda self: 1)
    monkeypatch.setattr(module.Qt3D0, "_current_tool_offset",
                        lambda self: (0.0, 0.0, 40.0, 0, 0, 0, 0, 0, 0))

    stat = SimpleNamespace(file="", tool_in_spindle=1, tool_offset=[0.0] * 9)
    monkeypatch.setattr(module, "linuxcnc", SimpleNamespace(stat=lambda: stat))
    monkeypatch.setattr(module, "connectSetting", lambda *args, **kwargs: None)

    widget = Qt3D0()
    try:
        widget.update_position((10.0, 20.0, 30.0))   # machine/gauge position
        # T1 dia 6 z-offset 40 -> radius 3, length 40; tip = z - 40 = -10,
        # body centre = -10 + 20 = 10 -> scene (x, z, -y) = (10, 10, -20).
        assert widget.plot_data.toolPosition == QVector3D(10.0, 10.0, -20.0)
    finally:
        widget.close()
        widget.deleteLater()


def test_tool_shape_from_tool_table():
    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot import tool

    table = [{"id": 1, "diameter": 6.0, "zoffset": 40.0}]
    shape = tool.tool_shape(table, 1, metric=True)
    assert shape.kind == "cylinder"
    assert shape.radius == 6.0 / 2.0
    assert shape.length == 40.0
    assert shape.visible

    no_tool = tool.tool_shape([{"id": 0, "diameter": 0.0, "zoffset": 0.0}], 0, metric=True)
    assert no_tool.kind == "cone"


def test_active_wcs_uses_live_offset_over_stale_table(monkeypatch):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.setattr(module, "LinuxCncDataSource", _OffsetDatasource)
    monkeypatch.setattr(module, "linuxcnc", SimpleNamespace(stat=_FakeStat))
    monkeypatch.setattr(module, "connectSetting", lambda *args, **kwargs: None)

    widget = Qt3D0()
    try:
        # The offset table is empty, so the active WCS must fall back to the
        # live status offset or the path would draw at program coordinates.
        assert widget._wcs_offsets(0) == (10.0, 20.0, 30.0, 0.0)
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_segment_role_indices_distinguishes_feed_and_arcfeed():
    import numpy as np
    from PySide6.QtGui import QColor

    cyan = {
        "traverse": "#0062d6",
        "feed": "#00e5ff",
        "arcfeed": "#7df6ff",
        "dwell": "#0091ff",
        "user": "#ff2bd6",
    }
    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot.paths import (
        segment_role_indices,
    )

    palette = np.asarray([QColor(cyan[role]).getRgb() for role in module.ROLE_NAMES],
                         dtype=np.int64)
    colors = np.asarray([[0, 229, 255, 255]] * 2 + [[125, 246, 255, 255]] * 3,
                        dtype=np.int64)

    indices = segment_role_indices(colors, palette)

    assert list(indices) == (
        [module.ROLE_NAMES.index("feed")] * 2
        + [module.ROLE_NAMES.index("arcfeed")] * 3
    )


def test_qt3d0_sets_plot_data_before_loading_qml(monkeypatch):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.setattr(module, "LinuxCncDataSource", _FakeDatasource)
    monkeypatch.setattr(module, "linuxcnc", SimpleNamespace(stat=_FakeStat))
    monkeypatch.setattr(module, "connectSetting", lambda *args, **kwargs: None)

    widget = Qt3D0()
    try:
        quick = widget.quick_widget
        assert quick.status() == module.QQuickWidget.Status.Ready
        assert quick.rootContext().contextProperty("plotData") is not None
        assert quick.rootContext().contextProperty("pathGroups") is not None
        assert quick.errors() == []
        # Children are destroyed in creation order, so the quick widget must
        # precede plot_data or QML bindings re-evaluate against a dead object.
        children = widget.children()
        assert children.index(quick) < children.index(widget.plot_data)
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


# -- settings / signal wiring ---------------------------------------------

def _make_widget(monkeypatch, datasource=_FakeDatasource):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.setattr(module, "LinuxCncDataSource", datasource)
    monkeypatch.setattr(module, "linuxcnc", SimpleNamespace(stat=_FakeStat))
    return app, Qt3D0()


def test_settings_bind_every_backplot_setting(monkeypatch):
    connected = []
    monkeypatch.setattr(module, "connectSetting",
                        lambda key, slot, *args, **kwargs: connected.append(key))
    app, widget = _make_widget(monkeypatch)
    try:
        expected = {
            "backplot.show-grid",
            "backplot.show-program-bounds",
            "backplot.show-machine-bounds",
            "backplot.show-machine-ticks",
            "backplot.show-machine-labels",
            "backplot.show-machine",
            "backplot.show-spindle",
            "backplot.multitool-colors",
            "backplot.show-points-surface",
            "backplot.show-fps",
            "backplot.view",
            "backplot.perspective-view",
        }
        assert expected.issubset(set(connected))
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_run_state_signal_drives_anchor_latch(monkeypatch):
    app, widget = _make_widget(monkeypatch)
    try:
        assert widget._program_running is False
        widget.datasource.program_running = True
        widget.datasource.runStateChanged.emit(True)
        assert widget._program_running is True
        assert widget._anchor_latched is True
        widget.datasource.program_running = False
        widget.datasource.runStateChanged.emit(False)
        assert widget._program_running is False
        assert widget._anchor_latched is False
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


# -- WCS placement, floating anchor, picking ------------------------------

def _feed_geometry():
    from qtpyvcp.widgets.display_widgets.backplot_common.geometry import (
        BackplotGeometry,
        PathGeometry,
    )

    points = np.asarray([
        [0.0, 0.0, 0.0], [10.0, 0.0, 0.0],
        [10.0, 0.0, 0.0], [10.0, 10.0, 0.0],
    ], dtype=np.float32)
    colors = np.tile(np.asarray([[210, 210, 255, 255]], dtype=np.uint8), (2, 1))
    return BackplotGeometry(paths={
        0: PathGeometry(wcs_index=0, points=points, colors=colors,
                        line_numbers=np.asarray([3, 4], dtype=np.int32)),
    })


def _install_geometry(widget, floating=False):
    widget._geometry = _feed_geometry()
    widget._floating_wcs = {0} if floating else set()
    widget._anchor_offset = (0.0, 0.0, 0.0) if floating else None
    widget._active_wcs_index = 0
    widget._active_wcs_offset = (0.0, 0.0, 0.0)
    widget._active_rotation = 0.0
    widget._rebuild_program_geometry()


def test_wcs_change_moves_rows_without_reuploading_vertices(monkeypatch):
    from PySide6.QtGui import QVector3D

    app, widget = _make_widget(monkeypatch)
    try:
        _install_geometry(widget)
        rows = widget.path_groups.rows()
        assert len(rows) == 1
        row = rows[0]
        assert row.role == "feed"
        assert row.starts.shape == (2, 3)
        before = bytes(row.geometry.vertexData())

        widget.datasource.g5xOffsetChanged.emit(
            (10.0, 20.0, 30.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

        assert bytes(row.geometry.vertexData()) == before
        assert row.position == QVector3D(10.0, 30.0, -20.0)
        assert widget._program_bounds[0] == pytest.approx(10.0)
        assert widget._program_bounds[1] == pytest.approx(20.0)
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_floating_wcs_tracks_then_latches_to_machine_position(monkeypatch):
    from PySide6.QtGui import QVector3D

    app, widget = _make_widget(monkeypatch)
    try:
        _install_geometry(widget, floating=True)
        row = widget.path_groups.rows()[0]
        assert row.position == QVector3D(0.0, 0.0, 0.0)

        widget.datasource.machine_position = (5.0, 6.0, 7.0)
        widget._update_floating_anchor()
        assert row.position == QVector3D(5.0, 7.0, -6.0)

        widget.datasource.machine_position = (8.0, 9.0, 10.0)
        widget.datasource.program_running = True
        widget.datasource.runStateChanged.emit(True)      # latch
        latched = QVector3D(row.position)

        widget.datasource.machine_position = (50.0, 60.0, 70.0)
        widget._update_floating_anchor()                  # still latched
        assert row.position == latched

        widget.datasource.program_running = False
        widget.datasource.runStateChanged.emit(False)     # release + track
        assert row.position == QVector3D(50.0, 70.0, -60.0)
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_click_picks_nearest_segment_and_emits_line(monkeypatch):
    from PySide6.QtGui import QVector3D

    app, widget = _make_widget(monkeypatch)
    try:
        _install_geometry(widget)
        selected = []
        widget.programLineSelected.connect(selected.append)

        # Scene ray equivalent to CNC (5, 0, 5) -> (5, 0, -5): it crosses the
        # first segment (0,0,0)-(10,0,0) at (5,0,0).
        widget.plot_data.reportPick(QVector3D(5.0, 5.0, 0.0),
                                    QVector3D(5.0, -5.0, 0.0))

        assert selected == [3]
        assert len(bytes(widget.plot_data.highlight.vertexData())) == 2 * 3 * 4
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_click_far_from_any_path_selects_nothing(monkeypatch):
    from PySide6.QtGui import QVector3D

    app, widget = _make_widget(monkeypatch)
    try:
        _install_geometry(widget)
        selected = []
        widget.programLineSelected.connect(selected.append)

        widget._on_picked(QVector3D(500.0, 500.0, 0.0),
                          QVector3D(500.0, -500.0, 0.0))

        assert selected == []
        assert len(bytes(widget.plot_data.highlight.vertexData())) == 0
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_selected_program_line_highlights_matching_segments(monkeypatch):
    app, widget = _make_widget(monkeypatch)
    try:
        _install_geometry(widget)
        widget._on_selected_program_lines([4])

        starts, _ends = widget.path_groups.segments_for_lines([4])
        assert starts.shape == (1, 3)
        assert len(bytes(widget.plot_data.highlight.vertexData())) == 2 * 3 * 4

        widget._on_selected_program_line(None)
        assert len(bytes(widget.plot_data.highlight.vertexData())) == 0
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_role_colour_change_does_not_reload_the_program(monkeypatch):
    from PySide6.QtGui import QColor

    app, widget = _make_widget(monkeypatch)
    try:
        _install_geometry(widget)
        calls = []
        monkeypatch.setattr(widget, "load_program",
                            lambda *args, **kwargs: calls.append(args))

        widget.feedColor = QColor("#123456")

        assert calls == []
        assert widget.path_groups.rows()[0].color == "#123456"
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_path_group_model_exposes_row_roles(monkeypatch):
    app, widget = _make_widget(monkeypatch)
    try:
        _install_geometry(widget)
        model = widget.path_groups
        row = model.rows()[0]
        index = model.index(0, 0)
        assert model.data(index, model.GeometryRole) is row.geometry
        assert model.data(index, model.ColorRole) == row.color
        assert model.data(index, model.PosRole) is row.position
        assert model.data(index, model.RotRole) is row.rotation
        assert model.data(model.index(99, 0), model.GeometryRole) is None

        # The QML Repeater3D must create one Model per row and bind its
        # geometry/transform roles.
        root = widget.quick_widget.rootObject()
        assert root is not None
        delegate = root.findChild(QtCore.QObject, "pathGroup")
        assert delegate is not None
        assert delegate.property("geometry") is row.geometry
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_background_colours_reach_the_qml_scene(monkeypatch):
    from PySide6.QtGui import QColor

    app, widget = _make_widget(monkeypatch)
    try:
        widget.backgroundColor = QColor("#102030")
        widget.backgroundColor2 = QColor("#405060")
        assert widget.plot_data.backgroundColor == "#102030"
        assert widget.plot_data.backgroundColor2 == "#405060"
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_placeholder_exposes_the_runtime_visibility_properties():
    from qtpyvcp.widgets.display_widgets.designer_plugins import Qt3D0Placeholder

    meta = Qt3D0Placeholder.staticMetaObject
    for name in ("gridVisible", "machineBoundsVisible", "programBoundsVisible",
                 "backgroundColor2", "traverseColor"):
        assert meta.indexOfProperty(name) >= 0

    placeholder = Qt3D0Placeholder()
    assert placeholder.machineBoundsVisible is True
    placeholder.gridVisible = True
    assert placeholder.gridVisible is True
    placeholder.deleteLater()


def test_load_program_builds_path_rows(monkeypatch, tmp_path):
    program = tmp_path / "part.ngc"
    program.write_text(
        "G21 G90 G54\n"
        "G0 X0 Y0 Z5\n"
        "G1 Z0 F100\n"
        "G1 X10 Y0\n"
        "G1 X10 Y10\n"
        "M30\n",
        encoding="utf-8",
    )

    app, widget = _make_widget(monkeypatch)
    try:
        widget.load_program(str(program))

        assert widget._geometry is not None
        rows = widget.path_groups.rows()
        assert rows
        assert widget._program_bounds is not None
        assert widget._program_bounds[0] == pytest.approx(0.0)
        assert widget._program_bounds[1] == pytest.approx(10.0)
        assert widget._program_bounds[3] == pytest.approx(10.0)

        for row in rows:
            assert row.role in module.ROLE_NAMES
            assert row.starts.shape[0] == row.line_numbers.size
            assert len(bytes(row.geometry.vertexData())) == row.starts.shape[0] * 2 * 3 * 4

        starts, _ends = widget.path_groups.segments_for_lines([4])
        assert starts.shape[0] >= 1
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_offset_transitions_are_drawn_and_follow_wcs_offsets(monkeypatch):
    from qtpyvcp.widgets.display_widgets.backplot_common.geometry import (
        BackplotGeometry,
        OffsetTransition,
        PathGeometry,
    )

    app, widget = _make_widget(monkeypatch)
    try:
        first = _feed_geometry().paths[0]
        second = PathGeometry(
            wcs_index=1,
            points=np.asarray([[0.0, 5.0, 0.0], [5.0, 5.0, 0.0]], np.float32),
            colors=np.tile(np.asarray([[210, 210, 255, 255]], np.uint8), (1, 1)),
            line_numbers=np.asarray([9], np.int32),
        )
        widget._geometry = BackplotGeometry(
            paths={0: first, 1: second},
            offset_transitions=[OffsetTransition(
                from_wcs=0, to_wcs=1, from_end=(10.0, 0.0, 0.0),
                to_start=(0.0, 5.0, 0.0))],
        )
        widget._floating_wcs = set()
        widget._anchor_offset = None
        widget._active_wcs_index = 0
        widget._active_wcs_offset = (0.0, 0.0, 0.0)
        widget._active_rotation = 0.0
        widget._rebuild_program_geometry()

        # Two segments (from -> elbow -> to) in the transition buffer.
        before = bytes(widget.plot_data.transitions.vertexData())
        assert len(before) == 4 * 3 * 4

        widget.datasource.g5xOffsetChanged.emit(
            (10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        assert bytes(widget.plot_data.transitions.vertexData()) != before
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_machine_part_rows_reach_the_qml_scene(monkeypatch):
    from qtpyvcp.widgets.display_widgets.qtquick3d_backplot import machine

    app, widget = _make_widget(monkeypatch)
    try:
        widget.machine_parts.load({"base": {"position": [1.0, 2.0, 3.0]}})
        part = widget.machine_parts._parts[0]
        part.geometry = machine._geometry_from_arrays(
            np.asarray([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                       dtype=np.float32))
        widget.machine_parts.apply_joint_values([0.0])
        app.processEvents()

        root = widget.quick_widget.rootObject()
        assert root is not None
        delegate = root.findChild(QtCore.QObject, "machinePart")
        assert delegate is not None
        assert delegate.property("geometry") is part.geometry
        assert delegate.property("visible") is True
        assert widget.quick_widget.errors() == []
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()


def test_wcs_rotation_maps_to_a_scene_y_rotation(monkeypatch):
    app, widget = _make_widget(monkeypatch)
    try:
        widget._geometry = _feed_geometry()
        widget._floating_wcs = set()
        widget._anchor_offset = None
        widget._active_wcs_index = 0
        widget._active_wcs_offset = (0.0, 0.0, 0.0)
        widget._active_rotation = 90.0
        widget._rebuild_program_geometry()

        row = widget.path_groups.rows()[0]
        # CNC +Z rotation maps to Quick 3D +Y; 90 degrees about Y.
        assert abs(abs(row.rotation.y()) - 0.70710678) < 1e-6
        world = row.world_point((1.0, 0.0, 0.0))
        assert world[0] == pytest.approx(0.0, abs=1e-9)
        assert world[1] == pytest.approx(1.0, abs=1e-9)
        assert world[2] == pytest.approx(0.0, abs=1e-9)
    finally:
        widget.close()
        widget.deleteLater()
        app.processEvents()
