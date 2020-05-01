import os

from qtpy.QtWidgets import QComboBox

from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets.dialogs import getDialog


class RecentFileComboBox(QComboBox):
    def __init__(self, parent=None):
        super(RecentFileComboBox, self).__init__(parent)

        self.status = getPlugin('status')

        self.activated.connect(self.onItemActivated)
        self.updateRecentFiles(self.status.recent_files)

        self.insertItem(0, 'No File Loaded', None)
        self.setCurrentIndex(0)
        self.status.recent_files.notify(self.updateRecentFiles)

    def updateRecentFiles(self, recent_files):
        self.clear()
        for file in recent_files:
            self.addItem(os.path.basename(file), file)

        # Add separator and item to launch the file dialog
        self.insertSeparator(len(self.status.recent_files.getValue()))
        self.addItem("Browse for files ...", 'browse_files')

    def onItemActivated(self):
        data = self.currentData()
        if data == 'browse_files':
            getDialog('open_file').show()
        elif data is None:
            pass
        else:
            loadProgram(data)
