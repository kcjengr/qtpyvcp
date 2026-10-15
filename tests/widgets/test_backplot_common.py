"""Regression tests for the renderer-independent backplot layer.

These pin the coordinate math that both the VTK and Qt3D backplots depend on:
unit normalisation, work-offset handling, rotary helper math, and the
segment/colour bookkeeping.  They use a fake datasource so they run without a
live LinuxCNC session.
"""


from types import SimpleNamespace

import numpy as np
import pytest

from qtpyvcp.widgets.display_widgets.backplot_common.canon import (
    DEFAULT_ROLE_COLORS,
    BackplotCanon,
)
from qtpyvcp.widgets.display_widgets.backplot_common.geometry import (
    BackplotGeometry,
    PathGeometry,
)
from qtpyvcp.widgets.display_widgets.backplot_common.loader import _unitcode, load_geometry


class FakeStat:
    def __init__(self, metric=True):
        self.tool_table = []
        self.linear_units = 1.0 if metric else (1.0 / 25.4)
        self.angular_units = 1.0
        self.axis_mask = 7
        self.block_delete = 0

    def poll(self):
        return 0


class FakeDatasource:
    def __init__(self, metric=False, foam=False, owners=None, origins=None):
        self._metric = metric
        self._foam = foam
        self._owners = owners or {}
        self._origins = origins or {'A': None, 'B': None, 'C': None}
        self._status = SimpleNamespace(stat=FakeStat(metric=metric))
        self.config_dir = None
        self._inifile = None

    def isMachineMetric(self):
        return self._metric

    def isMachineFoam(self):
        return self._foam

    def isMachineLathe(self):
        return False

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

    def getAxisMotionOwners(self):
        return dict(self._owners)

    def getRotaryAxisOrigins(self):
        return dict(self._origins)

    def getProgramUnits(self):
        return 'G20' if not self._metric else 'G21'

    def getAxisMask(self):
        return 7

    def getToolTable(self):
        return []


def make_canon(metric=False):
    return BackplotCanon(FakeDatasource(metric=metric), colors=DEFAULT_ROLE_COLORS,
                         stat=FakeStat(metric=metric))


# -- unit handling ---------------------------------------------------------

def test_metric_machine_scales_by_25_4():
    canon = make_canon(metric=True)
    assert canon._program_to_machine_length_factor() == pytest.approx(25.4)


def test_inch_machine_uses_unit_factor():
    canon = make_canon(metric=False)
    assert canon._program_to_machine_length_factor() == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("machine_metric", "gcode_units", "distance", "expected_machine_distance"),
    [
        (True, "G20", 1.0, 25.4),       # 1 inch on a metric machine -> 25.4 mm
        (True, "G21", 25.4, 25.4),      # 25.4 mm on a metric machine -> 25.4 mm
        (False, "G20", 1.0, 1.0),       # 1 inch on an inch machine -> 1 inch
        (False, "G21", 25.4, 1.0),      # 25.4 mm on an inch machine -> 1 inch
    ],
)
@pytest.mark.parametrize("prefer_native", [True, False])
def test_g20_and_g21_paths_use_machine_units(
        tmp_path, machine_metric, gcode_units, distance, expected_machine_distance,
        prefer_native):
    datasource = FakeDatasource(metric=machine_metric)
    datasource.config_dir = str(tmp_path)
    filename = tmp_path / "units.ngc"
    filename.write_text(
        f"{gcode_units} G90\n"
        "G0 X0 Y0 Z0\n"
        f"G1 X{distance} Y0 Z0 F10\n"
        "M2\n",
        encoding="utf-8",
    )

    geometry = load_geometry(str(filename), datasource, prefer_native=prefer_native)

    assert geometry is not None
    assert geometry.paths[0].bounds()[1] == pytest.approx(expected_machine_distance)


@pytest.mark.parametrize(
    ("machine_metric", "gcode_units", "radius", "expected_machine_radius"),
    [
        (True, "G20", 1.0, 25.4),
        (True, "G21", 25.4, 25.4),
        (False, "G20", 1.0, 1.0),
        (False, "G21", 25.4, 1.0),
    ],
)
@pytest.mark.parametrize("prefer_native", [True, False])
def test_g20_and_g21_arcs_use_machine_units(
        tmp_path, machine_metric, gcode_units, radius, expected_machine_radius,
        prefer_native):
    datasource = FakeDatasource(metric=machine_metric)
    datasource.config_dir = str(tmp_path)
    filename = tmp_path / "arc_units.ngc"
    filename.write_text(
        f"{gcode_units} G90 G17\n"
        f"G0 X{radius} Y0 Z0\n"
        f"G3 X0 Y{radius} I{-radius} J0 F10\n"
        "M2\n",
        encoding="utf-8",
    )

    geometry = load_geometry(str(filename), datasource, prefer_native=prefer_native)

    assert geometry is not None
    bounds = geometry.paths[0].bounds()
    assert bounds[1] == pytest.approx(expected_machine_radius, rel=1e-5)
    assert bounds[3] == pytest.approx(expected_machine_radius, rel=1e-5)


