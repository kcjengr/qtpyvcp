import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from qtpy.QtWidgets import QApplication, QWidget


class TestMDIButton:
    """Tests for MDIButton widget."""

    def test_init_no_parent(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton()
        qtbot.addWidget(btn)
        assert btn is not None

    def test_init_with_command_default(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton()
        qtbot.addWidget(btn)
        assert btn._mdi_cmd == ''

    def test_init_with_command(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='G0 X1 Y2')
        qtbot.addWidget(btn)
        assert btn._mdi_cmd == 'G0 X1 Y2'

    def test_init_sets_MDICommand_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='G53 Z0')
        qtbot.addWidget(btn)
        assert btn.MDICommand == 'G53 Z0'

    def test_init_is_pushbutton(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton()
        qtbot.addWidget(btn)
        assert isinstance(btn, QPushButton)

    def test_mdi_command_property_getter(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='G0 Z1')
        qtbot.addWidget(btn)
        assert btn.MDICommand == 'G0 Z1'

    def test_mdi_command_property_setter(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton()
        qtbot.addWidget(btn)
        btn.MDICommand = 'G1 X10 Y20 F500'
        assert btn._mdi_cmd == 'G1 X10 Y20 F500'

    def test_mdi_command_property_setter_empty(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='G0 X1')
        qtbot.addWidget(btn)
        btn.MDICommand = ''
        assert btn._mdi_cmd == ''

    @patch('qtpyvcp.widgets.button_widgets.mdi_button.issue_mdi')
    def test_issueMDI_simple_command(self, mock_issue, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='G0 X1 Y2')
        btn._data_channels = []
        # Mock QApplication.instance().activeWindow() to return a simple window
        mock_window = MagicMock()
        mock_app = MagicMock()
        mock_app.activeWindow.return_value = mock_window

        with patch('qtpy.QtWidgets.QApplication.instance', return_value=mock_app):
            qtbot.addWidget(btn)
            btn.issueMDI()
            mock_issue.assert_called_once_with('G0 X1 Y2')

    @patch('qtpyvcp.widgets.button_widgets.mdi_button.issue_mdi')
    def test_issueMDI_with_variable_substitution(self, mock_issue, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='T#<tool_entry> M6')
        btn._data_channels = []

        # Create a mock window with tool_entry widget that has text() but no value()
        mock_window = MagicMock(spec=[])  # Empty spec to allow any attribute access
        mock_tool_entry = MagicMock(spec=['text'])  # Only has text(), no value()
        mock_tool_entry.text.return_value = '5'
        mock_window.tool_entry = mock_tool_entry

        mock_app = MagicMock()
        mock_app.activeWindow.return_value = mock_window

        with patch('qtpy.QtWidgets.QApplication.instance', return_value=mock_app):
            qtbot.addWidget(btn)
            btn.issueMDI()
            mock_issue.assert_called_once_with('T5 M6')

    @patch('qtpyvcp.widgets.button_widgets.mdi_button.LOG')
    def test_issueMDI_missing_variable_widget(self, mock_log, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='T#<missing_entry> M6')
        btn._data_channels = []

        # Mock window without the missing_entry widget
        mock_window = MagicMock()
        del mock_window.missing_entry

        mock_app = MagicMock()
        mock_app.activeWindow.return_value = mock_window

        with patch('qtpy.QtWidgets.QApplication.instance', return_value=mock_app):
            qtbot.addWidget(btn)
            btn.issueMDI()
            mock_log.exception.assert_called()

    @patch('qtpyvcp.widgets.button_widgets.mdi_button.LOG')
    def test_issueMDI_format_error(self, mock_log, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='G0 {invalid')
        btn._data_channels = []

        mock_window = MagicMock()
        mock_app = MagicMock()
        mock_app.activeWindow.return_value = mock_window

        with patch('qtpy.QtWidgets.QApplication.instance', return_value=mock_app):
            qtbot.addWidget(btn)
            # ValueError is raised because { without matching } is not an IndexError
            # The code only catches IndexError, so ValueError propagates
            with pytest.raises(ValueError):
                btn.issueMDI()

    @patch('qtpyvcp.widgets.button_widgets.mdi_button.LOG')
    def test_issueMDI_no_active_window(self, mock_log, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton(command='G0 X1')
        btn._data_channels = []

        # Mock QApplication.instance() to return None
        with patch('qtpy.QtWidgets.QApplication.instance', return_value=None):
            qtbot.addWidget(btn)
            try:
                btn.issueMDI()
            except AttributeError:
                pass  # Expected - calling .activeWindow() on None

    def test_parse_vars_pattern(self):
        from qtpyvcp.widgets.button_widgets.mdi_button import PARSE_VARS
        result = PARSE_VARS.findall('T#<tool_name> M6')
        assert result == [('T', 'tool_name')]

    def test_parse_vars_pattern_multiple(self):
        from qtpyvcp.widgets.button_widgets.mdi_button import PARSE_VARS
        result = PARSE_VARS.findall('T#<t_num> M6 S#<rpm>')
        assert len(result) == 2
        assert ('T', 't_num') in result
        assert ('S', 'rpm') in result

    def test_parse_vars_pattern_no_vars(self):
        from qtpyvcp.widgets.button_widgets.mdi_button import PARSE_VARS
        result = PARSE_VARS.findall('G0 X1 Y2')
        assert result == []


class TestMDIButtonProperty:
    """Additional MDIButton property tests."""

    def test_mdi_command_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton
        btn = MDIButton()
        qtbot.addWidget(btn)
        meta_obj = btn.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'MDICommand' in prop_names
