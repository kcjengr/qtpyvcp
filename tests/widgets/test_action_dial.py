import pytest
from unittest.mock import MagicMock, patch


class TestActionDial:
    """Tests for ActionDial widget."""

    def test_init_no_parent(self, qtbot):
        from qtpy.QtWidgets import QDial
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        assert isinstance(d, QDial)

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        parent = QWidget()
        d = ActionDial(parent)
        qtbot.addWidget(d)
        assert d.parent() is parent

    def test_actionName_property_getter_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        assert d.actionName == ''

    @patch('qtpyvcp.widgets.input_widgets.action_dial.bindWidget')
    def test_actionName_setter_calls_bindWidget(self, mock_bind, qtbot):
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        d.actionName = 'machine.jog.x.positive'
        assert d._action_name == 'machine.jog.x.positive'
        mock_bind.assert_called_once_with(d, 'machine.jog.x.positive')

    def test_actionName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        meta_obj = d.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'actionName' in prop_names

    def test_value_range(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        d.setMinimum(0)
        d.setMaximum(255)
        d.setValue(128)
        assert d.minimum() == 0
        assert d.maximum() == 255
        assert d.value() == 128

    def test_mousePressEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QMouseEvent
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            d.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        d.mousePressEvent(event)
        assert event.isAccepted() is True

    def test_mouseReleaseEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QMouseEvent
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            d.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        d.mouseReleaseEvent(event)
        assert event.isAccepted() is True

    def test_keyPressEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Up,
            Qt.NoModifier
        )
        d.keyPressEvent(event)
        assert event.isAccepted() is True

    def test_keyReleaseEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
        d = ActionDial()
        qtbot.addWidget(d)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyRelease,
            Qt.Key_Up,
            Qt.NoModifier
        )
        d.keyReleaseEvent(event)
        assert event.isAccepted() is True
