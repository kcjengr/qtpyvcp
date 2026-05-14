import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from qtpy.QtWidgets import QPushButton, QApplication, QWidget


class TestActionButtonBase:
    """Tests for VCPButton base class (inherited by ActionButton)."""

    def test_vcpbutton_is_pushbutton(self, qtbot):
        from qtpyvcp.widgets.base_widgets.base_widget import VCPButton
        btn = VCPButton()
        qtbot.addWidget(btn)
        assert isinstance(btn, QPushButton)

    def test_vcpbutton_no_focus_policy(self, qtbot):
        from qtpyvcp.widgets.base_widgets.base_widget import VCPButton
        btn = VCPButton()
        qtbot.addWidget(btn)
        from qtpy.QtCore import Qt
        assert btn.focusPolicy() == Qt.NoFocus

    def test_vcpbutton_rule_properties_contains_text(self):
        from qtpyvcp.widgets.base_widgets.base_widget import VCPButton
        assert 'Text' in VCPButton.RULE_PROPERTIES
        assert VCPButton.RULE_PROPERTIES['Text'] == ['setText', str]

    def test_vcpbutton_rule_properties_contains_checked(self):
        from qtpyvcp.widgets.base_widgets.base_widget import VCPButton
        assert 'Checked' in VCPButton.RULE_PROPERTIES
        assert VCPButton.RULE_PROPERTIES['Checked'] == ['setChecked', bool]

    def test_vcpbutton_default_enable_rule_property(self):
        from qtpyvcp.widgets.base_widgets.base_widget import VCPButton
        assert VCPButton.DEFAULT_RULE_PROPERTY == 'Enable'


class TestActionButton:
    """Tests for ActionButton widget."""

    def test_init_no_parent_no_action(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton()
        qtbot.addWidget(btn)
        assert btn._action_name == ''

    def test_init_with_parent(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        parent = QWidget()
        btn = ActionButton(parent)
        qtbot.addWidget(btn)
        assert btn.parent() is parent

    def test_init_with_action_none(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton(action=None)
        qtbot.addWidget(btn)
        assert btn._action_name == ''

    def test_init_is_actionbutton_and_pushbutton(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton()
        qtbot.addWidget(btn)
        assert isinstance(btn, ActionButton)
        assert isinstance(btn, QPushButton)

    def test_actionName_property_getter_default(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton()
        qtbot.addWidget(btn)
        assert btn.actionName == ''

    @patch('qtpyvcp.widgets.button_widgets.action_button.bindWidget')
    def test_actionName_setter_calls_bindWidget(self, mock_bind, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton()
        qtbot.addWidget(btn)
        btn.actionName = 'machine.power.toggle'
        assert btn._action_name == 'machine.power.toggle'
        mock_bind.assert_called_once_with(btn, 'machine.power.toggle')

    @patch('qtpyvcp.widgets.button_widgets.action_button.bindWidget')
    def test_init_with_action_sets_action_name(self, mock_bind, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton(action='test.action')
        qtbot.addWidget(btn)
        assert btn._action_name == 'test.action'
        mock_bind.assert_called_once_with(btn, 'test.action')

    def test_init_with_invalid_action_passes(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        from qtpyvcp.actions import InvalidAction
        with patch('qtpyvcp.widgets.button_widgets.action_button.bindWidget', side_effect=InvalidAction()):
            btn = ActionButton(action='nonexistent.action')
            qtbot.addWidget(btn)
            assert btn._action_name == 'nonexistent.action'

    def test_actionName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton()
        qtbot.addWidget(btn)
        meta_obj = btn.metaObject()
        prop_count = meta_obj.propertyCount()
        prop_names = [meta_obj.property(i).name() for i in range(prop_count)]
        assert 'actionName' in prop_names

    def test_click_signal(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton()
        qtbot.addWidget(btn)
        clicked_fired = []
        btn.clicked.connect(lambda: clicked_fired.append(True))
        btn.click()
        assert len(clicked_fired) == 1

    def test_set_text(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = ActionButton()
        qtbot.addWidget(btn)
        btn.setText('Hello')
        assert btn.text() == 'Hello'

    def test_set_icon(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        from qtpy.QtGui import QIcon
        btn = ActionButton()
        qtbot.addWidget(btn)
        icon = QIcon()
        btn.setIcon(icon)
        assert btn.icon().name() == icon.name()
