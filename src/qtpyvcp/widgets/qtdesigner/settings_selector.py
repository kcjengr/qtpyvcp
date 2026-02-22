
import os

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QApplication

from PySide6.QtDesigner import QDesignerFormWindowInterface

from qtpyvcp import SETTINGS

from qtpyvcp.widgets.qtdesigner import _PluginExtension

from .settings_selector_ui import Ui_Dialog

UI_FILE = os.path.join(os.path.dirname(__file__), "settings_selector.ui")


class SettingSelectorExtension(_PluginExtension):
    def __init__(self, widget):
        super(SettingSelectorExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Select Setting ...", self.editAction)

    def editAction(self, state):
        SettingSelector(self.widget, parent=None).exec()


class SettingSelector(QDialog, Ui_Dialog):
    """QDialog for user-friendly selection of settings in Qt Designer."""

    def __init__(self, widget, parent=None):
        super(SettingSelector, self).__init__(parent)

        self.widget = widget
        self.app = QApplication.instance()
        

        # file_path = os.path.join(os.path.dirname(__file__), UI_FILE)
        # ui_file = QFile(file_path)
        # ui_file.open(QFile.ReadOnly)
        #
        # loader = QUiLoader()
        # self.ui = loader.load(ui_file, self)
        #self.ui.show()
        
        # self.ui = Ui_Dialog()
        self.setupUi(self)

        for setting in sorted(SETTINGS):
            print(setting)
            print((SETTINGS[setting].__doc__))
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
        self.setCursorProperty('settingName', self.settingsCombo.currentText())

        self.close()

    def setCursorProperty(self, prop_name, value):
        form = QDesignerFormWindowInterface.findFormWindow(self.widget)
        if form:
            form.cursor().setProperty(prop_name, value)
