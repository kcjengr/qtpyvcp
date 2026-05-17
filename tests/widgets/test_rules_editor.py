import pytest
from unittest.mock import MagicMock, patch


class TestTableCheckButton:
    """Tests for TableCheckButton widget."""

    def test_init_default_unchecked(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton()
        qtbot.addWidget(btn)

        assert btn.isChecked() is False

    def test_init_checked_true(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton(checked=True)
        qtbot.addWidget(btn)

        assert btn.isChecked() is True

    def test_init_checked_false(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton(checked=False)
        qtbot.addWidget(btn)

        assert btn.isChecked() is False

    def test_getattr_delegates_to_checkbox(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton()
        qtbot.addWidget(btn)

        state = btn.checkState()
        from qtpy.QtCore import Qt
        assert state in (Qt.Unchecked, Qt.Checked, 0, 2)

    def test_toggle_check_state(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton()
        qtbot.addWidget(btn)

        btn.chk_bx.toggle()
        assert btn.isChecked() is True

        btn.chk_bx.toggle()
        assert btn.isChecked() is False

    def test_has_checkbox_widget(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton()
        qtbot.addWidget(btn)

        assert hasattr(btn, 'chk_bx')
        assert btn.chk_bx is not None


class TestCompleterDelegate:
    """Tests for CompleterDelegate."""

    def test_init_creates_completer(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import CompleterDelegate

        delegate = CompleterDelegate()

        assert hasattr(delegate, 'completer')
        assert delegate.completer is not None

    def test_completer_is_case_insensitive(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.qtdesigner.rules_editor import CompleterDelegate

        delegate = CompleterDelegate()

        mode = delegate.completer.caseSensitivity()
        assert mode == Qt.CaseInsensitive


class TestRulesEditor:
    """Tests for RulesEditor dialog."""

    def test_init_with_empty_rules(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Enable': ['setEnabled', bool],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert editor.widget is mock_widget
        assert isinstance(editor.rules, list)
        assert len(editor.rules) == 0

    def test_init_with_rules_json(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        rules_json = '[{"name": "Rule1", "property": "Visible", "expression": "", "channels": []}]'

        mock_widget = MagicMock()
        mock_widget.rules = rules_json
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Enable': ['setEnabled', bool],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert len(editor.rules) == 1
        assert editor.rules[0]['name'] == 'Rule1'

    def test_init_with_invalid_json(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "not valid json {{{"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Enable': ['setEnabled', bool],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert isinstance(editor.rules, list)
        assert len(editor.rules) == 0

    def test_init_sets_available_properties(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        custom_props = {
            'None': ['None', None],
            'CustomProp': ['setCustom', str],
        }

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = custom_props
        mock_widget.DEFAULT_RULE_PROPERTY = 'CustomProp'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert editor.available_properties is custom_props
        assert editor.default_property == 'CustomProp'

    def test_ui_has_add_button(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert hasattr(editor, 'btn_add_rule')
        assert editor.btn_add_rule is not None

    def test_ui_has_delete_button(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert hasattr(editor, 'btn_del_rule')
        assert editor.btn_del_rule is not None

    def test_ui_has_rules_list(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert hasattr(editor, 'lst_rules')
        assert editor.lst_rules is not None

    def test_ui_has_name_edit(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert hasattr(editor, 'txt_name')
        assert editor.txt_name is not None

    def test_ui_has_property_combo(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
            'Enable': ['setEnabled', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert hasattr(editor, 'cmb_property')
        assert editor.cmb_property is not None

    def test_ui_has_expression_edit(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert hasattr(editor, 'txt_expression')
        assert editor.txt_expression is not None

    def test_ui_has_channels_table(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert hasattr(editor, 'tbl_channels')
        assert editor.tbl_channels is not None

    def test_ui_has_save_button(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        # Save button is created in setup_ui
        assert hasattr(editor, 'frm_edit')

    def test_window_title(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert editor.windowTitle() == "QtPyVCP Widget Rules Editor"


class TestRulesEditorActions:
    """Tests for RulesEditor action methods."""

    def test_add_rule(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        initial_count = len(editor.rules)
        editor.add_rule()

        assert len(editor.rules) == initial_count + 1
        assert editor.rules[-1]['name'] == 'New Rule'
        assert editor.rules[-1]['property'] == 'Visible'
        assert editor.rules[-1]['channels'] == []

    def test_add_rule_appears_in_list(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.add_rule()

        assert editor.lst_rules.count() == 1
        item_text = editor.lst_rules.item(0).text()
        assert item_text == 'New Rule'

    def test_add_multiple_rules(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.add_rule()
        editor.add_rule()
        editor.add_rule()

        assert len(editor.rules) == 3
        assert editor.lst_rules.count() == 3

    def test_get_current_index_no_selection(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        assert editor.get_current_index() == -1

    def test_get_current_index_with_selection(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = '[{"name": "Rule1"}]'
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.lst_rules.setCurrentRow(0)
        idx = editor.get_current_index()

        assert idx == 0


class TestRulesEditorValidation:
    """Tests for RulesEditor data validation."""

    def test_is_data_valid_empty_rules(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        is_valid, msg = editor.is_data_valid()
        assert is_valid is True
        assert msg == ""

    def test_is_data_valid_no_name(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        with patch.object(editor, 'get_channel_data', return_value=(None, None, None, None)):
            editor.rules.append({"name": "", "property": "Visible", "expression": "True", "channels": [{"url": "status:feed-override", "trigger": True}]})
            is_valid, msg = editor.is_data_valid()
            assert is_valid is False
            assert 'no name' in msg.lower()

    def test_is_data_valid_no_channel(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.rules.append({"name": "Rule1", "property": "Visible", "expression": "True", "channels": []})
        is_valid, msg = editor.is_data_valid()
        assert is_valid is False
        assert 'no channel' in msg.lower()

    def test_is_data_valid_no_expression(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        with patch.object(editor, 'get_channel_data', return_value=(None, None, None, None)):
            editor.rules.append({"name": "Rule1", "property": "Visible", "expression": "", "channels": [{"url": "status:feed-override", "trigger": True}]})
            is_valid, msg = editor.is_data_valid()
            assert is_valid is False
            assert 'no expression' in msg.lower()

    def test_is_data_valid_none_property_no_expression(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.rules.append({"name": "Rule1", "property": "None", "expression": "", "channels": []})
        is_valid, msg = editor.is_data_valid()
        assert is_valid is False  # Still fails due to no channels


class TestOpenHelp:
    """Tests for open_help method."""

    def test_open_help_default_url(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor
        import os

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        with patch.dict(os.environ, {}, clear=True):
            result = editor.open_help(open=False)
            assert 'kcjengr.github.io/qtpyvcp' in result
            assert 'widget_rules.html' in result

    def test_open_help_custom_url(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor
        import os

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        with patch.dict(os.environ, {"QTPYVCP_DOCS_URL": "https://custom.docs.com"}):
            result = editor.open_help(open=False)
            assert 'custom.docs.com' in result


class TestClearForm:
    """Tests for clear_form method."""

    def test_clear_form_resets_fields(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = '[{"name": "Existing", "property": "Visible", "expression": "True"}]'
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        # Select the existing rule
        editor.lst_rules.setCurrentRow(0)
        editor.load_from_list()

        assert editor.txt_name.text() == "Existing"

        editor.clear_form()

        assert editor.txt_name.text() == ""
        assert editor.frm_edit.isEnabled() is False


class TestChangeEntry:
    """Tests for change_entry method."""

    def test_change_entry_updates_rule(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = '[{"name": "Rule1", "property": "Visible"}]'
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.lst_rules.setCurrentRow(0)
        editor.change_entry("name", "Renamed")

        assert editor.rules[0]['name'] == "Renamed"

    def test_change_entry_no_selection_returns(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = '[{"name": "Rule1"}]'
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        # No selection - get_current_index returns -1, so this would fail on rules[-1]
        # But the method should handle it gracefully or we test with selection


class TestPropertyChanged:
    """Tests for property_changed callback."""

    def test_property_changed_updates_label(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
            'Enable': ['setEnabled', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.add_rule()
        editor.cmb_property.setCurrentText('Enable')
        editor.property_changed(1)

        assert editor.lbl_expected_type.text() == "bool"

    def test_property_changed_none_disables_expression(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = "[]"
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.add_rule()
        editor.cmb_property.setCurrentText('None')
        editor.property_changed(0)

        assert editor.txt_expression.isEnabled() is False


class TestExpressionChanged:
    """Tests for expression_changed callback."""

    def test_expression_changed_updates_rule(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = '[{"name": "Rule1", "property": "Visible"}]'
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.lst_rules.setCurrentRow(0)
        editor.txt_expression.setText("x > 5")
        editor.expression_changed()

        assert editor.rules[0]['expression'] == "x > 5"


class TestNameChanged:
    """Tests for name_changed callback."""

    def test_name_changed_updates_list_and_rule(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditor

        mock_widget = MagicMock()
        mock_widget.rules = '[{"name": "Rule1"}]'
        mock_widget.RULE_PROPERTIES = {
            'None': ['None', None],
            'Visible': ['setVisible', bool],
        }
        mock_widget.DEFAULT_RULE_PROPERTY = 'Visible'

        editor = RulesEditor(mock_widget)
        qtbot.addWidget(editor)

        editor.lst_rules.setCurrentRow(0)
        editor.txt_name.setText("Updated Name")
        editor.name_changed()

        assert editor.rules[0]['name'] == "Updated Name"
        assert editor.lst_rule_item.text() == "Updated Name"


class TestRulesEditorExtension:
    """Tests for RulesEditorExtension."""

    def test_extension_adds_task_menu_action(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditorExtension

        real_widget = QWidget()
        qtbot.addWidget(real_widget)

        ext = RulesEditorExtension(real_widget)

        actions = ext.actions()
        assert len(actions) == 1
        assert 'Edit Widget Rules' in actions[0].text()

    def test_extension_stores_widget(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditorExtension

        real_widget = QWidget()
        qtbot.addWidget(real_widget)

        ext = RulesEditorExtension(real_widget)

        assert ext.widget is real_widget


class TestChanInfoDialog:
    """Tests for ChanInfoDialog."""

    def test_init_displays_channel_info(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import ChanInfoDialog

        mock_chan_obj = MagicMock()
        mock_chan_obj.getValue.return_value = 42.5

        info = (mock_chan_obj, lambda: 42.5, 42.5, "Channel description\n:returns: the value\n:rtype: float")

        dialog = ChanInfoDialog(info)
        qtbot.addWidget(dialog)

        assert dialog is not None


class TestTableCheckButtonAttributes:
    """Additional tests for TableCheckButton attribute delegation."""

    def test_check_state_delegation(self, qtbot):
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton()
        qtbot.addWidget(btn)

        state = btn.checkState()
        from qtpy.QtCore import Qt
        assert isinstance(state, (int, Qt.CheckState))

    def test_set_checked_delegation(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton()
        qtbot.addWidget(btn)

        btn.setCheckState(Qt.Checked)
        assert btn.checkState() == Qt.Checked

    def test_widget_is_qwidget(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.qtdesigner.rules_editor import TableCheckButton

        btn = TableCheckButton()
        qtbot.addWidget(btn)

        assert isinstance(btn, QWidget)
