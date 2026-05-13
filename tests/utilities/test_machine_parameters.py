import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest


class TestReadParameterValues:
    def test_returns_empty_dict_for_missing_file(self):
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values('/nonexistent/file.var')
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_returns_empty_dict_for_none_file(self):
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(None)
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parses_valid_param_file(self):
        content = "1 10.5\n2 20.3\n3 30.7\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5, 2: 20.3, 3: 30.7}
        finally:
            os.unlink(path)

    def test_skips_comment_lines(self):
        content = "; this is a comment\n# another comment\n1 10.5\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5}
        finally:
            os.unlink(path)

    def test_skips_blank_lines(self):
        content = "\n\n1 10.5\n\n2 20.3\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5, 2: 20.3}
        finally:
            os.unlink(path)

    def test_skips_invalid_lines(self):
        content = "1 10.5\ninvalid_line\n2 not_a_number\n3 30.7\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5, 3: 30.7}
        finally:
            os.unlink(path)

    def test_skips_lines_with_single_part(self):
        content = "1 10.5\nsingle_part\n2 20.3\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5, 2: 20.3}
        finally:
            os.unlink(path)

    def test_handles_negative_values(self):
        content = "1 -10.5\n2 -20.3\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: -10.5, 2: -20.3}
        finally:
            os.unlink(path)

    def test_handles_zero_value(self):
        content = "1 0\n2 0.0\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 0.0, 2: 0.0}
        finally:
            os.unlink(path)

    def test_handles_int_param_numbers(self):
        content = "1 10.5\n100 99.9\n1000 -5.0\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5, 100: 99.9, 1000: -5.0}
        finally:
            os.unlink(path)

    def test_handles_whitespace_in_lines(self):
        content = "  1   10.5  \n\t2\t20.3\t\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5, 2: 20.3}
        finally:
            os.unlink(path)

    def test_handles_multiple_values_per_line(self):
        content = "1 10.5 extra\n2 20.3 more\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert result == {1: 10.5, 2: 20.3}
        finally:
            os.unlink(path)

    def test_empty_file_returns_empty_dict(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write("")
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert isinstance(result, dict)
            assert len(result) == 0
        finally:
            os.unlink(path)

    def test_only_comments_returns_empty_dict(self):
        content = "; comment 1\n# comment 2\n; comment 3\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.var', delete=False) as f:
            f.write(content)
            path = f.name

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['read_parameter_values']).read_parameter_values(path)
            assert isinstance(result, dict)
            assert len(result) == 0
        finally:
            os.unlink(path)


class TestGetParameterValue:
    def test_returns_value_for_existing_key(self):
        values = {1: 10.5, 2: 20.3}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, 1)
        assert result == 10.5

    def test_returns_default_for_missing_key(self):
        values = {1: 10.5, 2: 20.3}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, 99)
        assert result == 0.0

    def test_returns_custom_default(self):
        values = {1: 10.5}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, 99, default=-1.0)
        assert result == -1.0

    def test_handles_string_key(self):
        values = {1: 10.5, 2: 20.3}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, "1")
        assert result == 10.5

    def test_returns_default_for_invalid_string_key(self):
        values = {1: 10.5}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, "invalid")
        assert result == 0.0

    def test_returns_default_for_none_key(self):
        values = {1: 10.5}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, None)
        assert result == 0.0

    def test_handles_empty_values_dict(self):
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value({}, 1)
        assert result == 0.0

    def test_handles_large_param_numbers(self):
        values = {9999: 42.0}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, 9999)
        assert result == 42.0

    def test_returns_float_value(self):
        values = {1: 3.14159}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, 1)
        assert isinstance(result, float)

    def test_handles_negative_default(self):
        values = {}
        result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_value']).get_parameter_value(values, 1, default=-99.0)
        assert result == -99.0


class TestGetParameterFilePath:
    def test_returns_none_without_ini_env_var(self):
        old = os.environ.pop('INI_FILE_NAME', None)
        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_file_path']).get_parameter_file_path()
            assert result is None
        finally:
            if old is not None:
                os.environ['INI_FILE_NAME'] = old

    def test_uses_config_dir_from_env(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[RS274NGC]\nPARAMETER_FILE = params.var\n")
            ini_path = f.name
        config_dir = os.path.dirname(ini_path)

        old_ini = os.environ.get('INI_FILE_NAME')
        old_config = os.environ.get('CONFIG_DIR')
        os.environ['INI_FILE_NAME'] = ini_path
        os.environ['CONFIG_DIR'] = config_dir

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_file_path']).get_parameter_file_path()
            assert result is not None
            assert 'params.var' in result
        finally:
            os.unlink(ini_path)
            if old_ini is not None:
                os.environ['INI_FILE_NAME'] = old_ini
            else:
                os.environ.pop('INI_FILE_NAME', None)
            if old_config is not None:
                os.environ['CONFIG_DIR'] = old_config
            else:
                os.environ.pop('CONFIG_DIR', None)

    def test_defaults_to_linuxcnc_var(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[TRAJ]\nCOORDINATES = XYZ\n")
            ini_path = f.name
        config_dir = os.path.dirname(ini_path)

        old_ini = os.environ.get('INI_FILE_NAME')
        old_config = os.environ.get('CONFIG_DIR')
        os.environ['INI_FILE_NAME'] = ini_path
        os.environ['CONFIG_DIR'] = config_dir

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_file_path']).get_parameter_file_path()
            assert result is not None
            assert 'linuxcnc.var' in result
        finally:
            os.unlink(ini_path)
            if old_ini is not None:
                os.environ['INI_FILE_NAME'] = old_ini
            else:
                os.environ.pop('INI_FILE_NAME', None)
            if old_config is not None:
                os.environ['CONFIG_DIR'] = old_config
            else:
                os.environ.pop('CONFIG_DIR', None)

    def test_returns_absolute_path(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[RS274NGC]\nPARAMETER_FILE = params.var\n")
            ini_path = f.name
        config_dir = os.path.dirname(ini_path)

        old_ini = os.environ.get('INI_FILE_NAME')
        old_config = os.environ.get('CONFIG_DIR')
        os.environ['INI_FILE_NAME'] = ini_path
        os.environ['CONFIG_DIR'] = config_dir

        try:
            result = __import__('qtpyvcp.utilities.machine_parameters', fromlist=['get_parameter_file_path']).get_parameter_file_path()
            assert os.path.isabs(result)
        finally:
            os.unlink(ini_path)
            if old_ini is not None:
                os.environ['INI_FILE_NAME'] = old_ini
            else:
                os.environ.pop('INI_FILE_NAME', None)
            if old_config is not None:
                os.environ['CONFIG_DIR'] = old_config
            else:
                os.environ.pop('CONFIG_DIR', None)
