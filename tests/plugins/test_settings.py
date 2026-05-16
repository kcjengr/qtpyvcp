"""Tests for qtpyvcp.plugins.settings.Settings plugin."""

import pytest
from pathlib import Path
import sys
import importlib.util
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).parent.parent.parent
_SRC_DIR = _REPO_ROOT / "src"


def _load_settings_module():
    """Load the settings module directly from file to avoid caching issues."""
    spec = importlib.util.spec_from_file_location(
        "qtpyvcp.plugins.settings",
        str(_SRC_DIR / "qtpyvcp" / "plugins" / "settings.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["qtpyvcp.plugins.settings"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _reset_qtpyvcp_globals():
    """Reset SETTINGS and CONFIG between tests to avoid cross-test pollution."""
    from qtpyvcp import SETTINGS, CONFIG

    original_settings = SETTINGS.copy()
    original_config = CONFIG.copy()

    SETTINGS.clear()
    CONFIG.clear()
    CONFIG['settings'] = {}

    yield

    SETTINGS.clear()
    SETTINGS.update(original_settings)
    CONFIG.clear()
    CONFIG.update(original_config)


class TestSettingsInit:
    def test_init_sets_channels_to_settings_dict(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 'test'
        SETTINGS['mykey'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        assert s.channels is SETTINGS

    def test_init_creates_data_manager_reference(self):
        from qtpyvcp import SETTINGS
        SETTINGS.clear()

        mock_dm = MagicMock()
        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()

        assert s.data_manager is mock_dm


class TestSettingsGetChannel:
    def test_getChannel_returns_channel_for_known_key(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 'test_value'
        SETTINGS['mykey'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('mykey')
        assert chan_obj is not None
        assert chan_exp is not None
        assert callable(chan_exp)

    def test_getChannel_returns_value(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 'hello'
        SETTINGS['greet'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('greet')
        assert chan_exp() == 'hello'

    def test_getChannel_returns_none_for_unknown_key(self):
        from qtpyvcp import SETTINGS
        SETTINGS.clear()

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('nonexistent')
        assert chan_obj is None
        assert chan_exp is None


class TestSettingsInitialise:
    def test_initialise_loads_persistent_settings(self):
        from qtpyvcp import SETTINGS

        mock_obj_a = MagicMock()
        mock_obj_a.getValue.return_value = 'default_a'
        mock_obj_a.setValue = MagicMock()
        SETTINGS['setting_a'] = mock_obj_a

        mock_obj_b = MagicMock()
        mock_obj_b.getValue.return_value = 0
        mock_obj_b.setValue = MagicMock()
        SETTINGS['setting_b'] = mock_obj_b

        mock_dm = MagicMock()
        mock_dm.getData.return_value = {'setting_a': 'restored_a', 'setting_b': 42}

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()
            s.initialise()

        mock_obj_a.setValue.assert_called_once_with('restored_a')
        mock_obj_b.setValue.assert_called_once_with(42)

    def test_initialise_skips_unknown_settings(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 'default'
        mock_obj.setValue = MagicMock()
        SETTINGS['real_setting'] = mock_obj

        mock_dm = MagicMock()
        mock_dm.getData.return_value = {'unknown_setting': 'value'}

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()
            # Should not raise for unknown settings
            s.initialise()

    def test_initialise_with_empty_stored_settings(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 'default'
        mock_obj.setValue = MagicMock()
        SETTINGS['mykey'] = mock_obj

        mock_dm = MagicMock()
        mock_dm.getData.return_value = {}

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()
            s.initialise()

        mock_obj.setValue.assert_not_called()


class TestSettingsTerminate:
    def test_terminate_saves_persistent_settings(self):
        from qtpyvcp import SETTINGS

        mock_setting_a = MagicMock()
        mock_setting_a.getValue.return_value = 'changed_value'
        mock_setting_a.persistent = True
        mock_setting_a.default_value = 'default'
        SETTINGS['setting_a'] = mock_setting_a

        mock_setting_b = MagicMock()
        mock_setting_b.getValue.return_value = 'default'
        mock_setting_b.persistent = True
        mock_setting_b.default_value = 'default'
        SETTINGS['setting_b'] = mock_setting_b

        mock_dm = MagicMock()
        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()
            s.terminate()

        call_args = mock_dm.setData.call_args
        assert call_args[0][0] == 'settings'
        saved = call_args[0][1]
        assert 'setting_a' in saved
        assert saved['setting_a'] == 'changed_value'
        assert 'setting_b' not in saved

    def test_terminate_skips_non_persistent_settings(self):
        from qtpyvcp import SETTINGS

        mock_setting = MagicMock()
        mock_setting.getValue.return_value = 'changed'
        mock_setting.persistent = False
        mock_setting.default_value = 'default'
        SETTINGS['non_persistent'] = mock_setting

        mock_dm = MagicMock()
        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()
            s.terminate()

        # setData is called but with empty dict (no persistent changed settings)
        mock_dm.setData.assert_called_once_with('settings', {})

    def test_terminate_skips_settings_at_default(self):
        from qtpyvcp import SETTINGS

        mock_setting = MagicMock()
        mock_setting.getValue.return_value = 'default'
        mock_setting.persistent = True
        mock_setting.default_value = 'default'
        SETTINGS['at_default'] = mock_setting

        mock_dm = MagicMock()
        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()
            s.terminate()

        # setData is called but with empty dict (setting at default value)
        mock_dm.setData.assert_called_once_with('settings', {})

    def test_terminate_saves_all_changed_settings(self):
        from qtpyvcp import SETTINGS

        setting_a = MagicMock()
        setting_a.getValue.return_value = 'val_a'
        setting_a.persistent = True
        setting_a.default_value = 'default_a'
        SETTINGS['a'] = setting_a

        setting_b = MagicMock()
        setting_b.getValue.return_value = 99
        setting_b.persistent = True
        setting_b.default_value = 0
        SETTINGS['b'] = setting_b

        mock_dm = MagicMock()
        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=mock_dm):
            s = settings_mod.Settings()
            s.terminate()

        call_args = mock_dm.setData.call_args
        saved = call_args[0][1]
        assert 'a' in saved
        assert 'b' in saved
        assert saved['a'] == 'val_a'
        assert saved['b'] == 99


class TestSettingsGetChannelWithDifferentTypes:
    def test_getChannel_for_string_value(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 'hello world'
        SETTINGS['text'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('text')
        assert chan_exp() == 'hello world'

    def test_getChannel_for_int_value(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 42
        SETTINGS['count'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('count')
        assert chan_exp() == 42

    def test_getChannel_for_float_value(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = 3.14
        SETTINGS['ratio'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('ratio')
        assert chan_exp() == 3.14

    def test_getChannel_for_bool_value(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = True
        SETTINGS['flag'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('flag')
        assert chan_exp() is True

    def test_getChannel_for_list_value(self):
        from qtpyvcp import SETTINGS

        mock_obj = MagicMock()
        mock_obj.getValue.return_value = [1, 2, 3]
        SETTINGS['items'] = mock_obj

        settings_mod = _load_settings_module()
        with patch.object(settings_mod, 'getPlugin', return_value=MagicMock()):
            s = settings_mod.Settings()

        chan_obj, chan_exp = s.getChannel('items')
        assert chan_exp() == [1, 2, 3]
