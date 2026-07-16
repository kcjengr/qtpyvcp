import pytest
from unittest.mock import MagicMock, patch


class TestRecentFileComboBox:
    """Tests for RecentFileComboBox widget."""

    def test_init_no_parent(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        assert w is not None

    def test_inherits_from_qcombobox(self, qtbot):
        from qtpy.QtWidgets import QComboBox
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        assert isinstance(w, QComboBox)

    def test_has_no_file_loaded_item(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        assert w.itemText(0) == 'No File Loaded'

    def test_no_file_loaded_has_none_data(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        assert w.itemData(0) is None

    def test_current_index_starts_at_zero(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        assert w.currentIndex() == 0

    def test_has_browse_for_files_item(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        # Last item should be "Browse for files ..."
        last_index = w.count() - 1
        assert w.itemText(last_index) == "Browse for files ..."

    def test_browse_for_files_has_browse_files_data(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        last_index = w.count() - 1
        assert w.itemData(last_index) == 'browse_files'

    def test_has_separator_before_browse_item(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        w = RecentFileComboBox()
        qtbot.addWidget(w)
        last_index = w.count() - 1
        assert w.model().item(last_index - 1).text() == ''

    def test_update_recent_files_clears_and_populates(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        mock_status = MagicMock()
        mock_files = ['/path/to/file1.ngc', '/path/to/file2.ngc']
        mock_status.recent_files.getValue.return_value = mock_files
        mock_status.recent_files.__iter__ = lambda _: iter(mock_files)

        with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.getPlugin', return_value=mock_status):
            w = RecentFileComboBox()
            qtbot.addWidget(w)
            assert w.count() == 5  # No File Loaded + 2 files + separator + browse

    def test_update_recent_files_shows_basenames(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        mock_status = MagicMock()
        mock_files = ['/path/to/file1.ngc', '/path/to/file2.ngc']
        mock_status.recent_files.getValue.return_value = mock_files
        mock_status.recent_files.__iter__ = lambda _: iter(mock_files)

        with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.getPlugin', return_value=mock_status):
            w = RecentFileComboBox()
            qtbot.addWidget(w)
            assert w.itemText(1) == 'file1.ngc'
            assert w.itemText(2) == 'file2.ngc'

    def test_update_recent_files_sets_file_paths_as_data(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        mock_status = MagicMock()
        mock_files = ['/path/to/file1.ngc', '/path/to/file2.ngc']
        mock_status.recent_files.getValue.return_value = mock_files
        mock_status.recent_files.__iter__ = lambda _: iter(mock_files)

        with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.getPlugin', return_value=mock_status):
            w = RecentFileComboBox()
            qtbot.addWidget(w)
            assert w.itemData(1) == '/path/to/file1.ngc'
            assert w.itemData(2) == '/path/to/file2.ngc'

    def test_on_item_activated_browse_shows_open_file_dialog(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        mock_getDialog = MagicMock()
        mock_open_file = MagicMock()
        mock_getDialog.return_value = mock_open_file

        with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.getDialog', mock_getDialog):
            w = RecentFileComboBox()
            qtbot.addWidget(w)
            w.setCurrentIndex(w.count() - 1)  # Browse item
            w.onItemActivated()
            mock_open_file.show.assert_called_once()

    def test_on_item_activated_none_data_does_nothing(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.getDialog') as mock_getDialog:
            w = RecentFileComboBox()
            qtbot.addWidget(w)
            w.setCurrentIndex(0)  # No File Loaded item (data is None)
            w.onItemActivated()
            mock_getDialog.assert_not_called()

    def test_on_item_activated_file_loads_program(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        mock_status = MagicMock()
        mock_files = ['/path/to/test.ngc']
        mock_status.recent_files.getValue.return_value = mock_files
        mock_status.recent_files.__iter__ = lambda _: iter(mock_files)

        with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.getPlugin', return_value=mock_status):
            w = RecentFileComboBox()
            qtbot.addWidget(w)
            # Find the index of the test.ngc item
            for i in range(w.count()):
                if w.itemData(i) == '/path/to/test.ngc':
                    w.setCurrentIndex(i)
                    break
            with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.loadProgram') as mock_load:
                w.onItemActivated()
                mock_load.assert_called_once_with('/path/to/test.ngc')

    def test_on_item_activated_browse_calls_getDialog(self, qtbot):
        from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
        dialog_mock = MagicMock()
        with patch('qtpyvcp.widgets.input_widgets.recent_file_combobox.getDialog', return_value=dialog_mock):
            w = RecentFileComboBox()
            qtbot.addWidget(w)
            last_index = w.count() - 1
            w.setCurrentIndex(last_index)
            w.onItemActivated()
            dialog_mock.show.assert_called_once()
