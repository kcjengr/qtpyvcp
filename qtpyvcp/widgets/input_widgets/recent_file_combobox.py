#!/usr/bin/env python

import os
from qtpy.QtWidgets import QComboBox

from qtpyvcp.plugins import getPlugin
STATUS = getPlugin('status')

# from qtpyvcp.utilities import action
from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.widgets.dialogs.open_file_dialog import OpenFileDialog

class RecentFileComboBox(QComboBox):
    def __init__(self, parent=None):
        super(RecentFileComboBox, self).__init__(parent)

        self.file_dialog = OpenFileDialog()

        self.activated.connect(self.onItemActivated)
        self.updateRecentFiles(STATUS.recent_files)

        self.insertItem(0, 'No File Loaded', None)
        self.setCurrentIndex(0)
        STATUS.recent_files.notify(self.updateRecentFiles)

    def updateRecentFiles(self, recent_files):
        self.clear()
        for file in recent_files:
            self.addItem(os.path.basename(file), file)

        # Add separator and item to launch the file dialog
        self.insertSeparator(len(STATUS.recent_files.getValue()))
        self.addItem("Browse for files ...", 'browse_files')

    def onItemActivated(self):
        data = self.currentData()
        if data == 'browse_files':
            self.file_dialog.show()
        elif data is None:
            pass
        else:
            loadProgram(data)
