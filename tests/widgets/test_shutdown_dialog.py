import pytest
from unittest.mock import MagicMock, patch
import os


class TestShutDownDialog:
    """Tests for ShutDownDialog widget."""

    def test_init_no_parent(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_init_with_custom_ui_file(self, qtbot, tmp_path):
        from qtpy.QtWidgets import QDialog
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog

        custom_ui = tmp_path / "custom_shutdown.ui"
        custom_ui.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Dialog</class>
 <widget class="QDialog" name="Dialog">
  <property name="geometry">
   <rect><x>0</x><y>0</y><width>200</width><height>100</height></rect>
  </property>
  <property name="windowTitle"><string>Custom Shutdown</string></property>
 </widget>
 <resources/>
 <connections/>
</ui>""")

        dlg = ShutDownDialog(ui_file=str(custom_ui))
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_reject_hides_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        dlg.show()
        assert dlg.isVisible() is True
        dlg.reject()
        assert dlg.isVisible() is False

    def test_accept_hides_dialog(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        dlg.show()
        assert dlg.isVisible() is True
        dlg.accept()
        assert dlg.isVisible() is False

    def test_stay_on_top(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        flags = dlg.windowFlags()
        assert flags & Qt.WindowStaysOnTopHint

    def test_frameless(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        flags = dlg.windowFlags()
        assert flags & Qt.FramelessWindowHint

    def test_application_modal(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        assert dlg.windowModality() == Qt.ApplicationModal

    def test_has_cancel_button(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        cancel_btn = dlg.findChild(object, "btnCancel")
        assert cancel_btn is not None

    def test_cancel_button_exists_and_visible(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        cancel_btn = dlg.findChild(object, "btnCancel")
        assert cancel_btn is not None
        assert cancel_btn.text() == "Cancel"

    def test_ui_file_attribute_default(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        assert dlg.ui_file.endswith("shutdown_dialog.ui")

    def test_ui_file_attribute_custom(self, qtbot, tmp_path):
        from qtpy.QtWidgets import QDialog
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog

        custom_ui = tmp_path / "custom.ui"
        custom_ui.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Dialog</class>
 <widget class="QDialog" name="Dialog">
  <property name="geometry"><rect><x>0</x><y>0</y><width>200</width><height>100</height></rect></property>
  <property name="windowTitle"><string>Test</string></property>
 </widget>
</ui>""")

        dlg = ShutDownDialog(ui_file=str(custom_ui))
        qtbot.addWidget(dlg)
        assert dlg.ui_file == str(custom_ui)

    def test_has_action_button(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        action_btn = dlg.findChild(object, "actionbutton")
        assert action_btn is not None

    def test_action_button_has_correct_action_name(self, qtbot):
        from qtpyvcp.widgets.dialogs.shutdown_dialog import ShutDownDialog
        dlg = ShutDownDialog()
        qtbot.addWidget(dlg)
        action_btn = dlg.findChild(object, "actionbutton")
        assert hasattr(action_btn, 'actionName')
        assert action_btn.actionName == "power.shut_system_down_now"
