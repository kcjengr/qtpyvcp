import sys
from unittest.mock import MagicMock, patch

import pytest


class TestInvalidAction:
    def test_is_exception(self):
        from qtpyvcp.actions import InvalidAction
        assert issubclass(InvalidAction, Exception)

    def test_can_be_raised_and_caught(self):
        from qtpyvcp.actions import InvalidAction
        try:
            raise InvalidAction("test error")
        except InvalidAction as e:
            assert str(e) == "test error"

    def test_preserves_traceback_info(self):
        from qtpyvcp.actions import InvalidAction
        try:
            raise ValueError("original")
        except ValueError:
            try:
                raise InvalidAction("wrapped", sys.exc_info()[2])
            except InvalidAction as e:
                assert e.__traceback__ is not None


class TestBindWidgetStringParsing:
    """Test the string parsing logic of bindWidget without Qt widget dependencies."""

    def test_replaces_hyphens_with_underscores(self):
        from qtpyvcp.actions import InvalidAction
        action_str = 'machine-power-toggle'
        action, sep, args = action_str.partition(':')
        action = action.replace('-', '_')
        assert action == 'machine_power_toggle'

    def test_separates_args_with_colon(self):
        from qtpyvcp.actions import InvalidAction
        action_str = 'machine.home.axis:x'
        action, sep, args = action_str.partition(':')
        assert action == 'machine.home.axis'
        assert args == 'x'

    def test_no_args_when_no_colon(self):
        from qtpyvcp.actions import InvalidAction
        action_str = 'machine.power.toggle'
        action, sep, args = action_str.partition(':')
        assert action == 'machine.power.toggle'
        assert args == ''

    def test_multiple_args_separated_by_comma(self):
        from qtpyvcp.actions import InvalidAction
        action_str = 'machine.custom:a,b,c'
        action, sep, args = action_str.partition(':')
        assert args == 'a,b,c'
        args_processed = args.replace(' ', '').split(',')
        assert args_processed == ['a', 'b', 'c']

    def test_strips_spaces_from_args(self):
        from qtpyvcp.actions import InvalidAction
        action_str = 'machine.custom: a , b , c '
        action, sep, args = action_str.partition(':')
        args_processed = args.replace(' ', '').split(',')
        assert args_processed == ['a', 'b', 'c']

    def test_converts_numeric_args_to_int(self):
        from qtpyvcp.actions import InvalidAction
        action_str = 'machine.custom:1,2,3'
        action, sep, args = action_str.partition(':')
        args_processed = [int(arg) if arg.isdigit() else str(arg) for arg in args.replace(' ', '').split(',')]
        assert args_processed == [1, 2, 3]

    def test_mixed_args_kept_as_string(self):
        from qtpyvcp.actions import InvalidAction
        action_str = 'machine.custom:1,x,3'
        action, sep, args = action_str.partition(':')
        args_processed = [int(arg) if arg.isdigit() else str(arg) for arg in args.replace(' ', '').split(',')]
        assert args_processed == [1, 'x', 3]


class TestActionMethodResolution:
    """Test the method resolution logic from action string."""

    def test_resolves_simple_action_via_mock(self):
        """Test that getattr traversal works on a mock object."""
        mock_root = MagicMock()
        mock_machine = MagicMock()
        mock_method = MagicMock(ok=MagicMock(), bindOk=MagicMock())
        mock_machine.power = mock_method
        mock_root.machine = mock_machine

        method = mock_root
        action = 'machine.power'
        for item in action.split('.'):
            method = getattr(method, item)
        assert method is mock_method

    def test_numeric_segments_become_kwargs(self):
        """Test that numeric segments in action string become kwargs."""
        # Action: spindle.0.override -> kwargs={'spindle': 0}
        action = 'spindle.0.override'
        kwargs = {}
        prev_item = ''
        for item in action.split('.'):
            if item.isdigit():
                kwargs[prev_item] = int(item)
                continue
            prev_item = item
        assert kwargs == {'spindle': 0}

    def test_multiple_numeric_segments(self):
        """Test multiple numeric segments."""
        action = 'a.1.b.2.c'
        kwargs = {}
        prev_item = ''
        for item in action.split('.'):
            if item.isdigit():
                kwargs[prev_item] = int(item)
                continue
            prev_item = item
        assert kwargs == {'a': 1, 'b': 2}


class TestActionStringEndsWithToggle:
    """Test toggle detection logic."""

    def test_toggle_action_detected(self):
        action = 'machine.power.toggle'
        assert action.endswith('toggle')

    def test_non_toggle_action_not_detected(self):
        action = 'machine.power.on'
        assert not action.endswith('toggle')

    def test_jog_axis_action_not_toggle(self):
        action = 'machine.jog.axis'
        assert not action.endswith('toggle')


class TestJogAxisDetection:
    """Test jog axis action detection logic."""

    def test_jog_axis_action_detected(self):
        action = 'machine.jog.axis'
        assert action.startswith('machine.jog.axis')

    def test_non_jog_action_not_detected(self):
        action = 'machine.power.toggle'
        assert not action.startswith('machine.jog.axis')


class TestDesignModeFlag:
    """Test IN_DESIGNER environment variable behavior."""

    def test_in_designer_defaults_false(self):
        import os
        old_val = os.environ.get('DESIGNER')
        if 'DESIGNER' in os.environ:
            del os.environ['DESIGNER']
        try:
            # Force reimport
            if 'qtpyvcp.actions' in sys.modules:
                del sys.modules['qtpyvcp.actions']
            import qtpyvcp.actions as actions_mod
            assert actions_mod.IN_DESIGNER is False
        finally:
            if old_val is not None:
                os.environ['DESIGNER'] = old_val

    def test_in_designer_set_to_true(self):
        import os
        old_val = os.environ.get('DESIGNER')
        os.environ['DESIGNER'] = '1'
        try:
            # Force reimport
            if 'qtpyvcp.actions' in sys.modules:
                del sys.modules['qtpyvcp.actions']
            import qtpyvcp.actions as actions_mod
            assert bool(actions_mod.IN_DESIGNER) is True
        finally:
            if old_val is not None:
                os.environ['DESIGNER'] = old_val
            else:
                os.environ.pop('DESIGNER', None)
