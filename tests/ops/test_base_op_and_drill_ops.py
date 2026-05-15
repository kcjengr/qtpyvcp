import pytest


class TestBaseGeneratorInit:
    def test_default_wcs(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.wcs == ''

    def test_default_coolant(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.coolant == ''

    def test_default_units(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.units == ''

    def test_default_tool_number(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.tool_number == 0

    def test_default_spindle_rpm(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.spindle_rpm == 0.0

    def test_default_spindle_dir(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.spindle_dir == 'cw'

    def test_default_z_start(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.z_start == 0.0

    def test_default_z_end(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.z_end == 0.0

    def test_default_retract(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.retract == 0.0

    def test_default_z_feed(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.z_feed == 0.0

    def test_default_z_clear(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.z_clear == 0.0

    def test_default_xy_feed(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        ops = BaseGenerator()
        assert ops.xy_feed == 0.0


class TestBaseGeneratorStartOp:
    def setup_method(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        self.ops = BaseGenerator()

    def test_inch_units_produce_g20(self):
        self.ops.units = 'in'
        result = self.ops._start_op()
        assert 'G20' in result

    def test_metric_units_produce_g21(self):
        self.ops.units = 'mm'
        result = self.ops._start_op()
        assert 'G21' in result

    def test_cw_spindle_produces_m3(self):
        self.ops.spindle_dir = 'cw'
        result = self.ops._start_op()
        assert 'M3' in result

    def test_ccw_spindle_produces_m4(self):
        self.ops.spindle_dir = 'ccw'
        result = self.ops._start_op()
        assert 'M4' in result

    def test_coolant_mist_produces_m7(self):
        self.ops.coolant = 'mist'
        result = self.ops._start_op()
        assert 'M7' in result

    def test_coolant_flood_produces_m8(self):
        self.ops.coolant = 'flood'
        result = self.ops._start_op()
        assert 'M8' in result

    def test_coolant_air_blast_produces_m7(self):
        self.ops.coolant = 'air blast'
        result = self.ops._start_op()
        assert 'M7' in result

    def test_coolant_vacuum_produces_m8(self):
        self.ops.coolant = 'vacuum'
        result = self.ops._start_op()
        assert 'M8' in result

    def test_coolant_both_produces_m7_and_m8(self):
        self.ops.coolant = 'both'
        result = self.ops._start_op()
        assert 'M7' in result and 'M8' in result

    def test_no_coolant_skips_m7_m8(self):
        self.ops.coolant = ''
        result = self.ops._start_op()
        coolant_lines = [l for l in result if 'M7' in l or 'M8' in l]
        assert len(coolant_lines) == 0

    def test_tool_change_includes_t_and_m6(self):
        self.ops.tool_number = 5
        result = self.ops._start_op()
        assert 'T5 M6 G43' in result

    def test_spindle_rpm_formatting(self):
        self.ops.spindle_rpm = 3000.5
        result = self.ops._start_op()
        assert 'S3000.5000' in result

    def test_xy_feed_formatting(self):
        self.ops.xy_feed = 100.25
        result = self.ops._start_op()
        assert 'F100.2500' in result

    def test_wcs_included_as_is(self):
        self.ops.wcs = 'G54'
        result = self.ops._start_op()
        assert 'G54' in result


class TestBaseGeneratorEndOp:
    def setup_method(self):
        from qtpyvcp.ops.base_op import BaseGenerator
        self.ops = BaseGenerator()

    def test_coolant_on_produces_m9(self):
        self.ops.coolant = 'flood'
        result = self.ops._end_op()
        assert 'M9' in result

    def test_no_coolant_skips_m9(self):
        self.ops.coolant = ''
        result = self.ops._end_op()
        m9_lines = [l for l in result if 'M9' in l]
        assert len(m9_lines) == 0

    def test_ends_with_z_clear_retract(self):
        self.ops.z_clear = 0.5
        result = self.ops._end_op()
        assert 'G0 Z0.5000' in result

    def test_z_clear_formatting(self):
        self.ops.z_clear = 1.2345
        result = self.ops._end_op()
        assert 'G0 Z1.2345' in result


class TestDrillOpsInit:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()

    def test_default_retract_mode(self):
        assert self.ops.retract_mode == 'G98'

    def test_default_holes_is_empty_list(self):
        assert self.ops.holes == []


class TestDrillOpsDrill:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0)]

    def test_drill_returns_list(self):
        result = self.ops.drill()
        assert isinstance(result, list)

    def test_drill_contains_g81(self):
        result = self.ops.drill()
        assert any('G81' in line for line in result)

    def test_drill_contains_retreat_mode(self):
        result = self.ops.drill()
        assert any('G98' in line for line in result)

    def test_drill_contains_z_end(self):
        result = self.ops.drill()
        assert any('-0.5000' in line for line in result)

    def test_drill_contains_feed_rate(self):
        result = self.ops.drill()
        assert any('F10.0000' in line for line in result)


class TestDrillOpsDwell:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0)]

    def test_dwell_returns_list(self):
        result = self.ops.dwell(0.5)
        assert isinstance(result, list)

    def test_dwell_contains_g82(self):
        result = self.ops.dwell(0.5)
        assert any('G82' in line for line in result)

    def test_dwell_contains_p_parameter(self):
        result = self.ops.dwell(0.5)
        assert any('P0.5000' in line for line in result)

    def test_dwell_default_dwell_time_is_zero(self):
        result = self.ops.dwell()
        assert any('P0.0000' in line for line in result)


class TestDrillOpsPeck:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0)]

    def test_peck_returns_list(self):
        result = self.ops.peck(0.1)
        assert isinstance(result, list)

    def test_peck_contains_g83(self):
        result = self.ops.peck(0.1)
        assert any('G83' in line for line in result)

    def test_peck_contains_q_parameter(self):
        result = self.ops.peck(0.1)
        assert any('Q0.1000' in line for line in result)


class TestDrillOpsChipBreak:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0)]

    def test_chip_break_returns_list(self):
        result = self.ops.chip_break(0.1)
        assert isinstance(result, list)

    def test_chip_break_contains_g73(self):
        result = self.ops.chip_break(0.1)
        assert any('G73' in line for line in result)


class TestDrillOpsTap:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 480
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0)]

    def test_tap_right_hand_with_positive_rpm(self):
        self.ops.spindle_dir = 'cw'
        result = self.ops.tap(1 / 20)
        assert any('G84' in line for line in result)

    def test_tap_left_hand_with_negative_rpm(self):
        self.ops.spindle_dir = 'ccw'
        self.ops.spindle_rpm = -480
        result = self.ops.tap(1 / 20)
        assert any('G74' in line for line in result)

    def test_tap_calculates_feed_from_rpm_and_pitch(self):
        self.ops.spindle_dir = 'cw'
        self.ops.spindle_rpm = 100
        result = self.ops.tap(1 / 10)
        feed_line = [l for l in result if 'F10.0000' in l]
        assert len(feed_line) > 0

    def test_tap_abs_spindle_rpm_in_output(self):
        self.ops.spindle_dir = 'cw'
        self.ops.spindle_rpm = -500
        result = self.ops.tap(1 / 10)
        assert any('S500.0000' in line for line in result)


class TestDrillOpsRigidTap:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0)]

    def test_rigid_tap_returns_list(self):
        result = self.ops.rigid_tap(0.05)
        assert isinstance(result, list)

    def test_rigid_tap_contains_g33_1(self):
        result = self.ops.rigid_tap(0.05)
        assert any('G33.1' in line for line in result)

    def test_rigid_tap_contains_z_end(self):
        result = self.ops.rigid_tap(0.05)
        assert any('Z-0.5000' in line for line in result)

    def test_rigid_tap_contains_k_pitch(self):
        result = self.ops.rigid_tap(0.05)
        assert any('K0.0500' in line for line in result)


class TestDrillOpsManual:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(1.0, 2.0), (3.0, 4.0)]

    def test_manual_returns_list(self):
        result = self.ops.manual()
        assert isinstance(result, list)

    def test_manual_contains_tool_change(self):
        result = self.ops.manual()
        assert any('T1 M6' in line for line in result)

    def test_manual_goes_to_each_hole(self):
        result = self.ops.manual()
        x_lines = [l for l in result if 'X1.0000 Y2.0000' in l]
        assert len(x_lines) > 0


