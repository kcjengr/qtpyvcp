import os
import sys
import importlib
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_action_modules():
    """Inject minimal mock action submodules into qtpyvcp.actions namespace."""
    from qtpyvcp import actions

    # Create mock submodule objects
    # Methods need .ok and .bindOk attributes (like real actions do)
    _mock_toggle = MagicMock()
    _mock_toggle.ok = MagicMock(return_value=None)
    _mock_toggle.bindOk = MagicMock(return_value=None)

    _mock_home_axis = MagicMock()
    _mock_home_axis.ok = MagicMock(return_value=None)
    _mock_home_axis.bindOk = MagicMock(return_value=None)

    _mock_home_all = MagicMock()
    _mock_home_all.ok = MagicMock(return_value=None)
    _mock_home_all.bindOk = MagicMock(return_value=None)

    _mock_jog_axis = MagicMock()
    _mock_jog_axis.ok = MagicMock(return_value=None)
    _mock_jog_axis.bindOk = MagicMock(return_value=None)

    # power is a non-callable container with toggle method (simulates real action class)
    _power_container = type('_PowerContainer', (), {
        'toggle': _mock_toggle,
        'ok': MagicMock(return_value=None),
        'bindOk': MagicMock(return_value=None),
    })()

    mock_machine = MagicMock(spec=['power', 'home', 'jog', 'my_action'])
    mock_machine.power = _power_container  # non-callable for test_non_callable_raises
    mock_machine.home = MagicMock(spec=['axis', 'all'])
    mock_machine.home.axis = _mock_home_axis
    mock_machine.home.all = _mock_home_all
    mock_machine.jog = MagicMock(spec=['axis'])
    mock_machine.jog.axis = _mock_jog_axis

    _mock_override = MagicMock()
    _mock_override.ok = MagicMock(return_value=None)
    _mock_override.bindOk = MagicMock(return_value=None)

    _mock_something = MagicMock()
    _mock_something.ok = MagicMock(return_value=None)
    _mock_something.bindOk = MagicMock(return_value=None)

    mock_spindle = MagicMock(spec=['override', 'something'])
    mock_spindle.override = _mock_override
    mock_spindle.something = _mock_something

    mock_coolant = MagicMock(spec=['ok', 'bindOk'])
    mock_coolant.ok = MagicMock(return_value=None)
    mock_coolant.bindOk = MagicMock(return_value=None)

    mock_tool = MagicMock(spec=['ok', 'bindOk'])
    mock_tool.ok = MagicMock(return_value=None)
    mock_tool.bindOk = MagicMock(return_value=None)

    mock_program = MagicMock(spec=['ok', 'bindOk'])
    mock_program.ok = MagicMock(return_value=None)
    mock_program.bindOk = MagicMock(return_value=None)

    mock_power = MagicMock(spec=['ok', 'bindOk'])
    mock_power.ok = MagicMock(return_value=None)
    mock_power.bindOk = MagicMock(return_value=None)

    # Replace the submodule references in the actions namespace
    actions.machine = mock_machine
    actions.spindle = mock_spindle
    actions.coolant = mock_coolant
    actions.tool = mock_tool
    actions.program = mock_program
    actions.power = mock_power

    yield

    # Restore original references from submodules
    try:
        from . import machine_actions as _m
        actions.machine = _m
    except Exception:
        pass


class TestInvalidAction:
    """Tests for InvalidAction exception."""

    def test_invalid_action_is_exception(self):
        from qtpyvcp.actions import InvalidAction
        assert issubclass(InvalidAction, Exception)

    def test_invalid_action_raised_with_message(self):
        from qtpyvcp.actions import InvalidAction
        with pytest.raises(InvalidAction) as exc_info:
            raise InvalidAction("test error")
        assert "test error" in str(exc_info.value)


