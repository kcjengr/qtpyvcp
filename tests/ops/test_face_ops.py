import pytest
from qtpyvcp.ops.face_ops import FaceOps


class TestFaceOpsInit:
    def test_default_tool_diameter(self):
        ops = FaceOps()
        assert ops.tool_diameter == 0.

    def test_default_step_over(self):
        ops = FaceOps()
        assert ops.step_over == 0.

    def test_default_step_down(self):
        ops = FaceOps()
        assert ops.step_down == 0.

    def test_default_dimensions(self):
        ops = FaceOps()
        assert ops.x_start == 0
        assert ops.x_end == 0
        assert ops.y_start == 0
        assert ops.y_end == 0


class TestFaceGcodeGeneration:
    def setup_method(self):
        self.ops = FaceOps()
        self.ops.tool_diameter = 1.0
        self.ops.step_over = 2.0
        self.ops.step_down = 0.5
        self.ops.x_start = 0.0
        self.ops.x_end = 10.0
        self.ops.y_start = 0.0
        self.ops.y_end = 4.0
        self.ops.z_start = 0.0
        self.ops.z_end = -1.5
        self.ops.retract = 0.1
        self.ops.z_clear = 0.2
        self.ops.tool_number = 1
        self.ops.spindle_rpm = 5000
        self.ops.xy_feed = 100
        self.ops.units = 'in'
        self.ops.coolant = 'flood'

    def test_face_returns_list(self):
        result = self.ops.face()
        assert isinstance(result, list)

    def test_face_starts_with_start_op_preamble(self):
        result = self.ops.face()
        assert any('T1 M6' in line for line in result)
        assert any('S5000.0000' in line for line in result)
        assert any('M3' in line for line in result)

    def test_face_ends_with_end_op_cleanup(self):
        result = self.ops.face()
        assert any('M9' in line for line in result)
        assert any('G0 Z0.2000' in line for line in result)

    def test_contains_ramp_arc_entry(self):
        result = self.ops.face()
        ramp_lines = [l for l in result if 'G18 G2' in l and 'Z' in l]
        assert len(ramp_lines) > 0

    def test_contains_zigzag_passes(self):
        result = self.ops.face()
        zigzag_lines = [l for l in result if 'G17' in l]
        assert len(zigzag_lines) > 0

    def test_contains_g1_linear_moves(self):
        result = self.ops.face()
        g1_lines = [l for l in result if l.startswith('G1 X')]
        assert len(g1_lines) > 0

    def test_num_step_down_layers(self):
        """depth=1.5, step_down=0.5 -> 3 layers"""
        self.ops.z_end = -1.5
        self.ops.step_down = 0.5
        result = self.ops.face()
        ramp_entries = [l for l in result if 'G18 G2' in l and 'Z' in l]
        assert len(ramp_entries) == 3

    def test_num_z_clear_retractions(self):
        """3 layers -> 2 clear retractions between layers + 1 from end_op = 3 total"""
        self.ops.z_end = -1.5
        self.ops.step_down = 0.5
        result = self.ops.face()
        clear_moves = [l for l in result if 'G0 Z0.2000' in l]
        assert len(clear_moves) == 3

    def test_face_with_negative_dimensions(self):
        """Negative dimensions should still work (abs() used internally)"""
        self.ops.x_start = 10.0
        self.ops.x_end = 0.0
        self.ops.y_start = 4.0
        self.ops.y_end = 0.0
        self.ops.z_start = -1.5
        self.ops.z_end = 0.0
        result = self.ops.face()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_face_contains_tool_change(self):
        result = self.ops.face()
        assert any('T1 M6' in line for line in result)

    def test_face_contains_xy_feed(self):
        result = self.ops.face()
        assert any('F100.0000' in line for line in result)


class TestBaseGeneratorStartOp:
    def setup_method(self):
        self.ops = FaceOps()
        self.ops.units = 'in'
        self.ops.tool_number = 5
        self.ops.spindle_rpm = 3000
        self.ops.spindle_dir = 'cw'

    def test_inch_units_produce_g20(self):
        result = self.ops._start_op()
        assert any('G20' in line for line in result)

    def test_metric_units_produce_g21(self):
        self.ops.units = 'mm'
        result = self.ops._start_op()
        assert any('G21' in line for line in result)

    def test_cw_spindle_produces_m3(self):
        self.ops.spindle_dir = 'cw'
        result = self.ops._start_op()
        assert any('M3' in line for line in result)

    def test_ccw_spindle_produces_m4(self):
        self.ops.spindle_dir = 'ccw'
        result = self.ops._start_op()
        assert any('M4' in line for line in result)

    def test_coolant_mist_produces_m7(self):
        self.ops.coolant = 'mist'
        result = self.ops._start_op()
        assert any('M7' in line for line in result)

    def test_coolant_flood_produces_m8(self):
        self.ops.coolant = 'flood'
        result = self.ops._start_op()
        assert any('M8' in line for line in result)

    def test_no_coolant_skips_m7_m8(self):
        self.ops.coolant = ''
        result = self.ops._start_op()
        coolant_lines = [l for l in result if 'M7' in l or 'M8' in l]
        assert len(coolant_lines) == 0


class TestBaseGeneratorEndOp:
    def setup_method(self):
        self.ops = FaceOps()

    def test_coolant_on_produces_m9(self):
        self.ops.coolant = 'flood'
        result = self.ops._end_op()
        assert any('M9' in line for line in result)

    def test_no_coolant_skips_m9(self):
        self.ops.coolant = ''
        result = self.ops._end_op()
        m9_lines = [l for l in result if 'M9' in l]
        assert len(m9_lines) == 0

    def test_ends_with_z_clear_retract(self):
        self.ops.z_clear = 0.5
        result = self.ops._end_op()
        assert any('G0 Z0.5000' in line for line in result)
