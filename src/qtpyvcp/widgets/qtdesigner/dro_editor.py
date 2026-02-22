
import os

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QApplication

from PySide6.QtDesigner import QDesignerFormWindowInterface


from qtpyvcp.widgets.qtdesigner import _PluginExtension

UI_FILE = os.path.join(os.path.dirname(__file__), "dro_editor.ui")


class DroEditorExtension(_PluginExtension):
    def __init__(self, widget):
        super(DroEditorExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Edit DRO Settings ...", self.editAction)

    def editAction(self, state):
        DroEditor(self.widget, parent=None).exec()


class DroEditor(QDialog):
    """QDialog for user-friendly editing of DRO properties in Qt Designer."""

    def __init__(self, widget, parent=None):
        super(DroEditor, self).__init__(parent)

        self.widget = widget
        self.app = QApplication.instance()

        file_path = os.path.join(os.path.dirname(__file__), UI_FILE)
        ui_file = QFile(file_path)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.ui.show()

        self.ui.axisCombo.setCurrentIndex(self.widget.axisNumber)
        self.ui.refTypCombo.setCurrentIndex(self.widget.referenceType)

        self.ui.inFmtEntry.setText(self.widget.inchFormat)
        self.ui.mmFmtEntry.setText(self.widget.millimeterFormat)
        self.ui.degFmtEntry.setText(self.widget.degreeFormat)

        self.ui.latheModeCombo.setCurrentIndex(self.widget.latheMode)

        bb = self.ui.buttonBox
        bb.button(QDialogButtonBox.StandardButton.Apply).setDefault(True)
        bb.button(QDialogButtonBox.StandardButton.Cancel).setDefault(False)
        bb.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)

    @Slot()
    def accept(self):
        """Commit changes"""
        # general options
        self.setCursorProperty('axisNumber', self.ui.axisCombo.currentIndex())
        self.setCursorProperty('referenceType', self.ui.refTypCombo.currentIndex())

        # format options
        self.setCursorProperty('inchFormat', self.ui.inFmtEntry.text())
        self.setCursorProperty('millimeterFormat', self.ui.mmFmtEntry.text())
        self.setCursorProperty('degreeFormat', self.ui.degFmtEntry.text())

        # lathe options
        self.setCursorProperty('latheMode', self.ui.latheModeCombo.currentIndex())

        self.close()

    def setCursorProperty(self, prop_name, value):
        form = QDesignerFormWindowInterface.findFormWindow(self.widget)
        if form:
            form.cursor().setProperty(prop_name, value)