@pytest.mark.parametrize(("ini_units", "expected_unitcode"),
                         [("mm", "G21"), ("inch", "G20")])
def test_unitcode_ini_fallback_matches_machine_units(ini_units, expected_unitcode):
    datasource = FakeDatasource(metric=(ini_units == "mm"))
    datasource._status = None
    datasource._inifile = SimpleNamespace(
        find=lambda section, key: ini_units
        if (section, key) == ("TRAJ", "LINEAR_UNITS") else None
    )
    assert _unitcode(datasource) == expected_unitcode


@pytest.mark.parametrize("prefer_native", [True, False])
def test_custom_feed_color_reaches_shared_geometry(tmp_path, prefer_native):
    datasource = FakeDatasource(metric=True)
    datasource.config_dir = str(tmp_path)
    filename = tmp_path / "colored.ngc"
    filename.write_text(
        "G21 G90\nG0 X0 Y0 Z0\nG1 X5 Y0 Z0 F10\nM2\n",
        encoding="utf-8",
    )
    feed_rgba = (19, 87, 143, 255)

    geometry = load_geometry(
        str(filename), datasource, colors={"feed": feed_rgba},
        prefer_native=prefer_native,
    )

    assert geometry is not None
    path = geometry.paths[0]
    assert any(tuple(color) == feed_rgba for color in path.colors)


def test_scale_linear_axes_only_touches_linear_indices():
    scaled = BackplotCanon._scale_linear_axes([1, 2, 3, 4, 5, 6, 7, 8, 9], 10.0)
    # indices 0,1,2 and 6,7,8 scale; rotary a,b,c (3,4,5) do not.
    assert scaled == [10, 20, 30, 4, 5, 6, 70, 80, 90]


# -- rotary helpers --------------------------------------------------------

def test_rotate_about_x_axis():
    out = BackplotCanon._rotate_point_about_axis((0, 1, 0), (0, 0, 0), 'A', 90.0)
    assert out[0] == pytest.approx(0.0)
    assert out[1] == pytest.approx(0.0, abs=1e-9)
    assert out[2] == pytest.approx(1.0)


def test_rotate_about_z_axis_about_pivot():
    out = BackplotCanon._rotate_point_about_axis((2, 1, 5), (1, 1, 5), 'C', 90.0)
    assert out[0] == pytest.approx(1.0)
    assert out[1] == pytest.approx(2.0)
    assert out[2] == pytest.approx(5.0)


def test_rotary_delta_wrapped_takes_shortest_path():
    assert BackplotCanon._rotary_delta_deg(350.0, 10.0, wrapped=True) == pytest.approx(20.0)
    assert BackplotCanon._rotary_delta_deg(10.0, 350.0, wrapped=True) == pytest.approx(-20.0)
    assert BackplotCanon._rotary_delta_deg(10.0, 350.0, wrapped=False) == pytest.approx(340.0)


# -- geometry bookkeeping --------------------------------------------------

def _feed(canon, start, end):
    """Drive a straight feed from *start* to *end* (canon unit tuples)."""
    canon.path_initialized = True
    canon.first_move = False
    canon.last_pos = list(start)
    canon.straight_feed(*end)


def test_geometry_segment_and_color_lengths_match():
    canon = make_canon(metric=False)
    canon.set_g5x_offset(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    _feed(canon, (0, 0, 0, 0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0, 0))
    _feed(canon, (1, 0, 0, 0, 0, 0, 0, 0, 0), (1, 1, 0, 0, 0, 0, 0, 0, 0))

    geometry = canon.build_geometry()
    assert geometry.has_paths
    path = geometry.paths[canon._active_wcs_index]
    assert path.segment_count == 2
    assert path.colors.shape == (2, 4)
    assert path.line_numbers.shape == (2,)
    assert path.points.shape == (4, 3)


def test_offset_transition_when_wcs_changes():
    canon = make_canon(metric=False)
    canon.set_g5x_offset(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    _feed(canon, (0, 0, 0, 0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0, 0))
    canon.set_g5x_offset(2, 5, 5, 0, 0, 0, 0, 0, 0, 0)
    _feed(canon, (0, 0, 0, 0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0, 0))

    geometry = canon.build_geometry()
    assert len(geometry.paths) == 2
    assert len(geometry.offset_transitions) == 1
    assert geometry.offset_transitions[0].from_wcs == 0
    assert geometry.offset_transitions[0].to_wcs == 1


# -- geometry containers ---------------------------------------------------

def test_empty_geometry_bounds():
    geometry = BackplotGeometry()
    assert geometry.bounds() is None
    assert not geometry.has_paths


def test_path_bounds_and_segment_lookup():
    points = np.array([[0, 0, 0], [1, 2, 3]], dtype=np.float32)
    path = PathGeometry(0, points,
                        np.zeros((2, 4), dtype=np.uint8),
                        np.array([7], dtype=np.int32))
    assert path.bounds() == (0.0, 1.0, 0.0, 2.0, 0.0, 3.0)
    start, end = path.segment(0)
    assert tuple(start) == (0.0, 0.0, 0.0)
    assert tuple(end) == (1.0, 2.0, 3.0)
    assert path.segment(5) is None
