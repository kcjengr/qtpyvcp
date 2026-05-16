import os
import tempfile
import pytest


class TestNormalizePath:
    """Tests for normalizePath utility function."""

    def test_none_path_returns_none(self):
        from qtpyvcp.utilities.misc import normalizePath
        result = normalizePath(None, '/base')
        assert result is None

    def test_none_base_returns_none(self):
        from qtpyvcp.utilities.misc import normalizePath
        result = normalizePath('/some/path', None)
        assert result is None

    def test_expands_env_vars(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['TEST_PATH'] = tmpdir
            result = normalizePath('$TEST_PATH/file.txt', '/base')
            assert result == os.path.realpath(os.path.join(tmpdir, 'file.txt'))
            del os.environ['TEST_PATH']

    def test_expands_user_home(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        result = normalizePath('~/some/path', '/base')
        expected = os.path.expanduser('~/some/path')
        assert result == os.path.realpath(expected)

    def test_relative_path_joins_with_base(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        result = normalizePath('file.txt', '/base/dir')
        assert result == os.path.realpath('/base/dir/file.txt')

    def test_absolute_path_stays_absolute(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        with tempfile.TemporaryDirectory() as tmpdir:
            abs_path = os.path.join(tmpdir, 'file.txt')
            result = normalizePath(abs_path, '/base/dir')
            assert result == os.path.realpath(abs_path)

    def test_returns_realpath(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            
            result = normalizePath('test.txt', tmpdir)
            assert result == os.path.realpath(test_file)

    def test_nonexistent_path_returns_realpath(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = normalizePath('nonexistent.txt', tmpdir)
            expected = os.path.join(tmpdir, 'nonexistent.txt')
            assert result == os.path.realpath(expected)

    def test_tilde_expansion_with_base(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        result = normalizePath('~/test/path', '/base')
        # tilde takes precedence over base
        expected = os.path.expanduser('~/test/path')
        assert result == os.path.realpath(expected)

    def test_env_var_with_tilde(self):
        from qtpyvcp.utilities.misc import normalizePath
        
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['MY_DIR'] = tmpdir
            result = normalizePath('$MY_DIR/file.txt', '/base')
            assert result == os.path.realpath(os.path.join(tmpdir, 'file.txt'))
            del os.environ['MY_DIR']


class TestInsertPath:
    """Tests for insertPath utility function."""

    def test_insert_path_new_var(self):
        from qtpyvcp.utilities.misc import insertPath
        
        var_name = 'TEST_INSERT_PATH'
        if var_name in os.environ:
            del os.environ[var_name]
        
        insertPath(var_name, 0, '/new/path')
        assert os.environ[var_name] == '/new/path'
        del os.environ[var_name]

    def test_insert_path_into_existing_var(self):
        from qtpyvcp.utilities.misc import insertPath
        
        var_name = 'TEST_INSERT_EXISTING'
        os.environ[var_name] = '/existing/path1:/existing/path2'
        
        insertPath(var_name, 0, '/new/path')
        assert os.environ[var_name] == '/new/path:/existing/path1:/existing/path2'
        del os.environ[var_name]

    def test_insert_path_at_end(self):
        from qtpyvcp.utilities.misc import insertPath
        
        var_name = 'TEST_INSERT_END'
        os.environ[var_name] = '/path1:/path2'
        
        insertPath(var_name, 2, '/new/path')
        assert os.environ[var_name] == '/path1:/path2:/new/path'
        del os.environ[var_name]

    def test_insert_path_middle(self):
        from qtpyvcp.utilities.misc import insertPath
        
        var_name = 'TEST_INSERT_MIDDLE'
        os.environ[var_name] = '/path1:/path2:/path3'
        
        insertPath(var_name, 1, '/new/path')
        assert os.environ[var_name] == '/path1:/new/path:/path2:/path3'
        del os.environ[var_name]

    def test_insert_path_strips_trailing_colon(self):
        from qtpyvcp.utilities.misc import insertPath
        
        var_name = 'TEST_INSERT_STRIP'
        os.environ[var_name] = '/path1:/path2:'
        
        insertPath(var_name, 0, '/new/path')
        assert os.environ[var_name] == '/new/path:/path1:/path2'
        del os.environ[var_name]

    def test_insert_path_empty_var(self):
        from qtpyvcp.utilities.misc import insertPath
        
        var_name = 'TEST_INSERT_EMPTY'
        os.environ[var_name] = ''
        
        insertPath(var_name, 0, '/new/path')
        # Empty string splits to [''], so result has trailing colon
        assert os.environ[var_name] == '/new/path:'
        del os.environ[var_name]