class TestDrillOpsHoleCircle:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()

    def test_add_hole_circle_zero_holes_returns_early(self):
        self.ops.add_hole_circle(0, 5.0, (0.0, 0.0))
        assert self.ops.holes == []

    def test_add_hole_circle_one_hole(self):
        self.ops.add_hole_circle(1, 5.0, (0.0, 0.0))
        assert len(self.ops.holes) == 1

    def test_add_hole_circle_four_holes(self):
        self.ops.add_hole_circle(4, 5.0, (0.0, 0.0), 0)
        assert len(self.ops.holes) == 4

    def test_add_hole_circle_positions_on_circle(self):
        self.ops.add_hole_circle(4, 10.0, (0.0, 0.0), 0)
        assert len(self.ops.holes) == 4
        x_coords = [h[0] for h in self.ops.holes]
        y_coords = [h[1] for h in self.ops.holes]
        assert max(x_coords) > 0
        assert min(x_coords) < 0

    def test_add_hole_circle_with_offset_center(self):
        center = (5.0, 5.0)
        self.ops.add_hole_circle(4, 10.0, center, 0)
        x_coords = [h[0] for h in self.ops.holes]
        avg_x = sum(x_coords) / len(x_coords)
        assert abs(avg_x - 5.0) < 0.01

    def test_add_hole_circle_start_angle(self):
        self.ops.add_hole_circle(4, 10.0, (0.0, 0.0), 90)
        first_hole = self.ops.holes[0]
        assert abs(first_hole[0]) < 0.01

    def test_add_hole_circle_num_holes_abs_value(self):
        self.ops.add_hole_circle(-4, 5.0, (0.0, 0.0))
        assert len(self.ops.holes) == 4


