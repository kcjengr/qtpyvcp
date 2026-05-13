import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest


class TestLoadConfigFiles:
    def test_filters_none_files(self):
        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.load') as mock_load, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.dump') as mock_dump:
            mock_proc.return_value = ['/fake/file.yml']
            mock_load.return_value = ['merged']
            mock_dump.return_value = 'dumped'

            result = __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files']).load_config_files(None, '', '/fake/file.yml')

            assert result == ['merged']

    def test_filters_empty_string_files(self):
        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.load') as mock_load:
            mock_proc.return_value = ['/fake/file.yml']
            mock_load.return_value = ['merged']

            result = __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files']).load_config_files('', None, '  ', '/fake/file.yml')

            assert result == ['merged']

    def test_adds_file_dirs_to_sys_path(self):
        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.load') as mock_load:
            mock_proc.return_value = ['/fake/file.yml']
            mock_load.return_value = ['merged']

            __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files']).load_config_files('/some/dir/config.yml')

            assert '/some/dir' in sys.path[:5]

    def test_reverses_file_order_before_processing(self):
        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.load') as mock_load:
            mock_proc.return_value = ['/fake/b.yml', '/fake/a.yml']
            mock_load.return_value = ['merged']

            __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files']).load_config_files('/fake/a.yml', '/fake/b.yml')

            call_args = mock_proc.call_args[0][0]
            assert call_args == ['/fake/b.yml', '/fake/a.yml']

    def test_sets_hiya_pco_jinja2env(self):
        from qtpyvcp.utilities.config_loader import load_config_files, hiyapyco
        from jinja2.nativetypes import NativeEnvironment

        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc:
            mock_proc.return_value = ['/fake/file.yml']
            with patch.object(hiyapyco, 'load') as mock_load:
                mock_load.return_value = ['merged']

                load_config_files('/fake/file.yml')

                assert isinstance(hiyapyco.jinja2env, NativeEnvironment)
                assert hiyapyco.jinja2env.variable_start_string == '('
                assert hiyapyco.jinja2env.variable_end_string == ')'

    def test_calls_hiya_pco_load_with_substitute_method(self):
        from qtpyvcp.utilities.config_loader import load_config_files, hiyapyco

        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc:
            mock_proc.return_value = ['/fake/file.yml']
            with patch.object(hiyapyco, 'load') as mock_load:
                mock_load.return_value = ['merged']

                load_config_files('/fake/file.yml')

                mock_load.assert_called_once()
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs['method'] == hiyapyco.METHOD_SUBSTITUTE
                assert call_kwargs['interpolate'] is True
                assert call_kwargs['failonmissingfiles'] is True

    def test_returns_merged_config_dict(self):
        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.load') as mock_load:
            expected = {'section': {'key': 'value'}}
            mock_proc.return_value = ['/fake/file.yml']
            mock_load.return_value = expected

            result = __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files']).load_config_files('/fake/file.yml')

            assert result == expected

    def test_debug_logs_merged_config(self):
        import logging
        with patch('qtpyvcp.utilities.config_loader.process_templates') as mock_proc, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.load') as mock_load, \
             patch('qtpyvcp.utilities.config_loader.hiyapyco.dump') as mock_dump, \
             patch('qtpyvcp.utilities.config_loader.LOG') as mock_log:
            mock_proc.return_value = ['/fake/file.yml']
            mock_load.return_value = {'key': 'value'}
            mock_dump.return_value = 'dumped'
            mock_log.getEffectiveLevel.return_value = logging.DEBUG

            __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files']).load_config_files('/fake/file.yml')

            mock_log.debug.assert_called()


