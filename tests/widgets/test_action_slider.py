import pytest
from unittest.mock import MagicMock, patch


class TestActionSlider:
    """Tests for ActionSlider widget."""

    def test_init_no_parent(self, qtbot):
        from qtpy.QtWidgets import QSlider
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        assert isinstance(s, QSlider)

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        parent = QWidget()
        s = ActionSlider(parent)
        qtbot.addWidget(s)
        assert s.parent() is parent

    def test_actionName_property_getter_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        assert s.actionName == ''

    @patch('qtpyvcp.widgets.input_widgets.action_slider.bindWidget')
    def test_actionName_setter_calls_bindWidget(self, mock_bind, qtbot):
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        s.actionName = 'machine.jog.x.positive'
        assert s._action_name == 'machine.jog.x.positive'
        mock_bind.assert_called_once_with(s, 'machine.jog.x.positive')

    def test_actionName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        meta_obj = s.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'actionName' in prop_names

    def test_orientation_default(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        assert s.orientation() == Qt.Orientation.Vertical

    def test_set_orientation_horizontal(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        s.setOrientation(Qt.Orientation.Horizontal)
        assert s.orientation() == Qt.Orientation.Horizontal

    def test_set_orientation_vertical(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        s.setOrientation(Qt.Orientation.Vertical)
        assert s.orientation() == Qt.Orientation.Vertical

    def test_value_range(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        s.setOrientation(Qt.Orientation.Horizontal)
        s.setMinimum(0)
        s.setMaximum(100)
        s.setValue(50)
        assert s.minimum() == 0
        assert s.maximum() == 100
        assert s.value() == 50

    def test_mouseDoubleClickEvent_sets_value_to_100(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QMouseEvent
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        s.setMinimum(0)
        s.setMaximum(100)
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            s.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        s.mouseDoubleClickEvent(event)
        assert s.value() == 100

    def test_mouseDoubleClickEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QMouseEvent
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        initial_value = s.value()
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            s.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        s.mouseDoubleClickEvent(event)
        assert s.value() == initial_value
        assert event.isAccepted() is True

    def test_mousePressEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QMouseEvent
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            s.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        s.mousePressEvent(event)
        assert event.isAccepted() is True

    def test_mouseReleaseEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QMouseEvent
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            s.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        s.mouseReleaseEvent(event)
        assert event.isAccepted() is True

    def test_keyPressEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Up,
            Qt.NoModifier
        )
        s.keyPressEvent(event)
        assert event.isAccepted() is True

    def test_keyReleaseEvent_locked(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
        s = ActionSlider()
        qtbot.addWidget(s)
        
        from qtpyvcp.plugins import _PLUGINS
        _PLUGINS['status'].isLocked.return_value = True
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyRelease,
            Qt.Key_Up,
            Qt.NoModifier
        )
        s.keyReleaseEvent(event)
        assert event.isAccepted() is True
