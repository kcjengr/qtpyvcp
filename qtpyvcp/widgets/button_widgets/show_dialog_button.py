#!/usr/bin/env python

from qtpy.QtCore import Property
from qtpy.QtWidgets import QPushButton, QApplication

import qtpyvcp
from qtpyvcp.widgets import VCPWidget


class ShowDialogButton(QPushButton, VCPWidget):

    def __init__(self, parent=None, dialog_name=''):
        super(ShowDialogButton, self).__init__(parent)

        self.app = QApplication.instance().activeWindow()

        self._dialog_name = dialog_name

        self.clicked.connect(self.showDialog)


    def showDialog(self):
        dialog = qtpyvcp.DIALOGS.get(self._dialog_name)
        if dialog is not None:
            dialog.show()

    @Property(str)
    def dialogName(self):
        return self._dialog_name

    @dialogName.setter
    def dialogName(self, dialog_name):
        self._dialog_name = dialog_name