class TestBindWidgetBasic:
    """Tests for bindWidget basic functionality."""

    def test_bind_to_machine_action(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'machine.power.toggle')

    def test_bind_widget_connects_clicked(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'machine.home.axis:x')

        # Trigger the clicked signal
        widget.click()
        from qtpyvcp.actions import machine
        machine.home.axis.assert_called_once_with('x')

    def test_bind_widget_dashes_become_underscores(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'machine.my-action')


class TestBindWidgetWithArgs:
    """Tests for bindWidget with arguments."""

    def test_bind_single_arg(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'machine.home.axis:x')

        widget.click()
        from qtpyvcp.actions import machine
        machine.home.axis.assert_called_once_with('x')

    def test_bind_multiple_args(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'spindle.something:1,2,3')

        widget.click()
        from qtpyvcp.actions import spindle
        spindle.something.assert_called_once_with(1, 2, 3)

    def test_bind_mixed_args(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'spindle.something:1,hello')

        widget.click()
        from qtpyvcp.actions import spindle
        spindle.something.assert_called_once_with(1, 'hello')


class TestBindWidgetJogAxis:
    """Tests for jog axis action binding."""

    def test_jog_axis_pressed(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'machine.jog.axis:x')

        # Manually emit pressed signal (click() doesn't emit pressed in pytest-qt)
        widget.pressed.emit()
        from qtpyvcp.actions import machine
        machine.jog.axis.assert_called_once_with('x')

    def test_jog_axis_released_with_speed_zero(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'machine.jog.axis:x')

        # Manually emit pressed then released signals
        widget.pressed.emit()
        widget.released.emit()
        from qtpyvcp.actions import machine
        calls = machine.jog.axis.call_args_list
        assert len(calls) == 2
        assert calls[0] == (('x',), {})
        assert calls[1] == (('x',), {'speed': 0})


class TestBindWidgetAction:
    """Tests for QAction binding."""

    def test_bind_action_toggle(self, qtbot):
        from qtpy.QtWidgets import QAction
        from qtpyvcp.actions import bindWidget

        action = QAction('Toggle')
        bindWidget(action, 'machine.power.toggle')

        assert action.isCheckable() is True

    def test_bind_action_non_toggle(self, qtbot):
        from qtpy.QtWidgets import QAction
        from qtpyvcp.actions import bindWidget

        action = QAction('Home All')
        bindWidget(action, 'machine.home.all')

        assert action.isCheckable() is False


class TestBindWidgetSlider:
    """Tests for QSlider binding."""

    def test_bind_slider(self, qtbot):
        from qtpy.QtWidgets import QSlider
        from qtpyvcp.actions import bindWidget

        widget = QSlider()
        bindWidget(widget, 'spindle.override')

        widget.setValue(50)
        from qtpyvcp.actions import spindle
        spindle.override.assert_called_once_with(50)


class TestBindWidgetSpinBox:
    """Tests for QSpinBox binding."""

    def test_bind_spinbox(self, qtbot):
        from qtpy.QtWidgets import QSpinBox
        from qtpyvcp.actions import bindWidget

        widget = QSpinBox()
        bindWidget(widget, 'spindle.override')

        widget.setValue(75)
        from qtpyvcp.actions import spindle
        spindle.override.assert_called_once_with(75)


class TestBindWidgetDial:
    """Tests for QDial binding."""

    def test_bind_dial(self, qtbot):
        from qtpy.QtWidgets import QDial
        from qtpyvcp.actions import bindWidget

        widget = QDial()
        bindWidget(widget, 'spindle.override')

        widget.setValue(30)
        from qtpyvcp.actions import spindle
        spindle.override.assert_called_once_with(30)


class TestBindWidgetComboBox:
    """Tests for QComboBox binding."""

    def test_bind_combobox(self, qtbot):
        from qtpy.QtWidgets import QComboBox
        from qtpyvcp.actions import bindWidget

        widget = QComboBox()
        widget.addItem('x')
        widget.addItem('y')
        bindWidget(widget, 'machine.home.axis')

        # Manually emit the int signal that bindWidget connected to (index 0 = 'x')
        widget.activated[int].emit(0)
        from qtpyvcp.actions import machine
        machine.home.axis.assert_called_once_with(0)


