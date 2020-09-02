import unittest

from qtpyvcp.widgets.conversational.ops.drill_ops import DrillOps


class TestDrilling(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.sut = DrillOps()
        cls.sut.tool_number = 4
        cls.sut.spindle_rpm = 1200
        cls.sut.spindle_dir = 'cw'
        cls.sut.wcs = 'G55'
        cls.sut.coolant = ''
        cls.sut.retract = 0.02
        cls.sut.z_start = 1
        cls.sut.z_end = 0.5
        cls.sut.z_feed = 4.8
        cls.sut.z_clear = 0.2
        cls.sut.xy_feed = 60

    def test_should_drill_a_hole_at_the_given_location(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G98 G81 R1.0200 Z0.5000 F4.8000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.holes.append((4., 1.))
        op = self.sut.drill()
        self.assertEqual(op, expected_gcode)

    def test_should_drill_multiple_holes_at_the_given_locations(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G98 G81 R1.0200 Z0.5000 F4.8000',
            'X2.0000 Y0.0000',
            'X3.2000 Y-10.0100',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.holes.append((4., 1.))
        self.sut.holes.append((2., 0.))
        self.sut.holes.append((3.2, -10.01))
        self.assertEqual(self.sut.drill(), expected_gcode)

    def test_should_set_g20_when_unit_is_in(self):
        expected_gcode = [
            'G20',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.units = 'in'
        self.assertEqual(self.sut.drill(), expected_gcode)

    def test_should_set_g21_when_unit_is_mm(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.units = 'mm'
        self.assertEqual(self.sut.drill(), expected_gcode)

    def test_should_set_the_coolant_to_mist_when_specified(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'M7',
            'G80',
            'M9',
            'G0 Z0.2000'
        ]

        self.sut.coolant = 'mist'
        self.assertEqual(self.sut.drill(), expected_gcode)

    def test_should_set_the_coolant_to_flood_when_specified(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'M8',
            'G80',
            'M9',
            'G0 Z0.2000'
        ]

        self.sut.coolant = 'flood'
        self.assertEqual(self.sut.drill(), expected_gcode)

    def test_should_set_the_spindle_to_ccw_when_specified(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M4',
            'G55',
            'F60.0000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.spindle_dir = 'ccw'
        self.assertEqual(self.sut.drill(), expected_gcode)

    def test_dwell_should_use_a_g82_cycle(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G98 G82 R1.0200 Z0.5000 P0.5000 F4.8000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.holes.append((4., 1.))
        self.assertEqual(self.sut.dwell(0.5), expected_gcode)

    def test_peck_should_use_a_g83_cycle(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G98 G83 R1.0200 Z0.5000 Q0.1000 F4.8000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.holes.append((4., 1.))
        self.assertEqual(self.sut.peck(0.1), expected_gcode)

    def test_chip_break_should_use_a_g73_cycle(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G98 G73 R1.0200 Z0.5000 Q0.0500 F4.8000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.holes.append((4., 1.))
        self.assertEqual(expected_gcode, self.sut.chip_break(0.05))

    def test_right_hand_tap_should_use_a_g84_cycle(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S120.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G98 G84 R1.0200 Z0.5000 F6.0000 S120.0000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.spindle_rpm = 120
        self.sut.holes.append((4., 1.))
        self.assertEqual(self.sut.tap(0.05), expected_gcode)

    def test_left_hand_tap_should_use_a_g74_cycle(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S120.0000',
            'M4',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G98 G74 R1.0200 Z0.5000 F6.0000 S120.0000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.spindle_rpm = 120
        self.sut.spindle_dir = 'ccw'
        self.sut.holes.append((4., 1.))
        self.assertEqual(self.sut.tap(0.05), expected_gcode)

    def test_should_rigid_tap(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S120.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X4.0000 Y1.0000',
            'G0 Z0.2000',
            'G33.1 Z0.5000 K0.3125',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.spindle_rpm = 120
        self.sut.holes.append((4., 1.))
        self.assertEqual(self.sut.rigid_tap(0.3125), expected_gcode)

    def test_should_create_a_circle_with_evenly_spaced_holes(self):
        expected_gcode = [
            'G21',
            'T4 M6 G43',
            'S1200.0000',
            'M3',
            'G55',
            'F60.0000',
            'G0 X0.0000 Y-4.0000',
            'G0 Z0.2000',
            'G98 G81 R1.0200 Z0.5000 F4.8000',
            'X4.0000 Y0.0000',
            'X0.0000 Y4.0000',
            'X-4.0000 Y0.0000',
            'G80',
            'G0 Z0.2000'
        ]

        self.sut.add_hole_circle(4, 8, (0, 0), -90)
        self.assertEqual(expected_gcode, self.sut.drill())


