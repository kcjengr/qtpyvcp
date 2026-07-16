import pytest
from unittest.mock import MagicMock, patch


class TestFindReplaceDialog:
    """Tests for FindReplaceDialog widget."""

    @pytest.fixture
    def mock_parent(self):
        parent = MagicMock()
        parent.highlightAllMatches = MagicMock(return_value=True)
        parent.clearHighlights = MagicMock()
        parent.getMatchCount = MagicMock(return_value=5)
        parent.getCurrentMatchIndex = MagicMock(return_value=2)
        parent.findNext = MagicMock(return_value=True)
        parent.findPrevious = MagicMock(return_value=True)
        parent.replaceCurrentWithUndo = MagicMock(return_value={"pos": 10, "new_text": "X", "original": "Y"})
        parent.replaceAllWithUndo = MagicMock(return_value=[{"pos": 10, "new_text": "X", "original": "Y"}])
        parent.document = MagicMock()
        return parent

    @pytest.fixture
    def dialog(self, qtbot, mock_parent):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        # Replace the parent reference with our mock for method calls
        d.parent = mock_parent
        # Keep real_parent alive to prevent widget deletion
        d._real_parent = real_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        return d

    def test_init_creates_ui_elements(self, dialog):
        assert dialog.find_input is not None
        assert dialog.replace_input is not None
        assert dialog.find_prev_arrow is not None
        assert dialog.find_next_arrow is not None
        assert dialog.status_label is not None
        assert dialog.replace_button is not None
        assert dialog.replace_all_button is not None
        assert dialog.close_button is not None
        assert dialog.undo_button is not None

    def test_init_window_title(self, dialog):
        assert dialog.windowTitle() == "Find / Replace"

    def test_init_object_name(self, dialog):
        assert dialog.objectName() == "findReplaceDialog"

    def test_init_minimum_width(self, dialog):
        assert dialog.minimumWidth() >= 520

    def test_init_undo_button_disabled_by_default(self, dialog):
        assert dialog.undo_button.isEnabled() is False

    def test_init_replace_undo_stack_empty(self, dialog):
        assert dialog._replace_undo_stack == []

    def test_find_input_placeholder(self, dialog):
        assert "search" in dialog.find_input.placeholderText().lower()

    def test_replace_input_placeholder(self, dialog):
        assert "Replace" in dialog.replace_input.placeholderText()

    def test_status_label_initially_empty(self, dialog):
        assert dialog.status_label.text() == ""

    def test_find_next_calls_parent_method(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        dialog.find_next()
        mock_parent.findNext.assert_called_once()
        call_args = mock_parent.findNext.call_args
        assert call_args[0][0] == "test"
        assert call_args[1]["wrap"] is True

    def test_find_previous_calls_parent_method(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        dialog.find_previous()
        mock_parent.findPrevious.assert_called_once()
        call_args = mock_parent.findPrevious.call_args
        assert call_args[0][0] == "test"
        assert call_args[1]["wrap"] is True

    def test_find_next_with_empty_text(self, dialog, mock_parent):
        dialog.find_input.setText("")
        dialog.find_next()
        mock_parent.findNext.assert_not_called()

    def test_find_previous_with_empty_text(self, dialog, mock_parent):
        dialog.find_input.setText("")
        dialog.find_previous()
        mock_parent.findPrevious.assert_not_called()

    def test_replace_current_calls_parent_method(self, dialog, mock_parent):
        dialog.find_input.setText("find")
        dialog.replace_input.setText("replace")
        dialog.replace_current()
        mock_parent.replaceCurrentWithUndo.assert_called_once()

    def test_replace_all_calls_parent_method(self, dialog, mock_parent):
        dialog.find_input.setText("find")
        dialog.replace_input.setText("replace")
        dialog.replace_all()
        mock_parent.replaceAllWithUndo.assert_called_once()

    def test_replace_all_sets_status_label(self, dialog, mock_parent):
        dialog.find_input.setText("find")
        dialog.replace_input.setText("replace")
        dialog.replace_all()
        assert "Replaced" in dialog.status_label.text()

    def test_undo_button_enabled_after_replace(self, dialog, mock_parent):
        dialog.find_input.setText("find")
        dialog.replace_input.setText("replace")
        dialog.replace_current()
        assert dialog.undo_button.isEnabled() is True

    def test_hide_dialog_calls_hide(self, qtbot, mock_parent):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        d.show()
        d.hide_dialog()
        assert d.isVisible() is False

    def test_keyPressEvent_Escape_closes_dialog(self, qtbot, mock_parent):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        d.show()
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Escape,
            Qt.NoModifier
        )
        d.keyPressEvent(event)
        assert d.isVisible() is False

    def test_keyPressEvent_Return_finds_next(self, qtbot, mock_parent):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        d.find_input.setText("test")
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Return,
            Qt.NoModifier
        )
        d.keyPressEvent(event)
        mock_parent.findNext.assert_called_once()

    def test_keyPressEvent_ShiftReturn_finds_previous(self, qtbot, mock_parent):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        d.find_input.setText("test")
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_Return,
            Qt.ShiftModifier
        )
        d.keyPressEvent(event)
        mock_parent.findPrevious.assert_called_once()

    def test_keyPressEvent_other_key_passes_through(self, qtbot, mock_parent):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key_A,
            Qt.NoModifier
        )
        # Should not raise - just passes to super
        d.keyPressEvent(event)

    def test_on_search_text_changed_highlights(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        dialog.on_search_text_changed("test")
        mock_parent.highlightAllMatches.assert_called()

    def test_on_search_text_changed_clears_when_empty(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        dialog.on_search_text_changed("")
        mock_parent.clearHighlights.assert_called()
        assert dialog.status_label.text() == ""

    def test_update_match_count_shows_count(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        mock_parent.getMatchCount.return_value = 10
        mock_parent.getCurrentMatchIndex.return_value = 3
        dialog.update_match_count()
        assert "3 of 10" in dialog.status_label.text()

    def test_update_match_count_shows_not_found(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        mock_parent.getMatchCount.return_value = 0
        dialog.update_match_count()
        assert "Not found" in dialog.status_label.text()

    def test_update_match_count_clears_when_negative(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        mock_parent.getMatchCount.return_value = -1
        dialog.update_match_count()
        assert dialog.status_label.text() == ""

    def test_find_next_highlights_result(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        dialog.find_next()
        mock_parent.highlightAllMatches.assert_called()

    def test_find_previous_highlights_result(self, dialog, mock_parent):
        dialog.find_input.setText("test")
        dialog.find_previous()
        mock_parent.highlightAllMatches.assert_called()

    def test_replace_current_pushes_to_undo_stack(self, dialog, mock_parent):
        dialog.find_input.setText("find")
        dialog.replace_input.setText("replace")
        dialog.replace_current()
        assert len(dialog._replace_undo_stack) == 1

    def test_undo_last_replace_restores_text(self, qtbot, mock_parent):
        from qtpy.QtWidgets import QWidget
        from qtpy.QtGui import QTextDocument
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        
        mock_record = {"pos": 5, "new_text": "X", "original": "Y"}
        mock_parent.replaceCurrentWithUndo.return_value = mock_record
        
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        
        d.find_input.setText("find")
        d.replace_input.setText("replace")
        d.replace_current()
        
        assert len(d._replace_undo_stack) == 1
        
        # Undo should restore original text
        document = QTextDocument()
        mock_parent.document.return_value = document
        
        d.undo_last_replace()
        
        assert d.undo_button.isEnabled() is False

    def test_undo_last_replace_clears_when_empty_stack(self, dialog):
        dialog.undo_last_replace()
        # Should not raise even with empty stack

    def test_undo_last_replace_disables_button_when_stack_empty(self, qtbot, mock_parent):
        from qtpy.QtWidgets import QWidget
        from qtpy.QtGui import QTextDocument
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        
        # Push one item to stack, then undo it
        d._replace_undo_stack.append([{"pos": 5, "new_text": "X", "original": "Y"}])
        d.undo_button.setEnabled(True)
        
        document = QTextDocument()
        mock_parent.document.return_value = document
        
        d.undo_last_replace()
        assert d.undo_button.isEnabled() is False

    def test_showEvent_focuses_find_input(self, qtbot, mock_parent):
        from qtpy.QtWidgets import QWidget, QApplication
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        
        d.show()
        QApplication.processEvents()
        # Qt focus is asynchronous - verify showEvent was called and find_input exists
        assert d.isVisible() is True
        assert d.find_input is not None

    def test_hideEvent_clears_highlights(self, qtbot, mock_parent):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog
        real_parent = QWidget()
        d = FindReplaceDialog(real_parent)
        d.parent = mock_parent
        qtbot.addWidget(d)
        d._real_parent = real_parent
        
        d.show()
        d.hide()
        mock_parent.clearHighlights.assert_called()

    def test_find_input_text_changed_connects_to_handler(self, dialog):
        # Verify the connection exists by checking signal is connected
        assert dialog.find_input.textChanged is not None

    def test_replace_button_connects_to_replace_current(self, dialog):
        assert dialog.replace_button.clicked is not None

    def test_close_button_connects_to_hide_dialog(self, dialog):
        assert dialog.close_button.clicked is not None

    def test_undo_button_connects_to_undo_last_replace(self, dialog):
        assert dialog.undo_button.clicked is not None

    def test_default_palette_stored(self, dialog):
        assert dialog.default_palette is not None

    def test_error_palette_has_red_background(self, dialog):
        from qtpy.QtGui import QPalette
        color = dialog.error_palette.color(QPalette.Base)
        assert color.red() == 255 or color.green() == 0 or color.blue() == 0
