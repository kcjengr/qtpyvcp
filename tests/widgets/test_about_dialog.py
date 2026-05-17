import pytest
from unittest.mock import patch, MagicMock


class TestAboutDialogInit:
    """Tests for AboutDialog initialization."""

    def test_init_no_ui_file(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        assert dialog is not None

    def test_init_with_ui_file(self, qtbot):
        from qtpy.QtWidgets import QDialog
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        mock_form_class = MagicMock()
        mock_form_instance = MagicMock()
        mock_form_class.return_value = mock_form_instance

        with patch('qtpyvcp.widgets.dialogs.about_dialog.PySide6Ui') as MockPySide6Ui:
            MockPySide6Ui.return_value.load.return_value = (mock_form_class, None)
            dialog = AboutDialog(ui_file='custom.ui')
            qtbot.addWidget(dialog)
            MockPySide6Ui.assert_called_once()
            call_args = MockPySide6Ui.call_args
            assert 'custom.ui' in call_args[0][0] or call_args[0][0].endswith('custom.ui')

    def test_init_stay_on_top(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        flags = dialog.windowFlags()
        assert flags & Qt.WindowStaysOnTopHint


class TestAboutDialogDefaultUI:
    """Tests for AboutDialog default (programmatic) UI creation."""

    def test_window_title(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "About QtPyVCP"

    def test_fixed_size(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        assert dialog.size().width() == 600
        assert dialog.size().height() == 200

    def test_about_text_label_exists(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        assert dialog.about_text is not None

    def test_about_text_allows_external_links(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        assert dialog.about_text.openExternalLinks() is True

    def test_about_text_contains_version(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        text = dialog.about_text.text()
        assert 'Version:' in text

    def test_about_text_contains_copyright(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        text = dialog.about_text.text()
        assert 'Copyright' in text or 'copyright' in text

    def test_about_text_contains_url(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        text = dialog.about_text.text()
        assert 'qtpyvcp.com' in text or 'https://' in text

    def test_button_box_exists(self, qtbot):
        from qtpy.QtWidgets import QDialogButtonBox
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        assert dialog.button_box is not None
        assert isinstance(dialog.button_box, QDialogButtonBox)

    def test_button_box_has_ok_button(self, qtbot):
        from qtpy.QtWidgets import QDialogButtonBox
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        buttons = dialog.button_box.buttons()
        ok_buttons = [b for b in buttons if 'OK' in b.text()]
        assert len(ok_buttons) > 0

    def test_button_box_accepts_on_ok(self, qtbot):
        from qtpy.QtWidgets import QDialogButtonBox
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        accepted = False

        def on_accepted():
            nonlocal accepted
            accepted = True

        dialog.button_box.accepted.connect(on_accepted)
        ok_btn = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.click()
        assert accepted is True

    def test_close_button_closes_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)
        dialog.close()
        assert dialog.isVisible() is False


class TestAboutDialogInheritance:
    """Tests for AboutDialog inheritance."""

    def test_inherits_from_base_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
        from qtpyvcp.widgets.dialogs.about_dialog import AboutDialog

        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        assert isinstance(dialog, BaseDialog)
