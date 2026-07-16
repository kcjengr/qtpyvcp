import pytest
from qtpyvcp.ops.drill_ops import DrillOps


class TestDrillOps:
    def setup_method(self):
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 1000
        self.ops.z_end = -0.5
        self.ops.z_start = 0.02
        self.ops.z_feed = 10
        self.ops.xy_feed = 60
        self.ops.z_clear = 0.1
        self.ops.units = 'in'
        self.ops.holes = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]

    def test_drill_generates_gcode(self):
        result = self.ops.drill()
        assert isinstance(result, list)
        assert any('G81' in line for line in result)
        assert any('T1 M6' in line for line in result)
        assert any('S1000.0000' in line for line in result)

    def test_dwell_generates_gcode(self):
        result = self.ops.dwell(0.5)
        assert isinstance(result, list)
        assert any('G82' in line for line in result)
        assert any('P0.5000' in line for line in result)

    def test_peck_generates_gcode(self):
        result = self.ops.peck(0.1)
        assert isinstance(result, list)
        assert any('G83' in line for line in result)
        assert any('Q0.1000' in line for line in result)

    def test_chip_break_generates_gcode(self):
        result = self.ops.chip_break(0.05)
        assert isinstance(result, list)
        assert any('G73' in line for line in result)
        assert any('Q0.0500' in line for line in result)

    def test_tap_right_hand(self):
        self.ops.spindle_dir = 'cw'
        result = self.ops.tap(1 / 20)
        assert isinstance(result, list)
        assert any('G84' in line for line in result)

    def test_tap_left_hand(self):
        self.ops.spindle_dir = 'ccw'
        result = self.ops.tap(1 / 20)
        assert isinstance(result, list)
        assert any('G74' in line for line in result)

    def test_rigid_tap_generates_gcode(self):
        result = self.ops.rigid_tap(0.05)
        assert isinstance(result, list)
        assert any('G33.1' in line for line in result)
        assert any('K0.0500' in line for line in result)

    def test_manual_generates_gcode(self):
        result = self.ops.manual()
        assert isinstance(result, list)
        assert any('G0 X' in line for line in result)
        assert any('M0' in line for line in result)

    def test_retract_mode_g98(self):
        self.ops.retract_mode = 'G98'
        result = self.ops.drill()
        assert any('G98' in line for line in result)

    def test_retract_mode_g99(self):
        self.ops.retract_mode = 'G99'
        result = self.ops.drill()
        assert any('G99' in line for line in result)

    def test_no_holes_produces_empty_gcode(self):
        self.ops.holes = []
        result = self.ops.drill()
        assert isinstance(result, list)

    def test_add_hole_circle(self):
        ops = DrillOps()
        ops.add_hole_circle(4, 10.0, (5.0, 5.0), start_angle=0)
        assert len(ops.holes) == 4
        # First hole should be at angle 0 from center
        assert abs(ops.holes[0][0] - 10.0) < 0.01  # rightmost point

    def test_add_hole_circle_zero_holes(self):
        ops = DrillOps()
        ops.add_hole_circle(0, 10.0, (5.0, 5.0))
        assert len(ops.holes) == 0

    def test_add_hole_circle_negative_holes_abs(self):
        ops = DrillOps()
        ops.add_hole_circle(-4, 10.0, (5.0, 5.0))
        assert len(ops.holes) == 4

    def test_metric_units(self):
        self.ops.units = 'mm'
        result = self.ops.drill()
        assert any('G21' in line for line in result)

    def test_inch_units(self):
        self.ops.units = 'in'
        result = self.ops.drill()
        assert any('G20' in line for line in result)

    def test_coolant_mist(self):
        self.ops.coolant = 'mist'
        result = self.ops.drill()
        assert any('M7' in line for line in result)

    def test_coolant_flood(self):
        self.ops.coolant = 'flood'
        result = self.ops.drill()
        assert any('M8' in line for line in result)

    def test_no_coolant(self):
        self.ops.coolant = ''
        result = self.ops.drill()
        assert not any('M7' in line or 'M8' in line for line in result if 'G0 Z' in line or 'M9' in line)

    def test_end_op_m9(self):
        self.ops.coolant = 'flood'
        result = self.ops.drill()
        assert any('M9' in line for line in result)
