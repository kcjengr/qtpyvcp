"""Tests for qtpyvcp.plugins.virtual_input_manager.VirtualInputManager plugin."""

import pytest
from unittest.mock import MagicMock, patch


class TestVirtualInputManagerInit:
    def test_init_creates_input_providers_dict(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager
        vim = VirtualInputManager()
        assert vim.input_providers == {}

    def test_init_sets_active_vkb_to_none(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager
        vim = VirtualInputManager()
        assert vim.active_vkb is None


class TestVirtualInputManagerActivate:
    def test_activate_with_none_widget_returns_early(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager
        vim = VirtualInputManager()
        # Should not raise
        vim.activateVirtualInput(None)

    def test_activate_spinbox_sets_number_int_type(self):
        from qtpy.QtWidgets import QSpinBox
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_vkb = MagicMock()
        vim = VirtualInputManager()
        vim.input_providers['number:int'] = mock_vkb

        spinbox = MagicMock(spec=QSpinBox)
        vim.activateVirtualInput(spinbox)

        mock_vkb.activate.assert_called_once_with(spinbox)
        assert vim.active_vkb is mock_vkb

    def test_activate_doublespinbox_sets_number_float_type(self):
        from qtpy.QtWidgets import QDoubleSpinBox
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_vkb = MagicMock()
        vim = VirtualInputManager()
        vim.input_providers['number:float'] = mock_vkb

        spinbox = MagicMock(spec=QDoubleSpinBox)
        vim.activateVirtualInput(spinbox)

        mock_vkb.activate.assert_called_once_with(spinbox)
        assert vim.active_vkb is mock_vkb

    def test_activate_readonly_widget_returns_early(self):
        from qtpy.QtWidgets import QLineEdit
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        vim = VirtualInputManager()
        lineedit = MagicMock(spec=QLineEdit)
        lineedit.isReadOnly.return_value = True
        # Should not raise, should not activate anything
        vim.activateVirtualInput(lineedit)

    def test_activate_with_explicit_input_type_uses_it(self):
        from qtpy.QtWidgets import QLineEdit
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_vkb = MagicMock()
        vim = VirtualInputManager()
        vim.input_providers['custom:type'] = mock_vkb

        lineedit = MagicMock(spec=QLineEdit)
        vim.activateVirtualInput(lineedit, input_type='custom:type')

        mock_vkb.activate.assert_called_once_with(lineedit)
        assert vim.active_vkb is mock_vkb


class TestVirtualInputManagerDeactivate:
    def test_deactivate_with_no_active_vkb_does_nothing(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager
        vim = VirtualInputManager()
        # Should not raise
        vim.deactivateVirtualInput()

    def test_deactivate_hides_active_vkb(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_vkb = MagicMock()
        vim = VirtualInputManager()
        vim.active_vkb = mock_vkb

        vim.deactivateVirtualInput()

        mock_vkb.hide.assert_called_once()

    def test_deactivate_sets_active_vkb_to_none(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_vkb = MagicMock()
        vim = VirtualInputManager()
        vim.active_vkb = mock_vkb

        vim.deactivateVirtualInput()

        assert vim.active_vkb is None


class TestVirtualInputManagerOnFocusChanged:
    def test_on_focus_changed_with_no_new_widget_deactivates(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_vkb = MagicMock()
        vim = VirtualInputManager()
        vim.active_vkb = mock_vkb

        vim.onFocusChanged(None, None)

        mock_vkb.hide.assert_called_once()
        assert vim.active_vkb is None

    def test_on_focus_changed_with_disabled_plugin_does_nothing(self):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        vim = VirtualInputManager()
        vim._enabled_value = False

        new_widget = MagicMock(spec=QWidget)
        vim.onFocusChanged(None, new_widget)

        # Should not activate anything
        assert vim.active_vkb is None


class TestVirtualInputManagerEnabled:
    def test_enabled_returns_false_by_default(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager
        vim = VirtualInputManager()
        assert vim.enabled() is False

    def test_enabled_can_be_set_to_true(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager
        vim = VirtualInputManager()
        vim.enabled.value = True
        assert vim.enabled() is True


class TestVirtualInputManagerInitialise:
    @pytest.fixture(autouse=True)
    def _mock_qapp(self):
        """Ensure a mock QApplication instance exists for initialise tests."""
        from qtpy.QtWidgets import QApplication
        import qtpyvcp.plugins.virtual_input_manager as vim_mod
        mock_app = MagicMock()
        vim_mod.QApplication.instance = lambda: mock_app
        yield mock_app
        vim_mod.QApplication.instance = QApplication.instance  # restore

    def test_initialise_populates_input_providers_from_config(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_provider = MagicMock()
        config_dict = {
            'virtual_input_providers': {
                'text:gcode': {'class': 'MockVKB'},
                'number:float': {'class': 'MockVKB2'},
            }
        }

        with patch('qtpyvcp.plugins.virtual_input_manager.CONFIG', config_dict):
            with patch('qtpyvcp.plugins.virtual_input_manager._initialize_object_from_dict', return_value=mock_provider):
                vim = VirtualInputManager()
                vim.initialise()

                assert 'text:gcode' in vim.input_providers
                assert 'number:float' in vim.input_providers

    def test_initialise_converts_dots_to_colons_in_keys(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_provider = MagicMock()
        config_dict = {
            'virtual_input_providers': {
                'text.gcode': {'class': 'MockVKB'},
            }
        }

        with patch('qtpyvcp.plugins.virtual_input_manager.CONFIG', config_dict):
            with patch('qtpyvcp.plugins.virtual_input_manager._initialize_object_from_dict', return_value=mock_provider):
                vim = VirtualInputManager()
                vim.initialise()

                assert 'text:gcode' in vim.input_providers
                assert 'text.gcode' not in vim.input_providers

    def test_initialise_hides_all_providers(self):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        mock_provider1 = MagicMock()
        mock_provider2 = MagicMock()
        config_dict = {
            'virtual_input_providers': {
                'text:gcode': {'class': 'MockVKB'},
                'number:float': {'class': 'MockVKB2'},
            }
        }

        def side_effect(d):
            if 'MockVKB2' in str(d):
                return mock_provider2
            return mock_provider1

        with patch('qtpyvcp.plugins.virtual_input_manager.CONFIG', config_dict):
            with patch('qtpyvcp.plugins.virtual_input_manager._initialize_object_from_dict', side_effect=side_effect):
                vim = VirtualInputManager()
                vim.initialise()

                mock_provider1.hide.assert_called_once()
                mock_provider2.hide.assert_called_once()

    def test_initialise_connects_focus_changed_signal(self, _mock_qapp):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        config_dict = {
            'virtual_input_providers': {}
        }

        with patch('qtpyvcp.plugins.virtual_input_manager.CONFIG', config_dict):
            _mock_qapp.focusChanged.connect.reset_mock()
            vim = VirtualInputManager()
            vim.initialise()

            _mock_qapp.focusChanged.connect.assert_called_once_with(vim.onFocusChanged)

    def test_initialise_with_empty_config_does_nothing(self, _mock_qapp):
        from qtpyvcp.plugins.virtual_input_manager import VirtualInputManager

        config_dict = {
            'virtual_input_providers': {}
        }

        with patch('qtpyvcp.plugins.virtual_input_manager.CONFIG', config_dict):
            vim = VirtualInputManager()
            vim.initialise()

            assert vim.input_providers == {}
