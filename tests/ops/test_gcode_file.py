import os
import pytest
from qtpyvcp.ops.gcode_file import GCodeFile


class TestGCodeFileInit:
    def test_default_preamble(self):
        f = GCodeFile()
        assert f.preamble == ['G90 G94 G17 G91.1']

    def test_default_epilog(self):
        f = GCodeFile()
        assert f.epilog == ['G53 G0 Z0', 'M30', '%']

    def test_starting_line_number(self):
        f = GCodeFile()
        assert f.starting_line_number == 10

    def test_line_number_stride(self):
        f = GCodeFile()
        assert f.line_number_stride == 10

    def test_initial_ops_is_empty_list(self):
        f = GCodeFile()
        assert f.ops == []


class TestGCodeFileGcode:
    def setup_method(self):
        self.f = GCodeFile()

    def test_empty_ops_produces_preamble_and_epilog_only(self):
        result = self.f.gcode()
        assert len(result) == 4  # 1 preamble + 3 epilog lines
        assert 'N10 G90 G94 G17 G91.1' in result
        assert 'N40 %' in result

    def test_line_numbers_start_at_10(self):
        result = self.f.gcode()
        assert result[0].startswith('N10')

    def test_line_numbers_stride_by_10(self):
        result = self.f.gcode()
        assert result[1].startswith('N20')
        assert result[2].startswith('N30')
        assert result[3].startswith('N40')

    def test_ops_are_inserted_between_preamble_and_epilog(self):
        self.f.ops.append(['X10.0 Y5.0'])
        result = self.f.gcode()
        preamble_idx = next(i for i, line in enumerate(result) if 'G90 G94' in line)
        epilog_idx = next(i for i, line in enumerate(result) if 'M30' in line)
        op_idx = next(i for i, line in enumerate(result) if 'X10.0 Y5.0' in line)
        assert preamble_idx < op_idx < epilog_idx

    def test_each_line_has_n_prefix(self):
        self.f.ops.append(['X10.0 Y5.0'])
        result = self.f.gcode()
        for line in result:
            assert line.startswith('N')

    def test_line_numbers_are_sequential_by_stride(self):
        self.f.line_number_stride = 5
        self.f.starting_line_number = 2
        result = self.f.gcode()
        expected_numbers = [2, 7, 12, 17, 22]
        for i, line in enumerate(result):
            assert line.startswith('N{}'.format(expected_numbers[i]))


class TestGCodeFileToString:
    def setup_method(self):
        self.f = GCodeFile()

    def test_returns_joined_string(self):
        result = self.f.to_string()
        assert isinstance(result, str)
        assert '\n' in result

    def test_matches_gcode_output(self):
        result = self.f.to_string()
        expected = '\n'.join(self.f.gcode())
        assert result == expected


class TestGCodeFileWriteToFile:
    def test_creates_file(self, tmp_path):
        f = GCodeFile()
        target = tmp_path / 'test.ngc'
        f.write_to_file(str(target))
        assert target.exists()

    def test_writes_correct_content(self, tmp_path):
        f = GCodeFile()
        target = tmp_path / 'test.ngc'
        f.write_to_file(str(target))
        content = target.read_text()
        expected = '\n'.join(f.gcode())
        assert content == expected

    def test_overwrites_existing_file(self, tmp_path):
        f = GCodeFile()
        target = tmp_path / 'test.ngc'
        # Write initial content
        with open(str(target), 'w') as fh:
            fh.write('old content\n')
        f.write_to_file(str(target))
        content = target.read_text()
        assert 'old content' not in content
