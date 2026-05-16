import pytest
from unittest.mock import MagicMock, patch


class TestToolChangeDialog:
    """Tests for ToolChangeDialog."""

    def _make_mock_hal_component(self):
        comp = MagicMock()
        comp.addPin.return_value = MagicMock()
        return comp

    def _make_mock_tooltable(self):
        tt = MagicMock()
        tt.getToolTable.return_value = {
            1: {'R': 'R1.5'},
            2: {'R': 'R2.0'},
        }
        return tt

    def _get_patched_halt(self):
        mock_hal_comp = self._make_mock_hal_component()
        mock_tt = self._make_mock_tooltable()
        return (
            patch('qtpyvcp.widgets.dialogs.toolchange_dialog.hal.getComponent', return_value=mock_hal_comp),
            patch('qtpyvcp.widgets.dialogs.toolchange_dialog.getPlugin', return_value=mock_tt),
        )

    def test_init_no_parent(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert dlg is not None

    def test_init_sets_window_title(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert dlg.windowTitle() == "Manual Tool Change"

    def test_init_has_tool_number_label(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert hasattr(dlg.ui, 'lblToolNumber')

    def test_init_has_tool_remark_label(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert hasattr(dlg.ui, 'lblToolRemark')

    def test_init_has_done_button(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert hasattr(dlg.ui, 'btnDone')

    def test_init_hides_dialog(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert dlg.isVisible() is False

    def test_init_stores_tool_number_zero(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert dlg.tool_number == 0

    def test_init_adds_hal_pins(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        mock_comp = self._make_mock_hal_component()
        with patch('qtpyvcp.widgets.dialogs.toolchange_dialog.hal.getComponent', return_value=mock_comp), \
             tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert mock_comp.addPin.call_count == 4

    def test_init_adds_listeners(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        mock_comp = self._make_mock_hal_component()
        with patch('qtpyvcp.widgets.dialogs.toolchange_dialog.hal.getComponent', return_value=mock_comp), \
             tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert mock_comp.addListener.call_count == 3

    def test_prepare_tool_updates_number_label(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.prepare_tool(5)
            assert dlg.ui.lblToolNumber.text() == "5"

    def test_prepare_tool_updates_remark_label(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.prepare_tool(1)
            assert dlg.ui.lblToolRemark.text() == "R1.5"

    def test_prepare_tool_skips_same_number(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.prepare_tool(3)
            dlg.ui.lblToolNumber.setText("CHANGED")
            dlg.prepare_tool(3)
            assert dlg.ui.lblToolNumber.text() == "CHANGED"

    def test_prepare_tool_missing_tool_data(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        mock_tt = MagicMock()
        mock_tt.getToolTable.return_value = {}
        with hal_patch, patch('qtpyvcp.widgets.dialogs.toolchange_dialog.getPlugin', return_value=mock_tt):
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.prepare_tool(99)
            assert dlg.ui.lblToolRemark.text() == "UNKNOWN"

    def test_on_change_shows_dialog(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.on_change(True)
            assert dlg.isVisible() is True

    def test_on_change_does_not_show_if_false(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.show()
            dlg.isVisible()
            dlg.on_change(False)
            assert dlg.isVisible() is True

    def test_on_change_button_calls_accept(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.accept = MagicMock()
            dlg.on_change_button(True)
            dlg.accept.assert_called_once()

    def test_on_change_button_noop_if_false(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.accept = MagicMock()
            dlg.on_change_button(False)
            dlg.accept.assert_not_called()

    def test_reject_is_noop(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.show()
            assert dlg.isVisible() is True
            dlg.reject()
            assert dlg.isVisible() is True

    def test_accept_sets_changed_pin(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        mock_comp = self._make_mock_hal_component()
        with patch('qtpyvcp.widgets.dialogs.toolchange_dialog.hal.getComponent', return_value=mock_comp), \
             tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.changed_pin.value = False
            dlg.accept()
            assert dlg.changed_pin.value is True

    def test_timerEvent_hides_when_not_visible(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        mock_comp = self._make_mock_hal_component()
        with patch('qtpyvcp.widgets.dialogs.toolchange_dialog.hal.getComponent', return_value=mock_comp), \
             tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.changed_pin.value = True
            dlg.change_pin.value = False
            dlg.timerEvent(None)
            assert dlg.isVisible() is False
            assert dlg.changed_pin.value is False

    def test_timerEvent_hides_visible_dialog(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        mock_comp = self._make_mock_hal_component()
        with patch('qtpyvcp.widgets.dialogs.toolchange_dialog.hal.getComponent', return_value=mock_comp), \
             tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            dlg.show()
            dlg.change_pin.value = False
            dlg.timerEvent(None)
            assert dlg.isVisible() is False

    def test_ui_file_attribute_default(self, qtbot):
        hal_patch, tt_patch = self._get_patched_halt()
        with hal_patch, tt_patch:
            from qtpyvcp.widgets.dialogs.toolchange_dialog import ToolChangeDialog
            dlg = ToolChangeDialog()
            qtbot.addWidget(dlg)
            assert dlg.ui_file.endswith("toolchange_dialog.ui")
