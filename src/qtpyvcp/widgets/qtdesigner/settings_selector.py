import re

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QApplication, QMessageBox

from PySide6.QtDesigner import QDesignerFormWindowInterface

from qtpyvcp import SETTINGS

from qtpyvcp.widgets.qtdesigner import _PluginExtension

from .settings_selector_ui import Ui_Dialog


class SettingSelectorExtension(_PluginExtension):
    def __init__(self, widget):
        super(SettingSelectorExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Select Setting ...", self.editAction)

    def editAction(self, state):
        SettingSelector(self.widget, parent=None).exec()


class ConvertToVarLineEditExtension(_PluginExtension):
    """Task-menu extension to convert a VCPSettingsLineEdit into VCPVarLineEdit."""

    def __init__(self, widget):
        super(ConvertToVarLineEditExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Convert to VCPVarLineEdit ...", self.convertAction)

    def _convert_selected_widget_block(self, ui_text, widget_name):
        # Match selected widget by name first, then verify class.
        pattern = (
            r'(<widget\b(?=[^>]*\bname="' + re.escape(widget_name) + r'")[^>]*>)'
            r'(.*?)'
            r'(</widget>)'
        )

        m = re.search(pattern, ui_text, flags=re.DOTALL)
        if not m:
            return ui_text, False, (
                f"Widget '{widget_name}' block not found in form contents. "
                "Save the form once and retry conversion."
            )

        opening_tag, body, closing_tag = m.groups()

        if 'class="VCPSettingsLineEdit"' not in opening_tag:
            class_match = re.search(r'\bclass="([^"]+)"', opening_tag)
            current_class = class_match.group(1) if class_match else "<unknown>"
            return ui_text, False, (
                f"Widget '{widget_name}' is class '{current_class}', expected "
                "'VCPSettingsLineEdit'."
            )

        # Change widget class while preserving name and other attributes.
        opening_tag = opening_tag.replace('class="VCPSettingsLineEdit"', 'class="VCPVarLineEdit"', 1)

        # Remove settings-specific properties not used by VCPVarLineEdit.
        body = re.sub(r'\n\s*<property name="settingName"[^>]*>.*?</property>', '', body, flags=re.DOTALL)
        body = re.sub(r'\n\s*<property name="settingTypeMode"[^>]*>.*?</property>', '', body, flags=re.DOTALL)

        # Ensure varParameterNumber exists so converted widget is immediately configurable.
        if 'name="varParameterNumber"' not in body:
            indent_match = re.search(r'\n(\s*)<property\b', body)
            indent = indent_match.group(1) if indent_match else '      '
            var_prop = (
                f"\\n{indent}<property name=\"varParameterNumber\">"
                f"\\n{indent} <number>3015</number>"
                f"\\n{indent}</property>"
            )
            body = var_prop + body

        new_block = opening_tag + body + closing_tag
        start, end = m.span()
        return ui_text[:start] + new_block + ui_text[end:], True, ""

    def convertAction(self, state):
        form = QDesignerFormWindowInterface.findFormWindow(self.widget)
        if not form:
            QMessageBox.warning(None, "Convert to VCPVarLineEdit", "No active form window found.")
            return

        reply = QMessageBox.question(
            None,
            "Convert to VCPVarLineEdit",
            (
                f"Convert widget '{self.widget.objectName()}' from VCPSettingsLineEdit "
                "to VCPVarLineEdit?\\n\\n"
                "This keeps object name/geometry and most properties, removes setting-specific "
                "properties, and adds varParameterNumber if missing."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            contents = form.contents()
            ui_text = contents if isinstance(contents, str) else str(contents)

            new_text, changed, error_msg = self._convert_selected_widget_block(ui_text, self.widget.objectName())
            if not changed:
                QMessageBox.warning(None, "Convert to VCPVarLineEdit", error_msg)
                return

            form.beginCommand("Convert VCPSettingsLineEdit to VCPVarLineEdit")
            form.setContents(new_text)
            form.endCommand()
            form.setDirty(True)
        except Exception as e:
            try:
                form.endCommand()
            except Exception:
                pass
            QMessageBox.critical(None, "Convert to VCPVarLineEdit", f"Conversion failed: {e}")


class SettingSelector(QDialog, Ui_Dialog):
    """QDialog for user-friendly selection of settings in Qt Designer."""

    def __init__(self, widget, parent=None):
        super(SettingSelector, self).__init__(parent)

        self.widget = widget
        self.app = QApplication.instance()

        # Keep Setting Selector behavior aligned with Rules Editor by
        # preloading settings from configured YAML files in Designer.
        from .rules_editor import _ensure_designer_settings_loaded
        _ensure_designer_settings_loaded(self.widget)

        self.setupUi(self)

        for setting in sorted(SETTINGS):
            self.settingsCombo.addItem(setting)

        current_setting = self.widget.settingName
        if current_setting:
            if current_setting in SETTINGS:
                    self.settingsCombo.setCurrentText(self.widget.settingName)
            else:
                self.settingsCombo.insertItem(0, current_setting)
                self.settingsCombo.setCurrentIndex(0)

        bb = self.buttonBox
        bb.button(QDialogButtonBox.StandardButton.Apply).setDefault(True)
        bb.button(QDialogButtonBox.StandardButton.Cancel).setDefault(False)
        bb.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)

    @Slot()
    def accept(self):
        """Commit changes"""
        selected_setting = self.settingsCombo.currentText()
        self.setCursorProperty('settingName', selected_setting)

        setting = SETTINGS.get(selected_setting)
        if setting is not None and hasattr(self.widget, 'settingTypeMode'):
            if setting.value_type is float:
                mode = 'float'
            elif setting.value_type is int:
                mode = 'int'
            else:
                mode = 'text'
            self.setCursorProperty('settingTypeMode', mode)

        self.close()

    def setCursorProperty(self, prop_name, value):
        form = QDesignerFormWindowInterface.findFormWindow(self.widget)
        if form:
            form.cursor().setProperty(prop_name, value)
