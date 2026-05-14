import pytest
from unittest.mock import MagicMock, patch


class TestGetDialog:
    """Tests for getDialog function."""

    def test_get_existing_dialog(self):
        from qtpyvcp.widgets.dialogs import getDialog, DIALOGS
        mock_dialog = MagicMock()
        with patch.dict(DIALOGS, {'test_dialog': mock_dialog}):
            result = getDialog('test_dialog')
            assert result == mock_dialog

    def test_get_missing_dialog(self, caplog):
        from qtpyvcp.widgets.dialogs import getDialog
        result = getDialog('nonexistent_dialog_xyz')
        assert result is None

    def test_get_dialog_logs_error(self, caplog):
        from qtpyvcp.widgets.dialogs import getDialog
        with caplog.at_level('ERROR'):
            getDialog('missing')
            assert 'was not found' in caplog.text


class TestShowDialog:
    """Tests for showDialog function."""

    def setup_method(self):
        from qtpyvcp.widgets.dialogs import ACTIVE_DIALOGS
        while len(ACTIVE_DIALOGS) > 0:
            ACTIVE_DIALOGS.pop()

    def test_show_missing_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs import showDialog

        with patch('qtpyvcp.widgets.dialogs.QMessageBox'):
            dialog = showDialog('nonexistent_xyz')
            assert dialog is None

    def test_show_existing_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs import showDialog, DIALOGS, ACTIVE_DIALOGS
        from qtpy.QtWidgets import QDialog

        mock_dialog = MagicMock(spec=QDialog)
        mock_dialog.width.return_value = 200
        mock_dialog.height.return_value = 100

        with patch('qtpyvcp.widgets.dialogs.QApplication') as MockApp:
            MockApp.instance.return_value.activeWindow.return_value = MagicMock()
            with patch.dict(DIALOGS, {'my_dialog': mock_dialog}):
                showDialog('my_dialog')

        assert mock_dialog.show.called
        assert mock_dialog in ACTIVE_DIALOGS

    def test_show_dialog_moves_to_center(self, qtbot):
        from qtpyvcp.widgets.dialogs import showDialog, DIALOGS
        from qtpy.QtWidgets import QDialog

        mock_dialog = MagicMock(spec=QDialog)
        mock_dialog.width.return_value = 200
        mock_dialog.height.return_value = 100

        mock_win = MagicMock()
        mock_win.mapToGlobal.return_value = MagicMock(x=lambda: 500, y=lambda: 400)
        from qtpy.QtCore import QPoint
        center_point = QPoint(100, 100)
        mock_rect = MagicMock(center=MagicMock(return_value=center_point))
        mock_win.rect.return_value = mock_rect

        with patch('qtpyvcp.widgets.dialogs.QApplication') as MockApp:
            MockApp.instance.return_value.activeWindow.return_value = mock_win
            with patch.dict(DIALOGS, {'my_dialog': mock_dialog}):
                showDialog('my_dialog')


class TestHideDialogs:
    """Tests for hideActiveDialog and hideDialog functions."""

    def setup_method(self):
        from qtpyvcp.widgets.dialogs import ACTIVE_DIALOGS
        while len(ACTIVE_DIALOGS) > 0:
            ACTIVE_DIALOGS.pop()

    def test_hide_active_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs import hideActiveDialog, ACTIVE_DIALOGS
        from qtpy.QtWidgets import QDialog

        mock_dialog = MagicMock(spec=QDialog)
        mock_dialog.hide = MagicMock()
        ACTIVE_DIALOGS.append(mock_dialog)

        hideActiveDialog()

        assert mock_dialog.hide.called
        assert len(ACTIVE_DIALOGS) == 0

    def test_hide_active_dialog_empty_list(self, qtbot):
        from qtpyvcp.widgets.dialogs import hideActiveDialog

        hideActiveDialog()

    def test_hide_named_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs import hideDialog, DIALOGS
        from qtpy.QtWidgets import QDialog

        mock_dialog = MagicMock(spec=QDialog)
        mock_dialog.hide = MagicMock()

        with patch.dict(DIALOGS, {'my_dialog': mock_dialog}):
            hideDialog('my_dialog')

        assert mock_dialog.hide.called

    def test_hide_named_dialog_missing(self):
        from qtpyvcp.widgets.dialogs import hideDialog
        with pytest.raises(AttributeError):
            hideDialog('nonexistent_xyz')


