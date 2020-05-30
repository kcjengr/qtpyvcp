
import os
from qtpy import uic
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QDialog, QDialogButtonBox, QApplication

from qtpy.QtDesigner import QDesignerFormWindowInterface


from qtpyvcp.widgets.qtdesigner import _PluginExtension

UI_FILE = os.path.join(os.path.dirname(__file__), "dro_editor.ui")


class DroEditorExtension(_PluginExtension):
    def __init__(self, widget):
        super(DroEditorExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Edit DRO Settings ...", self.editAction)

    def editAction(self, state):
        DroEditor(self.widget, parent=None).exec_()


class DroEditor(QDialog):
    """QDialog for user-friendly editing of DRO properties in Qt Designer."""

    def __init__(self, widget, parent=None):
        super(DroEditor, self).__init__(parent)

        self.widget = widget
        self.app = QApplication.instance()

        uic.loadUi(UI_FILE, self)

        self.axisCombo.setCurrentIndex(self.widget.axisNumber)
        self.refTypCombo.setCurrentIndex(self.widget.referenceType)
        self.inFmtEntry.setText(self.widget.inchFormat)
        self.mmFmtEntry.setText(self.widget.metricFormat)

        bb = self.buttonBox
        bb.button(QDialogButtonBox.Apply).setDefault(True)
        bb.button(QDialogButtonBox.Cancel).setDefault(False)
        bb.button(QDialogButtonBox.Apply).clicked.connect(self.accept)

    @Slot()
    def accept(self):
        """Commit changes"""
        self.setProperty('axisNumber', self.axisCombo.currentIndex())
        self.setProperty('referenceType', self.refTypCombo.currentIndex())
        self.setProperty('inchFormat', self.inFmtEntry.text())
        self.setProperty('metricFormat', self.mmFmtEntry.text())

        self.close()

    def setProperty(self, prop_name, value):
        form = QDesignerFormWindowInterface.findFormWindow(self.widget)
        if form:
            form.cursor().setProperty(prop_name, value)
