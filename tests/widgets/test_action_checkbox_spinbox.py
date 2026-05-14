import pytest
from unittest.mock import MagicMock, patch


class TestActionCheckBox:
    """Tests for ActionCheckBox widget."""

    def test_init_no_parent(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        assert cb is not None

    def test_init_is_checkbox(self, qtbot):
        from qtpy.QtWidgets import QCheckBox
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        assert isinstance(cb, QCheckBox)

    def test_init_no_focus_policy(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        assert cb.focusPolicy() == Qt.NoFocus

    def test_init_with_action_none(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox(action=None)
        qtbot.addWidget(cb)
        assert cb._action_name == ''

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        parent = QWidget()
        cb = ActionCheckBox(parent)
        qtbot.addWidget(cb)
        assert cb.parent() is parent

    def test_actionName_property_getter_default(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        assert cb.actionName == ''

    @patch('qtpyvcp.widgets.button_widgets.action_checkbox.bindWidget')
    def test_actionName_setter_calls_bindWidget(self, mock_bind, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        cb.actionName = 'machine.power.toggle'
        assert cb._action_name == 'machine.power.toggle'
        mock_bind.assert_called_once_with(cb, 'machine.power.toggle')

    @patch('qtpyvcp.widgets.button_widgets.action_checkbox.bindWidget')
    def test_init_with_action_sets_action_name(self, mock_bind, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox(action='test.action')
        qtbot.addWidget(cb)
        assert cb._action_name == 'test.action'
        mock_bind.assert_called_once_with(cb, 'test.action')

    def test_checked_default(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        assert cb.isChecked() is False

    def test_set_checked(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        cb.setChecked(True)
        assert cb.isChecked() is True
        cb.setChecked(False)
        assert cb.isChecked() is False

    def test_actionName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        meta_obj = cb.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'actionName' in prop_names

    def test_toggled_signal(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        toggled_values = []
        cb.toggled.connect(lambda v: toggled_values.append(v))
        cb.setChecked(True)
        assert True in toggled_values
        cb.setChecked(False)
        assert False in toggled_values

    def test_text_get_set(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox
        cb = ActionCheckBox()
        qtbot.addWidget(cb)
        cb.setText('Toggle Me')
        assert cb.text() == 'Toggle Me'


class TestActionSpinBox:
    """Tests for ActionSpinBox widget."""

    def test_init_no_parent(self, qtbot):
        from qtpy.QtWidgets import QSpinBox
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        assert isinstance(sb, QSpinBox)

    def test_init_default_value(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        assert sb.value() == 0

    def test_init_with_action_none(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox(action=None)
        qtbot.addWidget(sb)
        assert sb._action_name == ''

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        parent = QWidget()
        sb = ActionSpinBox(parent)
        qtbot.addWidget(sb)
        assert sb.parent() is parent

    def test_actionName_property_getter_default(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        assert sb.actionName == ''

    @patch('qtpyvcp.widgets.button_widgets.action_spinbox.bindWidget')
    def test_actionName_setter_calls_bindWidget(self, mock_bind, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        sb.actionName = 'spindle.0.override'
        assert sb._action_name == 'spindle.0.override'
        mock_bind.assert_called_once_with(sb, 'spindle.0.override')

    @patch('qtpyvcp.widgets.button_widgets.action_spinbox.bindWidget')
    def test_init_with_action_sets_action_name(self, mock_bind, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox(action='spindle.1.override')
        qtbot.addWidget(sb)
        assert sb._action_name == 'spindle.1.override'
        mock_bind.assert_called_once_with(sb, 'spindle.1.override')

    def test_set_value(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        sb.setValue(42)
        assert sb.value() == 42

    def test_set_range(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        sb.setRange(0, 100)
        assert sb.minimum() == 0
        assert sb.maximum() == 100

    def test_actionName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        meta_obj = sb.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'actionName' in prop_names

    def test_valueChanged_signal(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        values_received = []
        sb.valueChanged.connect(lambda v: values_received.append(v))
        sb.setValue(10)
        assert 10 in values_received

    def test_step(self, qtbot):
        from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox
        sb = ActionSpinBox()
        qtbot.addWidget(sb)
        assert sb.singleStep() == 1
        sb.setSingleStep(5)
        assert sb.singleStep() == 5
