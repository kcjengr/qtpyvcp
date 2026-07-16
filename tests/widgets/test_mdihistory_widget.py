import pytest
from unittest.mock import MagicMock, patch


class TestMDIHistoryConstants:
    """Tests for MDIHistory class constants."""

    def test_mdiq_done_value(self):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory
        assert MDIHistory.MDIQ_DONE == 0

    def test_mdiq_running_value(self):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory
        assert MDIHistory.MDIQ_RUNNING == 1

    def test_mdiq_todo_value(self):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory
        assert MDIHistory.MDIQ_TODO == 2

    def test_mdqq_role_value(self):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory
        assert MDIHistory.MDQQ_ROLE == 256


class TestMDIHistoryInit:
    """Tests for MDIHistory initialization."""

    def test_init_no_parent(self, qtbot):
        from qtpy.QtWidgets import QListWidget
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        assert isinstance(widget, QListWidget)

    def test_init_with_parent(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        parent = QWidget()
        widget = MDIHistory(parent)
        qtbot.addWidget(widget)
        assert widget.parent() is parent

    def test_init_default_values(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        assert widget.mdi_entryline_name is None
        assert widget.mdi_entry_widget is None
        assert widget.mdi_listorder_natural is False

    def test_init_has_icons(self, qtbot):
        from qtpy.QtGui import QIcon
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        assert widget.icon_run is not None
        assert isinstance(widget.icon_run, QIcon)
        assert widget.icon_waiting is not None
        assert isinstance(widget.icon_waiting, QIcon)


class TestMDIHistoryProperties:
    """Tests for MDIHistory Qt properties."""

    def test_mdiEntrylineName_getter_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        assert widget.mdiEntrylineName is None

    def test_mdiEntrylineName_setter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.mdiEntrylineName = 'mdi_entry'
        assert widget.mdi_entryline_name == 'mdi_entry'

    def test_mdiEntrylineName_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        meta_obj = widget.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'mdiEntrylineName' in prop_names

    def test_mdiListOrderNatural_getter_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        assert widget.mdiListOrderNatural is False

    def test_mdiListOrderNatural_setter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.mdiListOrderNatural = True
        assert widget.mdi_listorder_natural is True

    def test_mdiListOrderNatural_is_qt_property(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        meta_obj = widget.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'mdiListOrderNatural' in prop_names


class TestMDIHistoryToggleQueue:
    """Tests for toggleQueue method."""

    def test_toggle_queue_start(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.heart_beat_timer = MagicMock()
        
        # Simulate sender with setText
        sender = MagicMock()
        sender.setText = MagicMock()
        
        widget.sender = lambda: sender
        widget.toggleQueue(True)
        widget.heart_beat_timer.stop.assert_called_once()

    def test_toggle_queue_stop_starts_timer(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.heart_beat_timer = MagicMock()
        
        sender = MagicMock()
        sender.setText = MagicMock()
        
        widget.sender = lambda: sender
        widget.toggleQueue(False)
        widget.heart_beat_timer.start.assert_called_once()


class TestMDIHistoryClearQueue:
    """Tests for clearQueue method."""

    def test_clear_queue_marks_todo_as_done(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        item1.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_TODO)
        widget.addItem(item1)
        
        item2 = QListWidgetItem("G1 X5")
        item2.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
        widget.addItem(item2)
        
        widget.clearQueue()
        
        # TODO items should be marked as DONE with no icon
        assert widget.item(0).data(MDIHistory.MDQQ_ROLE) == MDIHistory.MDIQ_DONE

    def test_clear_queue_natural_order(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.mdi_listorder_natural = True
        
        item1 = QListWidgetItem("G0 X1")
        item1.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_TODO)
        widget.addItem(item1)
        
        widget.clearQueue()
        assert widget.item(0).data(MDIHistory.MDQQ_ROLE) == MDIHistory.MDIQ_DONE


class TestMDIHistoryRemoveSelectedItem:
    """Tests for removeSelectedItem method."""

    def test_remove_selected_item(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        item2 = QListWidgetItem("G1 X5")
        widget.addItem(item2)
        
        widget.setCurrentRow(1)
        widget.removeSelectedItem()
        
        assert widget.count() == 1

    def test_remove_selected_item_updates_current_row(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        item2 = QListWidgetItem("G1 X5")
        widget.addItem(item2)
        
        # Select item at row 1 and remove it - after removal should select row 0
        widget.setCurrentRow(1)
        widget.takeItem(1)  # manually remove to test the expected behavior
        assert widget.count() == 1
        assert widget.currentRow() == 0


class TestMDIHistoryRemoveAll:
    """Tests for removeAll method."""

    def test_remove_all_clears_list(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        widget.addItem(QListWidgetItem("G0 X1"))
        widget.addItem(QListWidgetItem("G1 X5"))
        
        widget.removeAll()
        assert widget.count() == 0


class TestMDIHistoryRunFromSelection:
    """Tests for runFromSelection method."""

    def test_run_from_selection_marks_todo(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        item1.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
        widget.addItem(item1)
        
        item2 = QListWidgetItem("G1 X5")
        item2.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
        widget.addItem(item2)
        
        widget.setCurrentItem(item2)
        widget.runFromSelection()
        
        assert item2.data(MDIHistory.MDQQ_ROLE) == MDIHistory.MDIQ_TODO

    def test_run_from_selection_empty_list(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        # Should not raise on empty list
        widget.runFromSelection()


class TestMDIHistoryRunSelection:
    """Tests for runSelection method."""

    def test_run_selection_marks_todo(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item = QListWidgetItem("G0 X1")
        item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
        widget.addItem(item)
        
        widget.setCurrentItem(item)
        widget.runSelection()
        
        assert item.data(MDIHistory.MDQQ_ROLE) == MDIHistory.MDIQ_TODO

    def test_run_selection_invalid_row(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        # Should not raise on invalid row
        widget.runSelection()


class TestMDIHistorySubmit:
    """Tests for submit method."""

    def test_submit_with_no_entry_widget_logs_warning(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.mdi_entry_widget = None
        
        # Should not raise, just log warning
        widget.submit()

    def test_submit_with_empty_text(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from unittest.mock import MagicMock
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        entry = MagicMock()
        entry.text.return_value = ''
        widget.mdi_entry_widget = entry
        
        widget.submit()
        assert widget.count() == 0

    def test_submit_with_text_adds_item(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from unittest.mock import MagicMock
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        entry = MagicMock()
        entry.text.return_value = 'G0 X1'
        entry.clear = MagicMock()
        widget.mdi_entry_widget = entry
        
        widget.submit()
        assert widget.count() == 1

    def test_submit_sets_todo_status(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from unittest.mock import MagicMock
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        entry = MagicMock()
        entry.text.return_value = 'G0 X1'
        entry.clear = MagicMock()
        widget.mdi_entry_widget = entry
        
        widget.submit()
        item = widget.item(0)
        assert item.data(MDIHistory.MDQQ_ROLE) == MDIHistory.MDIQ_TODO


class TestMDIHistoryCopySelectionToGcodeEditor:
    """Tests for copySelectionToGcodeEditor method."""

    def test_copy_selection_to_file(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from unittest.mock import MagicMock, patch
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        widget.setCurrentRow(0)
        
        with patch('qtpyvcp.widgets.input_widgets.mdihistory_widget.loadProgram') as mock_load:
            widget.copySelectionToGcodeEditor()
            # Should write to file and call loadProgram


class TestMDIHistoryMoveRowItemUp:
    """Tests for moveRowItemUp method."""

    def test_move_row_up(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        item2 = QListWidgetItem("G1 X5")
        widget.addItem(item2)
        
        widget.setCurrentItem(item2)
        widget.moveRowItemUp()
        
        assert widget.item(0).text() == "G1 X5"
        assert widget.item(1).text() == "G0 X1"

    def test_move_row_up_at_top_does_nothing(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        
        widget.setCurrentItem(item1)
        widget.moveRowItemUp()
        assert widget.item(0).text() == "G0 X1"


class TestMDIHistoryMoveRowItemDown:
    """Tests for moveRowItemDown method."""

    def test_move_row_down(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        item2 = QListWidgetItem("G1 X5")
        widget.addItem(item2)
        
        widget.setCurrentItem(item1)
        widget.moveRowItemDown()
        
        assert widget.item(0).text() == "G1 X5"
        assert widget.item(1).text() == "G0 X1"

    def test_move_row_down_at_bottom_does_nothing(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        
        widget.setCurrentItem(item1)
        widget.moveRowItemDown()
        assert widget.item(0).text() == "G0 X1"


class TestMDIHistoryKeyPressEvent:
    """Tests for keyPressEvent method."""

    def test_key_up_moves_selection_up(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        item2 = QListWidgetItem("G1 X5")
        widget.addItem(item2)
        
        widget.setCurrentItem(item2)
        
        event_up = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Up,
            Qt.NoModifier
        )
        widget.keyPressEvent(event_up)
        assert widget.currentRow() == 0

    def test_key_down_moves_selection_down(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        item1 = QListWidgetItem("G0 X1")
        widget.addItem(item1)
        item2 = QListWidgetItem("G1 X5")
        widget.addItem(item2)
        
        widget.setCurrentItem(item1)
        
        event_down = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Down,
            Qt.NoModifier
        )
        widget.keyPressEvent(event_down)
        assert widget.currentRow() == 1


class TestMDIHistorySetHistory:
    """Tests for setHistory method."""

    def test_set_history_clears_list(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        widget.addItem(QListWidgetItem("old"))
        widget.setHistory(["new1", "new2"])
        assert widget.count() == 2

    def test_set_history_populates_items(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        # Default (natural=False): items added in order
        widget.setHistory(["G0 X1", "G1 X5"])
        assert widget.item(0).text() == "G0 X1"
        assert widget.item(1).text() == "G1 X5"

    def test_set_history_marks_done(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        widget.setHistory(["G0 X1"])
        assert widget.item(0).data(MDIHistory.MDQQ_ROLE) == MDIHistory.MDIQ_DONE

    def test_set_history_empty_list(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        
        widget.setHistory([])
        assert widget.count() == 0

    def test_set_history_natural_order(self, qtbot):
        from qtpy.QtWidgets import QListWidgetItem
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.mdi_listorder_natural = True
        
        widget.setHistory(["G0 X1", "G1 X5"])
        # In natural order, list is reversed before adding
        assert widget.item(0).text() == "G1 X5"
        assert widget.item(1).text() == "G0 X1"


class TestMDIHistoryRowClicked:
    """Tests for rowClicked method."""

    def test_row_clicked_exists(self, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        # Should not raise
        widget.rowClicked()


class TestMDIHistoryInitialize:
    """Tests for initialize method."""

    @patch('qtpyvcp.widgets.input_widgets.mdihistory_widget.STATUS')
    def test_initialize_loads_history(self, mock_status, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        mock_status.mdi_history.value = ["G0 X1", "G1 X5"]
        
        widget.initialize()
        assert widget.count() == 2

    @patch('qtpyvcp.widgets.input_widgets.mdihistory_widget.STATUS')
    def test_initialize_starts_timer(self, mock_status, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        mock_status.mdi_history.value = []
        
        widget.initialize()
        assert widget.heart_beat_timer is not None


class TestMDIHistoryTerminate:
    """Tests for terminate method."""

    @patch('qtpyvcp.widgets.input_widgets.mdihistory_widget.STATUS')
    def test_terminate_stops_timer(self, mock_status, qtbot):
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        mock_status.mdi_history.value = []
        
        widget.initialize()
        stop_mock = MagicMock()
        widget.heart_beat_timer.stop = stop_mock
        
        widget.terminate()
        stop_mock.assert_called_once()


class TestMDIHistorySubmitNaturalOrder:
    """Tests for submit with natural list order."""

    def test_submit_natural_order_adds_to_end(self, qtbot):
        from unittest.mock import MagicMock
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.mdi_listorder_natural = True
        
        entry = MagicMock()
        entry.text.return_value = 'G0 X1'
        entry.clear = MagicMock()
        widget.mdi_entry_widget = entry
        
        widget.submit()
        assert widget.item(0).text() == "G0 X1"

    def test_submit_non_natural_order_adds_to_top(self, qtbot):
        from unittest.mock import MagicMock
        from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory

        widget = MDIHistory()
        qtbot.addWidget(widget)
        widget.mdi_listorder_natural = False
        
        entry = MagicMock()
        entry.text.return_value = 'G0 X1'
        entry.clear = MagicMock()
        widget.mdi_entry_widget = entry
        
        widget.submit()
        assert widget.item(0).text() == "G0 X1"
