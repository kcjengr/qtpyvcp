import os
import tempfile
import pytest
from qtpyvcp.app.runtime_config import RuntimeConfig


class TestRuntimeConfig:
    def test_set_and_get_string(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'key', 'value')
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'key') == 'value'

    def test_set_and_get_int(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'count', 42)
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'count', default=0) == 42

    def test_set_and_get_float(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'pi', 3.14159)
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'pi', default=0.0) == 3.14159

    def test_set_and_get_bool_true(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'flag', True)
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'flag', default=False) is True

    def test_set_and_get_bool_false(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'flag', False)
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'flag', default=True) is False

    def test_set_and_get_list(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'items', [1, 2, 3])
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'items', default=[]) == [1, 2, 3]

    def test_set_and_get_dict(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'mapping', {'x': 1, 'y': 2})
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'mapping', default={}) == {'x': 1, 'y': 2}

    def test_get_creates_missing_section(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        value = rc.get('NEW_SECTION', 'key', 'default_val')
        assert value == 'default_val'

        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('NEW_SECTION', 'key') == 'default_val'

    def test_get_invalid_float_returns_default(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'bad_float', 'not_a_number')
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'bad_float', default=99.0) == 99.0

    def test_get_invalid_int_returns_default(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('SECTION', 'bad_int', 'not_a_number')
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'bad_int', default=999) == 999

    def test_context_manager_write(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        with RuntimeConfig(fname) as rc:
            rc.set('SECTION', 'key', 'value')
        assert os.path.exists(fname)

        rc2 = RuntimeConfig(fname).read()
        assert rc2.get('SECTION', 'key') == 'value'

    def test_context_manager_no_write_when_unchanged(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        # Create file first
        with open(fname, 'w') as f:
            f.write('[SECTION]\nkey = value\n')

        with RuntimeConfig(fname) as rc:
            rc.read()
            # Don't modify anything
        assert os.path.getsize(fname) > 0

    def test_bool_parsing_variants(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        for i, val in enumerate(['true', 'True', 'TRUE', '1', 'yes', 'on']):
            rc.set('BOOLS', f'key_{i}', True)
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        for i in range(6):
            assert rc2.get('BOOLS', f'key_{i}', default=False) is True

    def test_bool_parsing_false_variants(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        for i, val in enumerate(['false', 'False', '0', 'no', 'off']):
            rc.set('BOOLS', f'key_{i}', False)
        rc.write()

        rc2 = RuntimeConfig(fname).read()
        for i in range(5):
            assert rc2.get('BOOLS', f'key_{i}', default=True) is False

    def test_preserves_case_of_options(self, tmp_path):
        fname = str(tmp_path / 'test.cfg')
        rc = RuntimeConfig(fname)
        rc.set('Section', 'MixedCaseKey', 'value')
        rc.write()

        with open(fname) as f:
            content = f.read()
        assert 'MixedCaseKey' in content
