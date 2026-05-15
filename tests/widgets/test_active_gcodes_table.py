import importlib.util
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"


def _load_active_gcodes_module():
    """Load the active_gcodes_table module from source."""
    import qtpyvcp.widgets.display_widgets.active_gcodes_table as mod
    return mod


class TestActiveGcodesModelInit:
    """Tests for ActiveGcodesModel initialization."""

    def test_model_created(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        assert model is not None

    def test_model_has_two_columns(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        assert model.columnCount() == 2

    def test_model_column_labels(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        from qtpy.QtCore import Qt, QModelIndex
        header0 = model.headerData(0, Qt.Horizontal, Qt.DisplayRole)
        header1 = model.headerData(1, Qt.Horizontal, Qt.DisplayRole)
        assert header0 == "G-code"
        assert header1 == "Description"

    def test_model_has_rows(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        assert model.rowCount() > 0


class TestActiveGcodesTableData:
    """Tests for ActiveGcodesTable data display."""

    def test_g0_code_in_model(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        idx = model.index(0, 0)
        assert model.data(idx) == "G0"

    def test_g1_code_in_model(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        idx = model.index(1, 0)
        assert model.data(idx) == "G1"

    def test_g20_code_in_model(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            if model.data(idx) == "G20":
                desc_idx = model.index(row, 1)
                assert model.data(desc_idx) == "Inch units"
                break

    def test_g21_code_in_model(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            if model.data(idx) == "G21":
                desc_idx = model.index(row, 1)
                assert model.data(desc_idx) == "Millimeter units"
                break

    def test_g64_code_description(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            if model.data(idx) == "G64":
                desc_idx = model.index(row, 1)
                assert "blend" in model.data(desc_idx).lower()
                break

    def test_gcode_descriptions_populated(self):
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        for row in range(model.rowCount()):
            desc_idx = model.index(row, 1)
            assert len(model.data(desc_idx)) > 0


class TestActiveGcodesTableInit:
    """Tests for ActiveGcodesTable widget initialization."""

    def test_table_created(self, qtbot):
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table is not None

    def test_table_has_model(self, qtbot):
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.model() is not None

    def test_table_has_two_columns(self, qtbot):
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.model().columnCount() == 2

    def test_vertical_header_hidden(self, qtbot):
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.verticalHeader().isHidden() is True


class TestActiveGcodesTableBehavior:
    """Tests for ActiveGcodesTable behavior and properties."""

    def test_no_edit_triggers(self, qtbot):
        from qtpy.QtWidgets import QTableView
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.editTriggers() == QTableView.NoEditTriggers

    def test_single_selection_mode(self, qtbot):
        from qtpy.QtWidgets import QTableView
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.selectionMode() == QTableView.SingleSelection

    def test_select_rows_behavior(self, qtbot):
        from qtpy.QtWidgets import QTableView
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.selectionBehavior() == QTableView.SelectRows

    def test_alternating_row_colors(self, qtbot):
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.alternatingRowColors() is True

    def test_horizontal_header_stretch_last_section(self, qtbot):
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        header = table.horizontalHeader()
        assert header.sectionSize(1) > 0

    def test_active_code_color_property_default(self, qtbot):
        from qtpy.QtCore import Qt
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        color = table.activeCodeColor
        assert color.red() == 0

    def test_active_code_color_property_setter(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QColor
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        table.activeCodeColor = QColor(255, 0, 0)
        assert table.activeCodeColor.red() == 255

    def test_active_code_background_property_default(self, qtbot):
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        bg = table.activeCodeBackground
        assert bg.isValid() is False

    def test_active_code_background_property_setter(self, qtbot):
        from qtpy.QtGui import QColor
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        table.activeCodeBackground = QColor(255, 255, 0)
        assert table.activeCodeBackground.red() == 255


class TestActiveGcodesModelData:
    """Tests for ActiveGcodesModel data roles."""

    def test_display_role_returns_code(self):
        from qtpy.QtCore import Qt
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        idx = model.index(0, 0)
        assert model.data(idx, Qt.DisplayRole) == "G0"

    def test_edit_role_returns_code(self):
        from qtpy.QtCore import Qt
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        idx = model.index(0, 0)
        assert model.data(idx, Qt.EditRole) == "G0"

    def test_text_color_role_for_inactive_code(self):
        from qtpy.QtCore import Qt
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        idx = model.index(0, 0)
        color = model.data(idx, Qt.TextColorRole)
        assert color is None

    def test_flags_returns_enabled_only(self):
        from qtpy.QtCore import Qt
        mod = _load_active_gcodes_module()
        model = mod.ActiveGcodesModel()
        idx = model.index(0, 0)
        flags = model.flags(idx)
        assert flags & Qt.ItemIsEnabled
        assert not (flags & Qt.ItemIsEditable)


class TestActiveGcodesTableInheritance:
    """Tests for ActiveGcodesTable inheritance."""

    def test_inherits_from_qtableview(self, qtbot):
        from qtpy.QtWidgets import QTableView
        mod = _load_active_gcodes_module()
        table = mod.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert isinstance(table, QTableView)


class TestTableData:
    """Tests for the TABLE_DATA constant."""

    def test_data_has_g_codes(self):
        mod = _load_active_gcodes_module()
        assert len(mod.DATA) > 0

    def test_data_entries_have_code_and_description(self):
        mod = _load_active_gcodes_module()
        for entry in mod.DATA:
            assert 'code' in entry
            assert 'description' in entry
            assert len(entry['code']) > 0
            assert len(entry['description']) > 0

    def test_data_contains_g54(self):
        mod = _load_active_gcodes_module()
        codes = [e['code'] for e in mod.DATA]
        assert 'G54' in codes
