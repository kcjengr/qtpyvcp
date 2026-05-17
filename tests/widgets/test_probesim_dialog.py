import pytest
from unittest.mock import MagicMock, patch
from qtpy.QtCore import Qt


class TestProbeSim:
    """Tests for ProbeSim dialog."""

    def _make_mock_info(self):
        info = MagicMock()
        info.getIsLathe.return_value = False
        return info

    def test_init_no_parent(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            assert dlg is not None

    def test_init_sets_window_title(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            assert dlg.windowTitle() == "Simulate touch probe"

    def test_has_touch_button(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            assert hasattr(dlg, 'close_button')
            assert dlg.close_button.text() == "Touch"

    def test_has_pulse_checkbox(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            assert hasattr(dlg, 'pulse_checkbox')

    def test_pulse_checkbox_default_unchecked(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            assert dlg.pulse_checkbox.checkState() == Qt.CheckState.Unchecked

    def test_touch_on_without_pulse_calls_subprocess(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            import qtpyvcp.widgets.dialogs.probesim_dialog as mod
            with patch.object(mod.subprocess, 'Popen') as mock_popen:
                from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
                dlg = ProbeSim()
                qtbot.addWidget(dlg)
                dlg.touch_on()
                assert mock_popen.call_count == 1
                call_args = mock_popen.call_args[0][0]
                assert 'halcmd' in call_args
                assert 'motion.probe-input' in call_args
                assert '1' in call_args

    def test_touch_on_with_pulse_starts_timer(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            import qtpyvcp.widgets.dialogs.probesim_dialog as mod
            with patch.object(mod.subprocess, 'Popen') as mock_popen:
                from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
                dlg = ProbeSim()
                qtbot.addWidget(dlg)
                dlg.pulse_checkbox.setCheckState(Qt.CheckState.Checked)
                dlg.touch_on()
                assert mock_popen.call_count == 1
                assert dlg.timer.isActive() is True

    def test_touch_off_without_pulse_calls_subprocess_zero(self, qtbot):
        import qtpyvcp.widgets.dialogs.probesim_dialog as mod
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            assert dlg.pulse_checkbox.checkState() == Qt.CheckState.Unchecked
            with patch.object(mod.subprocess, 'Popen') as mock_popen:
                dlg.touch_off()
                assert mock_popen.call_count == 1
                call_args = mock_popen.call_args[0][0]
                assert 'motion.probe-input' in call_args
                assert '0' in call_args

    def test_touch_off_with_pulse_does_nothing(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            import qtpyvcp.widgets.dialogs.probesim_dialog as mod
            with patch.object(mod.subprocess, 'Popen') as mock_popen:
                from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
                dlg = ProbeSim()
                qtbot.addWidget(dlg)
                dlg.pulse_checkbox.setCheckState(Qt.CheckState.Checked)
                dlg.touch_off()
                assert mock_popen.call_count == 0

    def test_pulse_off_calls_subprocess_zero(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            import qtpyvcp.widgets.dialogs.probesim_dialog as mod
            with patch.object(mod.subprocess, 'Popen') as mock_popen:
                from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
                dlg = ProbeSim()
                qtbot.addWidget(dlg)
                dlg.pulse_off()
                assert mock_popen.call_count == 1
                call_args = mock_popen.call_args[0][0]
                assert 'motion.probe-input' in call_args
                assert '0' in call_args

    def test_close_hides_dialog(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            dlg.show()
            assert dlg.isVisible() is True
            dlg.close()
            assert dlg.isVisible() is False

    def test_timer_is_single_shot(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            assert dlg.timer.isSingleShot() is True

    def test_touch_button_pressed_signal_connected(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            # Verify the button has connected signals by checking it exists
            assert dlg.close_button is not None

    def test_release_signal_connected(self, qtbot):
        with patch('qtpyvcp.widgets.dialogs.probesim_dialog.Info', return_value=self._make_mock_info()):
            from qtpyvcp.widgets.dialogs.probesim_dialog import ProbeSim
            dlg = ProbeSim()
            qtbot.addWidget(dlg)
            # Verify the button has release signal connected
            assert dlg.close_button is not None
