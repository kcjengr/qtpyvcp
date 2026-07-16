import pytest
from unittest.mock import MagicMock, patch


class TestDialogButtonInit:
    """Tests for DialogButton initialization."""

    def test_init_no_parent(self, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton()
        qtbot.addWidget(btn)
        assert btn is not None

    def test_init_with_dialog_name(self, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton(dialog_name='about')
        qtbot.addWidget(btn)
        assert btn._dialog_name == 'about'

    def test_init_empty_dialog_name(self, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton()
        qtbot.addWidget(btn)
        assert btn._dialog_name == ''

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        parent = QWidget()
        btn = DialogButton(parent=parent, dialog_name='test')
        qtbot.addWidget(btn)
        assert btn.parent() is parent


class TestDialogButtonProperty:
    """Tests for DialogButton dialogName property."""

    def test_dialog_name_getter_default(self, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton()
        qtbot.addWidget(btn)
        assert btn.dialogName == ''

    def test_dialog_name_setter(self, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton()
        qtbot.addWidget(btn)
        btn.dialogName = 'shutdown'
        assert btn._dialog_name == 'shutdown'

    def test_dialog_name_getter_after_set(self, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton(dialog_name='initial')
        qtbot.addWidget(btn)
        assert btn.dialogName == 'initial'


class TestDialogButtonClick:
    """Tests for DialogButton click-to-show behavior."""

    @patch('qtpyvcp.widgets.button_widgets.dialog_button.showDialog')
    def test_click_calls_showDialog_with_name(self, mock_show, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton(dialog_name='about')
        qtbot.addWidget(btn)
        btn.click()
        mock_show.assert_called_once_with('about')

    @patch('qtpyvcp.widgets.button_widgets.dialog_button.showDialog')
    def test_click_calls_showDialog_empty_name(self, mock_show, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton()
        qtbot.addWidget(btn)
        btn.click()
        mock_show.assert_called_once_with('')

    @patch('qtpyvcp.widgets.button_widgets.dialog_button.showDialog')
    def test_dialogName_property_setter_triggers_show(self, mock_show, qtbot):
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton()
        qtbot.addWidget(btn)
        btn.dialogName = 'new_dialog'
        mock_show.assert_not_called()


class TestDialogButtonInheritance:
    """Tests for DialogButton inheritance chain."""

    def test_inherits_from_vcp_button(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton

        btn = DialogButton()
        qtbot.addWidget(btn)
        assert isinstance(btn, QPushButton)
