"""Tests for qtpyvcp.plugins.user_managment.UserManagement plugin."""

import pytest
from unittest.mock import MagicMock, patch


class TestUserManagementInit:
    def test_init_creates_users_dict(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        assert um.users == {}

    def test_init_creates_user_levels_dict(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        assert um.user_levels == {}

    def test_init_has_current_username_channel(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        assert 'currentUserName' in um.channels

    def test_init_has_current_user_level_channel(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        assert 'currentUserLevel' in um.channels


class TestUserManagementChannels:
    def test_current_username_returns_no_user_when_none(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        result = um.currentUserName.getValue()
        assert result == 'No User'

    def test_current_level_returns_minus_one_when_none(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        result = um.currentUserLevel.getValue()
        assert result == -1


class TestUserManagementLogin:
    def test_login_with_unknown_user_fails(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        result = um.loginUser('unknown', 'password')
        assert result is False

    def test_login_with_wrong_password_fails(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.users['admin'] = 'correct_pass'
        um.user_levels['admin'] = 10
        result = um.loginUser('admin', 'wrong_pass')
        assert result is False

    def test_login_with_correct_credentials_succeeds(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.users['admin'] = 'correct_pass'
        um.user_levels['admin'] = 10
        result = um.loginUser('admin', 'correct_pass')
        assert result is True

    def test_login_sets_current_user_level(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.users['manager'] = 'secret'
        um.user_levels['manager'] = 7
        um.loginUser('manager', 'secret')
        assert um.currentUserLevel.getValue() == 7

    def test_login_with_empty_username_fails(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        result = um.loginUser('', 'password')
        assert result is False

    def test_login_with_empty_password_for_unknown_user_fails(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        result = um.loginUser('nobody', '')
        assert result is False


class TestUserManagementLogoff:
    def test_logoff_resets_level_to_minus_one(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.currentUserLevel.value = 5
        um.logoffUser()
        assert um.currentUserLevel.getValue() == -1

    def test_logoff_sets_username_channel_value_to_empty(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.currentUserName.value = 'logged_user'
        um.logoffUser()
        assert um.currentUserName.value == ''


class TestUserManagementPermissions:
    def test_check_permissions_passes_when_level_higher(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.currentUserLevel.value = 10
        assert um.checkPermissions(5) is True

    def test_check_permissions_passes_when_levels_equal(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.currentUserLevel.value = 5
        assert um.checkPermissions(5) is True

    def test_check_permissions_fails_when_level_lower(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.currentUserLevel.value = 2
        assert um.checkPermissions(5) is False

    def test_check_permissions_with_zero_required_level(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        um.currentUserLevel.value = 0
        assert um.checkPermissions(0) is True


class TestUserManagementSetWidgetEnablement:
    def test_set_widget_enablement_checks_security_attr(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        mock_widget = MagicMock()
        mock_widget.security = 5
        mock_widget.setEnabled = MagicMock()

        with patch('qtpy.QtWidgets.QApplication.allWidgets', return_value=[mock_widget]):
            um.currentUserLevel.value = 10
            um.setWidgetEnablementPerPermission(None)
            mock_widget.setEnabled.assert_called_once_with(True)

    def test_set_widget_enablement_disables_when_insufficient(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        mock_widget = MagicMock()
        mock_widget.security = 10
        mock_widget.setEnabled = MagicMock()

        with patch('qtpy.QtWidgets.QApplication.allWidgets', return_value=[mock_widget]):
            um.currentUserLevel.value = 5
            um.setWidgetEnablementPerPermission(None)
            mock_widget.setEnabled.assert_called_once_with(False)

    def test_set_widget_enablement_skips_widgets_without_security(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        mock_widget = MagicMock(spec=['setText'])

        with patch('qtpy.QtWidgets.QApplication.allWidgets', return_value=[mock_widget]):
            um = UserManagement()
            um.setWidgetEnablementPerPermission(None)

    def test_set_widget_enablement_skips_widgets_without_setEnabled(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        widget = MagicMock()
        widget.security = 5
        del widget.setEnabled

        with patch('qtpy.QtWidgets.QApplication.allWidgets', return_value=[widget]):
            um = UserManagement()
            um.setWidgetEnablementPerPermission(None)

    def test_set_widget_enablement_with_multiple_widgets(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        w1 = MagicMock(security=5, setEnabled=MagicMock())
        w2 = MagicMock(security=10, setEnabled=MagicMock())

        with patch('qtpy.QtWidgets.QApplication.allWidgets', return_value=[w1, w2]):
            um = UserManagement()
            um.currentUserLevel.value = 7
            um.setWidgetEnablementPerPermission(None)
            w1.setEnabled.assert_called_once_with(True)
            w2.setEnabled.assert_called_once_with(False)


class TestUserManagementCacheUsers:
    def test_cache_users_reads_user_file(self, tmp_path):
        from qtpyvcp.plugins.user_managment import UserManagement

        user_file = tmp_path / 'users.txt'
        user_file.write_text('admin admin123 10\noperator op456 5\nguest guest789 0\n')

        um = UserManagement()
        with patch('qtpyvcp.plugins.user_managment.normalizePath', return_value=str(user_file)):
            with patch('os.getenv', return_value=str(tmp_path)):
                um.cacheUsers()

        assert 'admin' in um.users
        assert 'operator' in um.users
        assert 'guest' in um.users

    def test_cache_users_stores_passwords(self, tmp_path):
        from qtpyvcp.plugins.user_managment import UserManagement

        user_file = tmp_path / 'users.txt'
        user_file.write_text('admin admin123 10\n')

        um = UserManagement()
        with patch('qtpyvcp.plugins.user_managment.normalizePath', return_value=str(user_file)):
            with patch('os.getenv', return_value=str(tmp_path)):
                um.cacheUsers()

        assert um.users['admin'] == 'admin123'

    def test_cache_users_stores_security_levels(self, tmp_path):
        from qtpyvcp.plugins.user_managment import UserManagement

        user_file = tmp_path / 'users.txt'
        user_file.write_text('admin admin123 10\noperator op456 5\n')

        um = UserManagement()
        with patch('qtpyvcp.plugins.user_managment.normalizePath', return_value=str(user_file)):
            with patch('os.getenv', return_value=str(tmp_path)):
                um.cacheUsers()

        assert um.user_levels['admin'] == 10
        assert um.user_levels['operator'] == 5

    def test_cache_users_skips_comment_lines(self, tmp_path):
        from qtpyvcp.plugins.user_managment import UserManagement

        user_file = tmp_path / 'users.txt'
        user_file.write_text('# This is a comment\nadmin admin123 10\n# Another comment\n')

        um = UserManagement()
        with patch('qtpyvcp.plugins.user_managment.normalizePath', return_value=str(user_file)):
            with patch('os.getenv', return_value=str(tmp_path)):
                um.cacheUsers()

        assert 'admin' in um.users
        assert 'This' not in um.users

    def test_cache_users_skips_blank_lines(self, tmp_path):
        from qtpyvcp.plugins.user_managment import UserManagement

        user_file = tmp_path / 'users.txt'
        user_file.write_text('admin admin123 10\n\noperator op456 5\n')

        um = UserManagement()
        with patch('qtpyvcp.plugins.user_managment.normalizePath', return_value=str(user_file)):
            with patch('os.getenv', return_value=str(tmp_path)):
                um.cacheUsers()

        assert 'admin' in um.users
        assert 'operator' in um.users

    def test_cache_users_skips_malformed_lines(self, tmp_path):
        from qtpyvcp.plugins.user_managment import UserManagement

        user_file = tmp_path / 'users.txt'
        user_file.write_text('admin admin123 10\nbadline\noperator op456 5\n')

        um = UserManagement()
        with patch('qtpyvcp.plugins.user_managment.normalizePath', return_value=str(user_file)):
            with patch('os.getenv', return_value=str(tmp_path)):
                um.cacheUsers()

        assert 'admin' in um.users
        assert 'operator' in um.users


class TestUserManagementInitialise:
    def test_initialise_calls_cache_users(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        with patch.object(um, 'cacheUsers') as mock_cache:
            um.initialise()
            mock_cache.assert_called_once()


class TestUserManagementTerminate:
    def test_terminate_is_noop(self):
        from qtpyvcp.plugins.user_managment import UserManagement
        um = UserManagement()
        # Should not raise
        um.terminate()
