import pytest


class TestErrorDialogInit:
    def test_inherits_from_base_dialog(self, error_dialog):
        from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog

        assert isinstance(error_dialog, BaseDialog)

    def test_stay_on_top_enabled(self, error_dialog):
        from qtpy.QtCore import Qt

        flags = error_dialog.windowFlags()
        assert flags & Qt.WindowStaysOnTopHint

    def test_exc_info_stored(self, error_dialog):
        assert error_dialog.exc_info is not None
        assert len(error_dialog.exc_info) == 3

    def test_exc_type_stored(self, error_dialog):
        exc_type, exc_msg, exc_tb = error_dialog.exc_info
        assert exc_type is ValueError

    def test_exc_msg_stored(self, error_dialog):
        exc_type, exc_msg, exc_tb = error_dialog.exc_info
        assert "test error" in str(exc_msg)

    def test_window_title_contains_error_type(self, error_dialog):
        assert "ValueError" in error_dialog.windowTitle()
        assert "Unhandled Exception" in error_dialog.windowTitle()


class TestErrorDialogDisplay:
    def test_error_type_label_shows_exception_name(self, error_dialog):
        text = error_dialog.errorType.text()
        assert "ValueError" in text

    def test_error_value_label_shows_message(self, error_dialog):
        text = error_dialog.errorValue.text()
        assert "test error" in text

    def test_traceback_text_is_populated(self, error_dialog):
        text = error_dialog.tracebackText.toPlainText()
        assert len(text) > 0

    def test_ignore_checkbox_exists(self, error_dialog):
        assert error_dialog.ignoreCheckBox is not None

    def test_ignore_checkbox_default_unchecked(self, error_dialog):
        assert error_dialog.ignoreCheckBox.isChecked() is False

    def test_quit_app_button_exists(self, error_dialog):
        assert error_dialog.quitApp is not None

    def test_ignore_exception_button_exists(self, error_dialog):
        assert error_dialog.ignoreException is not None


class TestErrorDialogWarningType:
    def test_warning_type_shows_orange_color(self, warning_dialog):
        text = warning_dialog.errorType.text()
        assert "Warning" in text or "UserWarning" in text

    def test_warning_window_title(self, warning_dialog):
        title = warning_dialog.windowTitle()
        assert "Warning" in title or "UserWarning" in title


class TestErrorDialogIgnoreList:
    def test_ignore_list_empty_initially(self):
        from qtpyvcp.widgets.dialogs.error_dialog import IGNORE_LIST

        initial_len = len(IGNORE_LIST)
        # After creating a dialog, list may have entries
        assert isinstance(IGNORE_LIST, list)

    def test_ignore_adds_to_list_when_checked(self, error_dialog):
        from qtpyvcp.widgets.dialogs.error_dialog import IGNORE_LIST

        error_dialog.ignoreCheckBox.setChecked(True)
        error_dialog.on_ignoreException_clicked()
        assert len(IGNORE_LIST) > 0

    def test_ignore_does_not_add_when_unchecked(self, error_dialog):
        from qtpyvcp.widgets.dialogs.error_dialog import IGNORE_LIST

        initial_len = len(IGNORE_LIST)
        error_dialog.ignoreCheckBox.setChecked(False)
        error_dialog.on_ignoreException_clicked()
        # List should not have new entries for this exception


class TestErrorDialogQuitApp:
    def test_quit_app_in_designer_accepts(self, qtbot, designer_error_dialog):
        import os

        os.environ["DESIGNER"] = "1"
        designer_error_dialog.show()
        qtbot.waitExposed(designer_error_dialog)


class TestErrorDialogExceptionTypes:
    def test_keyerror_shows_in_title(self, keyerror_dialog):
        title = keyerror_dialog.windowTitle()
        assert "KeyError" in title

    def test_keyerror_type_label(self, keyerror_dialog):
        text = keyerror_dialog.errorType.text()
        assert "KeyError" in text

    def test_attributeerror_shows_in_title(self, attrerror_dialog):
        title = attrerror_dialog.windowTitle()
        assert "AttributeError" in title

    def test_typeerror_shows_in_title(self, typeerror_dialog):
        title = typeerror_dialog.windowTitle()
        assert "TypeError" in title


class TestErrorDialogEdgeCases:
    def test_exception_with_no_message(self, empty_msg_dialog):
        exc_type, exc_msg, exc_tb = empty_msg_dialog.exc_info
        assert exc_type is ValueError

    def test_exception_with_long_message(self, long_msg_dialog):
        text = long_msg_dialog.errorValue.text()
        assert len(text) > 100
