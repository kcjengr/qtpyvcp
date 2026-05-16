import pytest


class TestBaseDialogInit:
    def test_default_parent(self, base_dialog):
        assert base_dialog.parent() is None

    def test_inherits_from_qdialog(self, base_dialog):
        from qtpy.QtWidgets import QDialog

        assert isinstance(base_dialog, QDialog)

    def test_default_window_title(self, base_dialog):
        assert base_dialog.windowTitle() == ""

    def test_default_modality(self, base_dialog):
        from qtpy.QtCore import Qt

        assert base_dialog.windowModality() == Qt.NonModal


class TestBaseDialogTitle:
    def test_set_window_title(self, base_dialog):
        base_dialog.setWindowTitle("My Dialog")
        assert base_dialog.windowTitle() == "My Dialog"

    def test_set_empty_title(self, base_dialog):
        base_dialog.setWindowTitle("")
        assert base_dialog.windowTitle() == ""


class TestBaseDialogModality:
    def test_set_modal_true(self, base_dialog):
        from qtpy.QtCore import Qt

        base_dialog.setWindowModality(Qt.ApplicationModal)
        assert base_dialog.windowModality() == Qt.ApplicationModal

    def test_set_modal_false(self, base_dialog):
        from qtpy.QtCore import Qt

        base_dialog.setWindowModality(Qt.NonModal)
        assert base_dialog.windowModality() == Qt.NonModal

    def test_modal_constructor_true(self, base_dialog):
        from qtpy.QtCore import Qt

        dialog = base_dialog.__class__(modal=True)
        assert dialog.windowModality() == Qt.ApplicationModal

    def test_modal_constructor_false(self, base_dialog):
        from qtpy.QtCore import Qt

        dialog = base_dialog.__class__(modal=False)
        assert dialog.windowModality() == Qt.NonModal


class TestBaseDialogWindowFlags:
    def test_frameless_true(self, base_dialog):
        from qtpy.QtCore import Qt

        base_dialog.setWindowFlag(Qt.FramelessWindowHint, True)
        flags = base_dialog.windowFlags()
        assert flags & Qt.FramelessWindowHint

    def test_stay_on_top_true(self, base_dialog):
        from qtpy.QtCore import Qt

        base_dialog.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        flags = base_dialog.windowFlags()
        assert flags & Qt.WindowStaysOnTopHint

    def test_popup_flag(self, base_dialog):
        from qtpy.QtCore import Qt

        base_dialog.setWindowFlags(Qt.Popup)
        flags = base_dialog.windowFlags()
        assert flags & Qt.Popup

    def test_frameless_constructor_true(self, base_dialog):
        from qtpy.QtCore import Qt

        dialog = base_dialog.__class__(frameless=True)
        flags = dialog.windowFlags()
        assert flags & Qt.FramelessWindowHint

    def test_stay_on_top_constructor_true(self, base_dialog):
        from qtpy.QtCore import Qt

        dialog = base_dialog.__class__(stay_on_top=True)
        flags = dialog.windowFlags()
        assert flags & Qt.WindowStaysOnTopHint

    def test_setWindowFlag_toggles_flag(self, base_dialog):
        from qtpy.QtCore import Qt

        initial_flags = base_dialog.windowFlags()
        base_dialog.setWindowFlag(Qt.FramelessWindowHint, True)
        after_on = base_dialog.windowFlags()
        assert after_on != initial_flags or (after_on & Qt.FramelessWindowHint)
        base_dialog.setWindowFlag(Qt.FramelessWindowHint, False)
        after_off = base_dialog.windowFlags()

    def test_multiple_flags(self, base_dialog):
        from qtpy.QtCore import Qt

        base_dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        flags = base_dialog.windowFlags()
        assert flags & Qt.Dialog
        assert flags & Qt.WindowStaysOnTopHint


class TestBaseDialogLoadUiFile:
    def test_load_nonexistent_file_logs_error(self, base_dialog, caplog):
        import logging

        result = base_dialog.loadUiFile("/nonexistent/path/dialog.ui")
        assert result is None
        assert any("does not exist" in record.message for record in caplog.records)

    def test_load_valid_ui_file(self, base_dialog, tmp_path):
        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QDialog

        ui_content = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>TestDialog</class>
 <widget class="QDialog" name="TestDialog">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>200</width>
    <height>100</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Loaded Dialog</string>
  </property>
 </widget>
 <resources/>
 <connections/>
</ui>"""

        ui_file = tmp_path / "test_dialog.ui"
        ui_file.write_text(ui_content)

        result = base_dialog.loadUiFile(str(ui_file))
        assert result is None
        assert base_dialog.windowTitle() == "Loaded Dialog"


class TestBaseDialogCombinedOptions:
    def test_title_and_modal_together(self, base_dialog):
        from qtpy.QtCore import Qt

        dialog = base_dialog.__class__(title="Test", modal=True)
        assert dialog.windowTitle() == "Test"
        assert dialog.windowModality() == Qt.ApplicationModal

    def test_frameless_and_stay_on_top(self, base_dialog):
        from qtpy.QtCore import Qt

        dialog = base_dialog.__class__(frameless=True, stay_on_top=True)
        flags = dialog.windowFlags()
        assert flags & Qt.FramelessWindowHint
        assert flags & Qt.WindowStaysOnTopHint

    def test_all_options_together(self, base_dialog, tmp_path):
        from qtpy.QtCore import Qt

        ui_content = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>TestDialog</class>
 <widget class="QDialog" name="TestDialog">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>200</width>
    <height>100</height>
   </rect>
  </property>
 </widget>
</ui>"""

        ui_file = tmp_path / "test_dialog.ui"
        ui_file.write_text(ui_content)

        dialog = base_dialog.__class__(
            ui_file=str(ui_file),
            title="Full Dialog",
            modal=False,
            frameless=True,
            stay_on_top=True,
        )
        assert dialog.windowTitle() == "Full Dialog"
        assert dialog.windowModality() == Qt.NonModal
        flags = dialog.windowFlags()
        assert flags & Qt.FramelessWindowHint
        assert flags & Qt.WindowStaysOnTopHint