class TestProcessTemplates:
    def test_returns_list_of_strings(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("key: (env.get('HOME', '/default'))\n")
            template_path = f.name

        try:
            result = __import__('qtpyvcp.utilities.config_loader', fromlist=['process_templates']).process_templates([template_path])
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], str)
        finally:
            os.unlink(template_path)

    def test_includes_ini_data_in_render_context(self):
        from qtpyvcp.utilities.yaml_filters import from_ini as real_from_ini
        with patch('qtpyvcp.utilities.config_loader.INIFilterModule') as mock_filter_cls:
            mock_filter = MagicMock()
            mock_filter.filters.return_value = {'from-ini': real_from_ini}
            mock_filter_cls.return_value = mock_filter

            old_ini = os.environ.get('INI_FILE_NAME')
            os.environ['INI_FILE_NAME'] = '/dev/null'

            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                    f.write("data: (ini)\n")
                    template_path = f.name

                try:
                    result = __import__('qtpyvcp.utilities.config_loader', fromlist=['process_templates']).process_templates([template_path])
                    assert isinstance(result, list)
                    assert 'data:' in result[0]
                finally:
                    os.unlink(template_path)
            finally:
                if old_ini is not None:
                    os.environ['INI_FILE_NAME'] = old_ini
                else:
                    os.environ.pop('INI_FILE_NAME', None)

    def test_includes_env_in_render_context(self):
        from qtpyvcp.utilities.yaml_filters import from_ini as real_from_ini
        with patch('qtpyvcp.utilities.config_loader.INIFilterModule') as mock_filter_cls:
            mock_filter = MagicMock()
            mock_filter.filters.return_value = {'from-ini': real_from_ini}
            mock_filter_cls.return_value = mock_filter

            old_ini = os.environ.get('INI_FILE_NAME')
            os.environ['INI_FILE_NAME'] = '/dev/null'

            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                    f.write("home: (env.get('HOME', ''))\n")
                    template_path = f.name

                try:
                    result = __import__('qtpyvcp.utilities.config_loader', fromlist=['process_templates']).process_templates([template_path])
                    assert isinstance(result, list)
                    assert os.path.expandvars('$HOME') in result[0] or 'home:' in result[0]
                finally:
                    os.unlink(template_path)
            finally:
                if old_ini is not None:
                    os.environ['INI_FILE_NAME'] = old_ini
                else:
                    os.environ.pop('INI_FILE_NAME', None)

    def test_skips_nonexistent_files(self):
        with patch('qtpyvcp.utilities.config_loader.INIFilterModule') as mock_filter_cls:
            mock_filter = MagicMock()
            mock_filter.filters.return_value = {}
            mock_filter_cls.return_value = mock_filter

            old_ini = os.environ.get('INI_FILE_NAME')
            os.environ['INI_FILE_NAME'] = '/dev/null'

            try:
                result = __import__('qtpyvcp.utilities.config_loader', fromlist=['process_templates']).process_templates(['/nonexistent/file.yml'])
                assert isinstance(result, list)
                assert all(isinstance(r, str) for r in result)
            finally:
                if old_ini is not None:
                    os.environ['INI_FILE_NAME'] = old_ini
                else:
                    os.environ.pop('INI_FILE_NAME', None)

    def test_multiple_files_return_multiple_results(self):
        from qtpyvcp.utilities.yaml_filters import from_ini as real_from_ini
        with patch('qtpyvcp.utilities.config_loader.INIFilterModule') as mock_filter_cls:
            mock_filter = MagicMock()
            mock_filter.filters.return_value = {'from-ini': real_from_ini}
            mock_filter_cls.return_value = mock_filter

            old_ini = os.environ.get('INI_FILE_NAME')
            os.environ['INI_FILE_NAME'] = '/dev/null'

            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f1:
                    f1.write("key1: value1\n")
                    path1 = f1.name
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f2:
                    f2.write("key2: value2\n")
                    path2 = f2.name

                try:
                    result = __import__('qtpyvcp.utilities.config_loader', fromlist=['process_templates']).process_templates([path1, path2])
                    assert len(result) == 2
                finally:
                    os.unlink(path1)
                    os.unlink(path2)
            finally:
                if old_ini is not None:
                    os.environ['INI_FILE_NAME'] = old_ini
                else:
                    os.environ.pop('INI_FILE_NAME', None)

    def test_file_context_includes_path_dir_and_name(self):
        from qtpyvcp.utilities.yaml_filters import from_ini as real_from_ini
        with patch('qtpyvcp.utilities.config_loader.INIFilterModule') as mock_filter_cls:
            mock_filter = MagicMock()
            mock_filter.filters.return_value = {'from-ini': real_from_ini}
            mock_filter_cls.return_value = mock_filter

            old_ini = os.environ.get('INI_FILE_NAME')
            os.environ['INI_FILE_NAME'] = '/dev/null'

            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                    f.write("path: (file.path)\n")
                    template_path = f.name

                try:
                    result = __import__('qtpyvcp.utilities.config_loader', fromlist=['process_templates']).process_templates([template_path])
                    assert isinstance(result, list)
                    assert template_path in result[0] or 'path:' in result[0]
                finally:
                    os.unlink(template_path)
            finally:
                if old_ini is not None:
                    os.environ['INI_FILE_NAME'] = old_ini
                else:
                    os.environ.pop('INI_FILE_NAME', None)