class TestAskQuestion:
    """Tests for askQuestion function."""

    def test_ask_question_yes(self, qtbot):
        from qtpyvcp.widgets.dialogs import askQuestion

        with patch('qtpyvcp.widgets.dialogs.QMessageBox') as MockMsgBox:
            MockMsgBox.question.return_value = MockMsgBox.Yes
            result = askQuestion('Title', 'Message')
            assert result is True

    def test_ask_question_no(self, qtbot):
        from qtpyvcp.widgets.dialogs import askQuestion

        with patch('qtpyvcp.widgets.dialogs.QMessageBox') as MockMsgBox:
            MockMsgBox.question.return_value = MockMsgBox.No
            result = askQuestion('Title', 'Message')
            assert result is False

    def test_ask_question_with_parent(self, qtbot):
        from qtpyvcp.widgets.dialogs import askQuestion

        parent = MagicMock()

        with patch('qtpyvcp.widgets.dialogs.QMessageBox') as MockMsgBox:
            MockMsgBox.question.return_value = MockMsgBox.Yes
            askQuestion('Title', 'Message', parent=parent)
            MockMsgBox.question.assert_called_once()
            call_args = MockMsgBox.question.call_args
            assert call_args[0][0] is parent

    def test_ask_question_no_parent_uses_active_window(self, qtbot):
        from qtpyvcp.widgets.dialogs import askQuestion

        with patch('qtpyvcp.widgets.dialogs.QMessageBox') as MockMsgBox:
            MockMsgBox.question.return_value = MockMsgBox.Yes
            with patch('qtpyvcp.widgets.dialogs.QApplication') as MockApp:
                mock_win = MagicMock()
                MockApp.instance.return_value.activeWindow.return_value = mock_win
                askQuestion()
                call_args = MockMsgBox.question.call_args
                assert call_args[0][0] is mock_win


class TestActiveDialogsState:
    """Tests for ACTIVE_DIALOGS list state management."""

    def setup_method(self):
        from qtpyvcp.widgets.dialogs import ACTIVE_DIALOGS
        while len(ACTIVE_DIALOGS) > 0:
            ACTIVE_DIALOGS.pop()

    def test_active_dialogs_starts_empty(self):
        from qtpyvcp.widgets.dialogs import ACTIVE_DIALOGS
        assert len(ACTIVE_DIALOGS) == 0

    def test_showDialog_appends_to_active(self, qtbot):
        from qtpyvcp.widgets.dialogs import showDialog, DIALOGS, ACTIVE_DIALOGS
        from qtpy.QtWidgets import QDialog

        mock_dialog = MagicMock(spec=QDialog)
        mock_dialog.width.return_value = 200
        mock_dialog.height.return_value = 100

        with patch('qtpyvcp.widgets.dialogs.QApplication') as MockApp:
            MockApp.instance.return_value.activeWindow.return_value = MagicMock()
            with patch.dict(DIALOGS, {'d1': mock_dialog}):
                showDialog('d1')

        assert len(ACTIVE_DIALOGS) == 1
        assert ACTIVE_DIALOGS[0] is mock_dialog

    def test_multiple_showDialog_appends_all(self, qtbot):
        from qtpyvcp.widgets.dialogs import showDialog, DIALOGS, ACTIVE_DIALOGS
        from qtpy.QtWidgets import QDialog

        d1 = MagicMock(spec=QDialog)
        d1.width.return_value = 200
        d1.height.return_value = 100
        d2 = MagicMock(spec=QDialog)
        d2.width.return_value = 300
        d2.height.return_value = 200

        with patch('qtpyvcp.widgets.dialogs.QApplication') as MockApp:
            MockApp.instance.return_value.activeWindow.return_value = MagicMock()
            with patch.dict(DIALOGS, {'d1': d1, 'd2': d2}):
                showDialog('d1')
                showDialog('d2')

        assert len(ACTIVE_DIALOGS) == 2
        assert ACTIVE_DIALOGS[0] is d1
        assert ACTIVE_DIALOGS[1] is d2

    def test_hideActiveDialog_pops_last(self, qtbot):
        from qtpyvcp.widgets.dialogs import hideActiveDialog, ACTIVE_DIALOGS
        from qtpy.QtWidgets import QDialog

        d1 = MagicMock(spec=QDialog)
        d1.hide = MagicMock()
        d2 = MagicMock(spec=QDialog)
        d2.hide = MagicMock()

        ACTIVE_DIALOGS.extend([d1, d2])

        hideActiveDialog()

        assert len(ACTIVE_DIALOGS) == 1
        assert d2.hide.called
        assert not d1.hide.called


class TestShowDialogNotFound:
    """Tests for showDialog when dialog is not found."""

    def setup_method(self):
        from qtpyvcp.widgets.dialogs import ACTIVE_DIALOGS
        while len(ACTIVE_DIALOGS) > 0:
            ACTIVE_DIALOGS.pop()

    def test_show_dialog_not_found_shows_critical(self, qtbot):
        from qtpyvcp.widgets.dialogs import showDialog

        with patch('qtpyvcp.widgets.dialogs.QMessageBox') as MockMsgBox:
            showDialog('missing_dialog')
            MockMsgBox.critical.assert_called_once()
            call_args = MockMsgBox.critical.call_args
            assert 'Dialog not found' in str(call_args[0][1])
            assert 'missing_dialog' in str(call_args[0][2])
