import unittest

from qtpyvcp.widgets.conversational.ops.gcode_file import GCodeFile


class FakeOp:
    def __init__(self):
        self.test_gcode = ''
        self.test_name = ''
        self.test_start_op = []
        self.test_end_op = []

    def name(self):
        return self.test_name

    def gcode(self):
        return self.test_gcode


class TestGCodeFile(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.sut = GCodeFile()

    def test_should_output_line_numbers_and_increment_by_stride_for_each_line(self):
        expected_output = [
            'N10 G90 G94 G17 G91.1',
            'N20 G53 G0 Z0',
            'N30 M30',
            'N40 %',
        ]

        self.assertEqual(expected_output, self.sut.gcode())

    def test_should_add_a_single_op(self):
        expected_output = [
            'N10 G90 G94 G17 G91.1',
            'N20 some conversational',
            'N30 gcode ops',
            'N40 G53 G0 Z0',
            'N50 M30',
            'N60 %',
        ]

        self.sut.ops.append(['some conversational', 'gcode ops'])
        self.assertEqual(expected_output, self.sut.gcode())

    def test_should_add_multiple_ops(self):
        expected_output = [
            'N10 G90 G94 G17 G91.1',
            'N20 some conversational',
            'N30 some more conversational',
            'N40 and some more conversational',
            'N50 G53 G0 Z0',
            'N60 M30',
            'N70 %',
        ]

        self.sut.ops.append(['some conversational'])
        self.sut.ops.append(['some more conversational'])
        self.sut.ops.append(['and some more conversational'])

        self.assertEqual(expected_output, self.sut.gcode())
