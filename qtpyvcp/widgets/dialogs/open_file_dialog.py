
from qtpy import QtCore
from qtpy.QtWidgets import QFileDialog

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.core import Info
INFO = Info()

from qtpyvcp.actions.program_actions import load as loadProgram


class OpenFileDialog(QFileDialog):
    """NGC file chooser dialog."""
    def __init__(self, parent=None):
        super(OpenFileDialog, self).__init__(parent)

        nc_file_dir = INFO.getProgramPrefix()
        nc_file_types = INFO.getQtFilefilter()

        self.setDirectory(nc_file_dir)
        self.setNameFilters(nc_file_types.split(';;'))

        self.setOption(self.DontUseNativeDialog)
        self.setModal(True)

        urls = self.sidebarUrls()
        urls.append(QtCore.QUrl.fromLocalFile(nc_file_dir))
        self.setSidebarUrls(urls)

    def accept(self):
        path = self.selectedFiles()[0]
        stats = QtCore.QFileInfo(path)
        if stats.isDir():
            self.setDirectory(path)
            return
        if not stats.exists():
            return
        loadProgram(path)
        self.hide()
