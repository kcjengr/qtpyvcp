import pytest


class TestActiveGcodesModelInit:
    """Tests for ActiveGcodesModel initialization."""

    def test_model_created(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        assert model is not None

    def test_model_has_two_columns(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        assert model.columnCount() == 2

    def test_model_column_labels(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        from qtpy.QtCore import Qt, QModelIndex
        header0 = model.headerData(0, Qt.Horizontal, Qt.DisplayRole)
        header1 = model.headerData(1, Qt.Horizontal, Qt.DisplayRole)
        assert header0 == "G-code"
        assert header1 == "Description"

    def test_model_has_rows(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        assert model.rowCount() > 0


class TestActiveGcodesTableData:
    """Tests for ActiveGcodesTable data display."""

    def test_g0_code_in_model(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        idx = model.index(0, 0)
        assert model.data(idx) == "G0"

    def test_g1_code_in_model(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        idx = model.index(1, 0)
        assert model.data(idx) == "G1"

    def test_g20_code_in_model(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            if model.data(idx) == "G20":
                desc_idx = model.index(row, 1)
                assert model.data(desc_idx) == "Inch units"
                break

    def test_g21_code_in_model(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            if model.data(idx) == "G21":
                desc_idx = model.index(row, 1)
                assert model.data(desc_idx) == "Millimeter units"
                break

    def test_g64_code_description(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            if model.data(idx) == "G64":
                desc_idx = model.index(row, 1)
                assert "blend" in model.data(desc_idx).lower()
                break

    def test_gcode_descriptions_populated(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        model = module.ActiveGcodesModel()
        for row in range(model.rowCount()):
            desc_idx = model.index(row, 1)
            assert len(model.data(desc_idx)) > 0


class TestActiveGcodesTableInit:
    """Tests for ActiveGcodesTable widget initialization."""

    def test_table_created(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table is not None

    def test_table_has_model(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.model() is not None

    def test_table_has_two_columns(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.model().columnCount() == 2

    def test_vertical_header_hidden(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.verticalHeader().isHidden() is True


class TestActiveGcodesTableBehavior:
    """Tests for ActiveGcodesTable behavior and properties."""

    def test_no_edit_triggers(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtWidgets import QTableView
        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.editTriggers() == QTableView.NoEditTriggers

    def test_single_selection_mode(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtWidgets import QTableView
        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.selectionMode() == QTableView.SingleSelection

    def test_select_rows_behavior(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtWidgets import QTableView
        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.selectionBehavior() == QTableView.SelectRows

    def test_alternating_row_colors(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert table.alternatingRowColors() is True

    def test_horizontal_header_stretch_last_section(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        header = table.horizontalHeader()
        assert header.sectionSize(1) > 0

    def test_active_code_color_property_default(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtCore import Qt
        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        color = table.activeCodeColor
        assert color.red() == 0

    def test_active_code_color_property_setter(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtCore import Qt
        from qtpy.QtGui import QColor
        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        table.activeCodeColor = QColor(255, 0, 0)
        assert table.activeCodeColor.red() == 255

    def test_active_code_background_property_default(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        bg = table.activeCodeBackground
        assert bg.isValid() is False

    def test_active_code_background_property_setter(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtGui import QColor
        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        table.activeCodeBackground = QColor(255, 255, 0)
        assert table.activeCodeBackground.red() == 255


class TestActiveGcodesModelData:
    """Tests for ActiveGcodesModel data roles."""

    def test_display_role_returns_code(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtCore import Qt
        model = module.ActiveGcodesModel()
        idx = model.index(0, 0)
        assert model.data(idx, Qt.DisplayRole) == "G0"

    def test_edit_role_returns_code(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtCore import Qt
        model = module.ActiveGcodesModel()
        idx = model.index(0, 0)
        assert model.data(idx, Qt.EditRole) == "G0"

    def test_text_color_role_for_inactive_code(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtCore import Qt
        model = module.ActiveGcodesModel()
        idx = model.index(0, 0)
        color = model.data(idx, Qt.TextColorRole)
        assert color is None

    def test_flags_returns_enabled_only(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtCore import Qt
        model = module.ActiveGcodesModel()
        idx = model.index(0, 0)
        flags = model.flags(idx)
        assert flags & Qt.ItemIsEnabled
        assert not (flags & Qt.ItemIsEditable)


class TestActiveGcodesTableInheritance:
    """Tests for ActiveGcodesTable inheritance."""

    def test_inherits_from_qtableview(self, qtbot):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        from qtpy.QtWidgets import QTableView
        table = module.ActiveGcodesTable()
        qtbot.addWidget(table)
        assert isinstance(table, QTableView)


class TestTableData:
    """Tests for the TABLE_DATA constant."""

    def test_data_has_g_codes(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        assert len(module.DATA) > 0

    def test_data_entries_have_code_and_description(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        for entry in module.DATA:
            assert 'code' in entry
            assert 'description' in entry
            assert len(entry['code']) > 0
            assert len(entry['description']) > 0

    def test_data_contains_g54(self):
        import sys
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "active_gcodes_table",
            "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/active_gcodes_table.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["qtpyvcp.widgets.display_widgets.active_gcodes_table"] = module
        spec.loader.exec_module(module)

        codes = [e['code'] for e in module.DATA]
        assert 'G54' in codes