class TestBindWidgetErrors:
    """Tests for bindWidget error handling."""

    def test_invalid_action_raises(self, mock_action_modules, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget, InvalidAction
        import qtpyvcp.actions as actions_module

        original_designer = os.environ.get('DESIGNER')
        try:
            os.environ.pop('DESIGNER', None)
            # Re-import to pick up the changed env var
            importlib.reload(actions_module)
            from qtpyvcp.actions import bindWidget as bw, InvalidAction as IA

            widget = QPushButton()
            with pytest.raises(IA) as exc_info:
                bw(widget, 'nonexistent.action')
            assert "Could not get action method" in str(exc_info.value)
        finally:
            if original_designer is not None:
                os.environ['DESIGNER'] = original_designer

    def test_non_callable_raises(self, mock_action_modules, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget, InvalidAction
        import qtpyvcp.actions as actions_module

        original_designer = os.environ.get('DESIGNER')
        try:
            os.environ.pop('DESIGNER', None)
            importlib.reload(actions_module)
            from qtpyvcp.actions import bindWidget as bw, InvalidAction as IA

            widget = QPushButton()
            with pytest.raises(IA):
                bw(widget, 'machine.power')
        finally:
            if original_designer is not None:
                os.environ['DESIGNER'] = original_designer

    def test_unsupported_widget_type_raises(self, qtbot):
        from qtpy.QtWidgets import QLabel
        from qtpyvcp.actions import bindWidget, InvalidAction

        widget = QLabel()
        with pytest.raises(InvalidAction) as exc_info:
            bindWidget(widget, 'machine.power.toggle')
        assert "unsupported widget type" in str(exc_info.value)
        assert "QLabel" in str(exc_info.value)


class TestBindWidgetDesignerMode:
    """Tests for bindWidget behavior in Designer mode."""

    def test_designer_mode_returns_early_on_invalid_action(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget
        import qtpyvcp.actions as actions_module

        widget = QPushButton()
        original = actions_module.IN_DESIGNER
        try:
            actions_module.IN_DESIGNER = True
            result = bindWidget(widget, 'nonexistent.action')
            assert result is None
        finally:
            actions_module.IN_DESIGNER = original


class TestBindWidgetOkState:
    """Tests for OK state checking during binding."""

    def test_ok_method_called(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget
        import qtpyvcp.actions as actions_module

        widget = QPushButton()
        bindWidget(widget, 'machine.power.toggle')

        # method.ok/bindOk are called on the method object (toggle), not power container
        toggle = actions_module.machine.power.toggle
        toggle.ok.assert_called_once()
        toggle.bindOk.assert_called_once()


class TestBindWidgetKwargs:
    """Tests for keyword argument binding."""

    def test_numeric_segment_becomes_kwarg(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'spindle.0.something')

        widget.click()
        from qtpyvcp.actions import spindle
        spindle.something.assert_called_once_with(spindle=0)


class TestBindWidgetWithIntKwargs:
    """Tests for numeric kwarg binding."""

    def test_numeric_segment_becomes_kwarg(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.actions import bindWidget

        widget = QPushButton()
        bindWidget(widget, 'spindle.0.override')

        widget.click()
        from qtpyvcp.actions import spindle
        spindle.override.assert_called_once_with(spindle=0)


class TestBindWidgetActionTriggered:
    """Tests for QAction triggered signal binding."""

    def test_action_triggered_calls_method(self, qtbot):
        from qtpy.QtWidgets import QAction
        from qtpyvcp.actions import bindWidget

        action = QAction('Toggle')
        bindWidget(action, 'machine.home.all')

        action.trigger()
        from qtpyvcp.actions import machine
        machine.home.all.assert_called_once()
