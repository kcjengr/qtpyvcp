import os
import pytest
from qtpyvcp.utilities.misc import normalizePath


class TestNormalizePath:
    def test_none_path_returns_none(self, tmp_path):
        assert normalizePath(None, str(tmp_path)) is None

    def test_none_base_returns_none(self):
        assert normalizePath("/some/path", None) is None

    def test_absolute_path_resolved(self, tmp_path):
        abs_path = str(tmp_path / "subdir" / "file.txt")
        os.makedirs(os.path.dirname(abs_path))
        with open(abs_path, 'w') as f:
            f.write('test')
        result = normalizePath(abs_path, '/any/base')
        assert result == os.path.realpath(abs_path)

    def test_relative_path_joined_to_base(self, tmp_path):
        rel_path = "subdir/file.txt"
        target = tmp_path / rel_path
        target.parent.mkdir()
        with open(target, 'w') as f:
            f.write('test')
        result = normalizePath(rel_path, str(tmp_path))
        assert result == os.path.realpath(str(target))

    def test_tilde_expanded(self):
        result = normalizePath("~/some/path", "/base")
        assert '~' not in result

    def test_env_var_expanded(self, monkeypatch):
        monkeypatch.setenv('TEST_NORM_PATH', '/expanded/path')
        result = normalizePath('$TEST_NORM_PATH', '/base')
        assert result == '/expanded/path'
