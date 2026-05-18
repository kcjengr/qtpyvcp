import pytest
from unittest.mock import MagicMock, patch


class TestActionComboBox:
    """Tests for ActionComboBox widget."""

    def test_init_no_parent(self, qtbot):
        from qtpy.QtWidgets import QComboBox
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        assert isinstance(cb, QComboBox)

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        parent = QWidget()
        cb = ActionComboBox(parent)
        qtbot.addWidget(cb)
        assert cb.parent() is parent

    def test_actionName_property_getter_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        assert cb.actionName == ''

    @patch('qtpyvcp.widgets.input_widgets.action_combobox.bindWidget')
    def test_actionName_setter_calls_bindWidget(self, mock_bind, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        cb.actionName = 'machine.power.toggle'
        assert cb._action_name == 'machine.power.toggle'
        mock_bind.assert_called_once_with(cb, 'machine.power.toggle')

    def test_actionName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        meta_obj = cb.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'actionName' in prop_names

    def test_add_item(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        cb.addItem('Option 1')
        cb.addItem('Option 2')
        assert cb.count() == 2
        assert cb.itemText(0) == 'Option 1'
        assert cb.itemText(1) == 'Option 2'

    def test_current_index_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        assert cb.currentIndex() == -1

    def test_set_current_index(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        cb.addItem('Option 1')
        cb.setCurrentIndex(0)
        assert cb.currentIndex() == 0

    def test_mousePressEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt, QPoint
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)

        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True

        qtbot.mousePress(cb, Qt.LeftButton, pos=QPoint(cb.rect().center()))

    def test_mouseReleaseEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt, QPoint
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)

        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True

        qtbot.mouseRelease(cb, Qt.LeftButton, pos=QPoint(cb.rect().center()))

    def test_keyPressEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Return,
            Qt.NoModifier
        )
        cb.keyPressEvent(event)
        assert event.isAccepted() is True

    def test_keyReleaseEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyRelease,
            Qt.Key_Return,
            Qt.NoModifier
        )
        cb.keyReleaseEvent(event)
        assert event.isAccepted() is True

    def test_clear(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        cb.addItem('Option 1')
        cb.clear()
        assert cb.count() == 0

    def test_set_enabled(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
        cb = ActionComboBox()
        qtbot.addWidget(cb)
        cb.setEnabled(False)
        assert cb.isEnabled() is False
