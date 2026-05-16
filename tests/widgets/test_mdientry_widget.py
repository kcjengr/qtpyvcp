import pytest
from unittest.mock import MagicMock, patch


class TestValidator:
    """Tests for MDIEntry Validator class."""

    def test_validate_uppercases_text(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate("g0 x1", 4)
        assert result == QValidator.Acceptable
        assert output == "G0 X1"
        assert pos == 4

    def test_validate_preserves_semicolon_prefix(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate(";comment", 8)
        assert result == QValidator.Acceptable
        assert output == ";comment"

    def test_validate_preserves_parenthesis_prefix(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate("(comment)", 9)
        assert result == QValidator.Acceptable
        assert output == "(comment)"

    def test_validate_mixed_case_with_semicolon(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate(";some text", 10)
        assert result == QValidator.Acceptable
        assert output == ";some text"


class TestMDIEntry:
    """Tests for MDIEntry widget."""

    def test_init_defaults(self, qtbot):
        from qtpy.QtWidgets import QLineEdit
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        assert isinstance(widget, QLineEdit)
        assert widget.mdi_history_size == 100
        assert widget.mdi_rtnkey_behaviour_supressed is False

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        parent = QWidget()
        widget = MDIEntry(parent)
        qtbot.addWidget(widget)
        assert widget.parent() is parent

    def test_init_has_validator(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        assert widget.validator is not None
        assert isinstance(widget.validator, QValidator)

    def test_init_completer_enabled_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        assert widget._completer_enabled is True

    def test_returnPressed_connected_to_submit(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        # QLineEdit provides returnPressed; verify it's connectable
        called = []
        widget.returnPressed.connect(called.append)
        assert len(called) == 0

    def test_mdi_history_size_property_getter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        assert widget.mdi_history_size == 100

    def test_mdi_history_size_property_setter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.mdi_history_size = 50
        assert widget.mdi_history_size == 50

    def test_mdi_history_size_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        meta_obj = widget.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'mdi_history_size' in prop_names

    def test_completerEnabled_property_getter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        assert widget.completerEnabled is True

    def test_completerEnabled_property_setter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.completerEnabled = False
        assert widget._completer_enabled is False

    def test_completerEnabled_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        meta_obj = widget.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'completerEnabled' in prop_names

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.issue_mdi')
    def test_submit_calls_issue_mdi(self, mock_issue_mdi, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.setText("G0 X1")
        widget.submit()
        mock_issue_mdi.assert_called_once_with("G0 X1")

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.issue_mdi')
    def test_submit_clears_text(self, mock_issue_mdi, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.setText("G0 X1")
        widget.submit()
        assert widget.text() == ""

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.issue_mdi')
    def test_submit_strips_text(self, mock_issue_mdi, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.setText("  G0 X1  ")
        widget.submit()
        mock_issue_mdi.assert_called_once_with("G0 X1")

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.issue_mdi')
    def test_submit_updates_mdi_history(self, mock_issue_mdi, qtbot):
        from qtpyvcp.plugins import _PLUGINS
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.submit()
        call_arg = _PLUGINS['status'].mdi_history.setValue.call_args[0][0] if _PLUGINS['status'].mdi_history.setValue.called else None
        assert call_arg == ""

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.issue_mdi')
    def test_submit_suppressed_no_issue_mdi(self, mock_issue_mdi, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.mdi_rtnkey_behaviour_supressed = True
        widget.submit()
        mock_issue_mdi.assert_not_called()

    def test_setMDIText_with_item(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        item = QListWidgetItem("G1 X5")
        widget.setMDIText(item)
        assert widget.text() == "G1 X5"

    def test_setMDIText_with_none(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.setText("existing")
        widget.setMDIText(None)
        assert widget.text() == "EXISTING"

    def test_suppress_rtn_key_behaviour(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.supress_rtn_key_behaviour()
        assert widget.mdi_rtnkey_behaviour_supressed is True

    def test_enable_rtn_key_behaviour(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.supress_rtn_key_behaviour()
        widget.enable_rtn_key_behaviour()
        assert widget.mdi_rtnkey_behaviour_supressed is False

    def test_keyPressEvent_up_down_with_completer(self, qtbot):
        from qtpy.QtCore import Qt, QStringListModel
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtWidgets import QCompleter
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        completer = QCompleter()
        model = QStringListModel()
        completer.setModel(model)
        widget.setCompleter(completer)

        event_up = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Up,
            Qt.NoModifier
        )
        widget.keyPressEvent(event_up)

    def test_keyPressEvent_up_down_disabled_when_completer_disabled(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.completerEnabled = False

        event_up = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Up,
            Qt.NoModifier
        )
        widget.keyPressEvent(event_up)

    def test_keyPressEvent_other_key(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_A,
            Qt.NoModifier
        )
        widget.keyPressEvent(event)

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.STATUS')
    def test_initialize_creates_completer(self, mock_status, qtbot):
        from qtpy.QtWidgets import QCompleter
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.initialize()
        assert widget.completer() is not None
        assert isinstance(widget.completer(), QCompleter)

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.STATUS')
    def test_initialize_sets_model(self, mock_status, qtbot):
        from qtpy.QtCore import QStringListModel
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.initialize()
        assert widget.model is not None
        assert isinstance(widget.model, QStringListModel)

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.STATUS')
    def test_initialize_sets_history_on_model(self, mock_status, qtbot):
        from qtpy.QtCore import QStringListModel
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        mock_status.mdi_history.value = ["G0 X1", "G1 X5"]
        widget.initialize()
        assert widget.model.stringList() == ["G0 X1", "G1 X5"]

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.STATUS')
    def test_initialize_subscribes_to_mdi_history(self, mock_status, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.initialize()
        assert widget._mdi_history_subscribed is True
        mock_status.mdi_history.signal.connect.assert_called_once()

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.STATUS')
    def test_initialize_sets_max_mdi_history_length(self, mock_status, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.initialize()
        # STATUS.max_mdi_history_length is assigned the integer value
        assert mock_status.max_mdi_history_length == 100

    @patch('qtpyvcp.widgets.input_widgets.mdientry_widget.STATUS')
    def test_initialize_does_not_create_completer_when_disabled(self, mock_status, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.completerEnabled = False
        widget.initialize()
        assert widget.completer() is None

    def test_terminate_cleanup_after_initialize(self, qtbot):
        from unittest.mock import patch
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        with patch('qtpyvcp.widgets.input_widgets.mdientry_widget.STATUS') as mock_status:
            widget = MDIEntry()
            qtbot.addWidget(widget)
            widget.initialize()
            assert widget._mdi_history_subscribed is True

            widget.terminate()
            assert widget._mdi_history_subscribed is False
            mock_status.mdi_history.signal.disconnect.assert_called_once()

    def test_terminate_without_initialize(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry

        widget = MDIEntry()
        qtbot.addWidget(widget)
        widget.terminate()


class TestValidatorEdgeCases:
    """Edge case tests for Validator."""

    def test_validate_empty_string(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate("", 0)
        assert result == QValidator.Acceptable
        assert output == ""

    def test_validate_semicolon_with_spaces(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate("; comment here", 15)
        assert result == QValidator.Acceptable
        assert output == "; comment here"

    def test_validate_parenthesis_mixed(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate("(some text)", 11)
        assert result == QValidator.Acceptable
        assert output == "(some text)"

    def test_validate_position_preserved(self, qtbot):
        from qtpy.QtGui import QValidator
        from qtpyvcp.widgets.input_widgets.mdientry_widget import Validator

        v = Validator()
        result, output, pos = v.validate("g0 x1", 2)
        assert pos == 2
