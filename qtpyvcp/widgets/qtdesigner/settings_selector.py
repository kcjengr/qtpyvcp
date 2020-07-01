
import os
from qtpy import uic
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QDialog, QDialogButtonBox, QApplication

from qtpy.QtDesigner import QDesignerFormWindowInterface

from qtpyvcp import SETTINGS

from qtpyvcp.widgets.qtdesigner import _PluginExtension

UI_FILE = os.path.join(os.path.dirname(__file__), "settings_selector.ui")


class SettingSelectorExtension(_PluginExtension):
    def __init__(self, widget):
        super(SettingSelectorExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Select Setting ...", self.editAction)

    def editAction(self, state):
        SettingSelector(self.widget, parent=None).exec_()


class SettingSelector(QDialog):
    """QDialog for user-friendly selection of settings in Qt Designer."""

    def __init__(self, widget, parent=None):
        super(SettingSelector, self).__init__(parent)

        self.widget = widget
        self.app = QApplication.instance()

        uic.loadUi(UI_FILE, self)

        for setting in sorted(SETTINGS):
            print setting
            print SETTINGS[setting].__doc__
            self.settingsCombo.addItem(setting)

        current_setting = self.widget.settingName
        if current_setting:
            if current_setting in SETTINGS:
                    self.settingsCombo.setCurrentText(self.widget.settingName)
            else:
                self.settingsCombo.insertItem(0, current_setting)
                self.settingsCombo.setCurrentIndex(0)

        bb = self.buttonBox
        bb.button(QDialogButtonBox.Apply).setDefault(True)
        bb.button(QDialogButtonBox.Cancel).setDefault(False)
        bb.button(QDialogButtonBox.Apply).clicked.connect(self.accept)

    @Slot()
    def accept(self):
        """Commit changes"""
        self.setCursorProperty('settingName', self.settingsCombo.currentText())

        self.close()

    def setCursorProperty(self, prop_name, value):
        form = QDesignerFormWindowInterface.findFormWindow(self.widget)
        if form:
            form.cursor().setProperty(prop_name, value)
