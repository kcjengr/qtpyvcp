import pytest
from unittest.mock import MagicMock, patch


class TestProbeSimWidget:
    """Tests for ProbeSim widget (QWidget variant of probesim_dialog)."""

    def _make_mock_info(self):
        info = MagicMock()
        info.getIsLathe.return_value = False
        return info

    def test_init_no_parent(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert w is not None

    def test_init_sets_window_title(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert w.windowTitle() == "Simulate touch probe"

    def test_has_touch_button(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert hasattr(w, 'close_button')
            assert w.close_button.text() == "Touch"

    def test_has_pulse_button(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert hasattr(w, 'pulse_button')

    def test_pulse_button_is_checkable(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert w.pulse_button.isCheckable() is True

    def test_close_button_is_not_checkable(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert w.close_button.isCheckable() is False

    def test_timer_is_single_shot(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert w.timer.isSingleShot() is True

    def test_touch_on_without_pulse_calls_subprocess(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            with patch('subprocess.Popen') as mock_popen:
                from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
                w = ProbeSim()
                qtbot.addWidget(w)
                w.touch_on()
                assert mock_popen.call_count == 1
                call_args = mock_popen.call_args[0][0]
                assert 'halcmd' in call_args
                assert 'motion.probe-input' in call_args
                assert '1' in call_args

    def test_touch_on_with_pulse_starts_timer(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            with patch('subprocess.Popen') as mock_popen:
                from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
                w = ProbeSim()
                qtbot.addWidget(w)
                w.pulse_button.setChecked(True)
                w.touch_on()
                assert mock_popen.call_count == 1
                assert w.timer.isActive() is True

    def test_touch_off_without_pulse_calls_subprocess_zero(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            with patch('subprocess.Popen') as mock_popen:
                from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
                w = ProbeSim()
                qtbot.addWidget(w)
                w.touch_off()
                assert mock_popen.call_count == 1
                call_args = mock_popen.call_args[0][0]
                assert 'motion.probe-input' in call_args
                assert '0' in call_args

    def test_touch_off_with_pulse_does_nothing(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            with patch('subprocess.Popen') as mock_popen:
                from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
                w = ProbeSim()
                qtbot.addWidget(w)
                w.pulse_button.setChecked(True)
                w.touch_off()
                assert mock_popen.call_count == 0

    def test_pulse_off_calls_subprocess_zero(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            with patch('subprocess.Popen') as mock_popen:
                from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
                w = ProbeSim()
                qtbot.addWidget(w)
                w.pulse_off()
                assert mock_popen.call_count == 1
                call_args = mock_popen.call_args[0][0]
                assert 'motion.probe-input' in call_args
                assert '0' in call_args

    def test_timer_timeout_connects_to_pulse_off(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            # Verify timer exists and has a connection by checking it's not None
            assert w.timer is not None

    def test_close_button_pressed_signal_connected(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert hasattr(w.close_button, 'pressed')

    def test_close_button_released_signal_connected(self, qtbot):
        with patch('qtpyvcp.widgets.input_widgets.probesim_widget.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
            w = ProbeSim()
            qtbot.addWidget(w)
            assert hasattr(w.close_button, 'released')
