import pytest
from unittest.mock import MagicMock, patch


class TestVCPLineEdit:
    """Tests for VCPLineEdit widget."""

    def test_init_no_parent(self, qtbot):
        from qtpy.QtWidgets import QLineEdit
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        assert isinstance(le, QLineEdit)

    def test_init_action_name_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        assert le._action_name == ''

    def test_actionName_property_getter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        assert le.actionName == ''

    def test_actionName_setter_stores_name(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        le.actionName = 'test.action'
        assert le._action_name == 'test.action'

    def test_actionName_does_not_bind(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        with patch('qtpyvcp.actions.bindWidget') as mock_bind:
            le = VCPLineEdit()
            qtbot.addWidget(le)
            le.actionName = 'test.action'
            # bindWidget should NOT be called (it's commented out with TODO)
            mock_bind.assert_not_called()

    def test_text_get_set(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        le.setText('Hello World')
        assert le.text() == 'Hello World'

    def test_clear(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        le.setText('Hello')
        le.clear()
        assert le.text() == ''

    def test_onReturnPressed_clears_focus(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        le.setText('test')
        # onReturnPressed should clear focus
        le.onReturnPressed()
        assert le.hasFocus() is False

    def test_default_rule_property(self):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        assert VCPLineEdit.DEFAULT_RULE_PROPERTY == 'Text'

    def test_rule_properties_contains_text(self):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        assert 'Text' in VCPLineEdit.RULE_PROPERTIES
        assert VCPLineEdit.RULE_PROPERTIES['Text'] == ['setText', str]

    def test_actionName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        meta_obj = le.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'actionName' in prop_names

    def test_initialize(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        # initialize should not raise
        le.initialize()

    def test_terminate(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        # terminate should not raise
        le.terminate()


class TestVCPLineEditText:
    """Tests for text-related functionality."""

    def test_placeholder_text(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        le.setPlaceholderText('Enter value...')
        assert le.placeholderText() == 'Enter value...'

    def test_echo_mode(self, qtbot):
        from qtpy.QtWidgets import QLineEdit
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        assert le.echoMode() == QLineEdit.Normal
        le.setEchoMode(QLineEdit.Password)
        assert le.echoMode() == QLineEdit.Password

    def test_maximum_length(self, qtbot):
        from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
        le = VCPLineEdit()
        qtbot.addWidget(le)
        assert le.maxLength() == 32767
        le.setMaxLength(100)
        assert le.maxLength() == 100