class TestDrillOpsRetreatMode:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0)]

    def test_g98_retreat_mode_in_drill(self):
        result = self.ops.drill()
        assert any('G98' in line for line in result)

    def test_g99_retreat_mode_in_drill(self):
        self.ops.retract_mode = 'G99'
        result = self.ops.drill()
        assert any('G99' in line for line in result)


class TestDrillOpsMultipleHoles:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100
        self.ops.holes = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]

    def test_multiple_holes_skip_first_g0(self):
        result = self.ops.drill()
        g0_lines = [l for l in result if 'G0 X' in l]
        assert len(g0_lines) == 1

    def test_multiple_holes_x_only_moves(self):
        result = self.ops.drill()
        x_only = [l for l in result if l.strip().startswith('X') and 'Y' in l]
        assert len(x_only) == 2

    def test_drill_contains_g80_cancel(self):
        result = self.ops.drill()
        assert 'G80' in result


class TestDrillOpsEmptyHoles:
    def setup_method(self):
        from qtpyvcp.ops.drill_ops import DrillOps
        self.ops = DrillOps()
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 3000
        self.ops.z_start = 0.1
        self.ops.z_end = -0.5
        self.ops.z_feed = 10
        self.ops.xy_feed = 100

    def test_drill_with_no_holes_returns_start_and_end_only(self):
        result = self.ops.drill()
        assert len(result) > 0

    def test_manual_with_no_holes_skips_x_y_moves(self):
        result = self.ops.manual()
        x_lines = [l for l in result if 'G0 X' in l]
        assert len(x_lines) == 0