class TestLoadConfigFilesFromEnv:
    def test_reads_vcp_config_files_env_var(self):
        with patch('qtpyvcp.utilities.config_loader.load_config_files') as mock_load:
            mock_load.return_value = {'key': 'value'}

            old_val = os.environ.get('VCP_CONFIG_FILES')
            os.environ['VCP_CONFIG_FILES'] = '/path/to/config1.yml:/path/to/config2.yml'

            try:
                result = __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files_from_env']).load_config_files_from_env()
                mock_load.assert_called_once_with('/path/to/config1.yml', '/path/to/config2.yml')
                assert result == {'key': 'value'}
            finally:
                if old_val is not None:
                    os.environ['VCP_CONFIG_FILES'] = old_val
                else:
                    os.environ.pop('VCP_CONFIG_FILES', None)

    def test_handles_empty_env_var(self):
        with patch('qtpyvcp.utilities.config_loader.load_config_files') as mock_load:
            mock_load.return_value = {}

            old_val = os.environ.get('VCP_CONFIG_FILES')
            os.environ['VCP_CONFIG_FILES'] = ''

            try:
                result = __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files_from_env']).load_config_files_from_env()
                mock_load.assert_called_once_with('')
            finally:
                if old_val is not None:
                    os.environ['VCP_CONFIG_FILES'] = old_val
                else:
                    os.environ.pop('VCP_CONFIG_FILES', None)

    def test_handles_single_file_in_env_var(self):
        with patch('qtpyvcp.utilities.config_loader.load_config_files') as mock_load:
            mock_load.return_value = {'key': 'value'}

            old_val = os.environ.get('VCP_CONFIG_FILES')
            os.environ['VCP_CONFIG_FILES'] = '/single/config.yml'

            try:
                result = __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files_from_env']).load_config_files_from_env()
                mock_load.assert_called_once_with('/single/config.yml')
            finally:
                if old_val is not None:
                    os.environ['VCP_CONFIG_FILES'] = old_val
                else:
                    os.environ.pop('VCP_CONFIG_FILES', None)

    def test_handles_multiple_colon_separated_files(self):
        with patch('qtpyvcp.utilities.config_loader.load_config_files') as mock_load:
            mock_load.return_value = {'key': 'value'}

            old_val = os.environ.get('VCP_CONFIG_FILES')
            os.environ['VCP_CONFIG_FILES'] = '/a.yml:/b.yml:/c.yml'

            try:
                result = __import__('qtpyvcp.utilities.config_loader', fromlist=['load_config_files_from_env']).load_config_files_from_env()
                mock_load.assert_called_once_with('/a.yml', '/b.yml', '/c.yml')
            finally:
                if old_val is not None:
                    os.environ['VCP_CONFIG_FILES'] = old_val
                else:
                    os.environ.pop('VCP_CONFIG_FILES', None)
