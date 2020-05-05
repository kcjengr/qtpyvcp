from qtpy.QtCore import QUrl, QFileInfo
from qtpy.QtWidgets import QFileDialog

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.widgets import VCPPrimitiveWidget

LOG = getLogger(__name__)

from qtpyvcp.utilities.info import Info
INFO = Info()

from qtpyvcp.actions.program_actions import load as loadProgram


class OpenFileDialog(QFileDialog, VCPPrimitiveWidget):
    """NGC file chooser dialog."""
    def __init__(self, parent=None):
        super(OpenFileDialog, self).__init__(parent)

        self.dm = getPlugin('persistent_data_manager')

        nc_file_dir = INFO.getProgramPrefix()
        nc_file_types = INFO.getQtFilefilter()

        self.setDirectory(nc_file_dir)
        self.setNameFilters(nc_file_types.split(';;'))

        self.setOption(self.DontUseNativeDialog)
        self.setModal(True)

        urls = self.sidebarUrls()
        urls.append(QUrl.fromLocalFile(nc_file_dir))
        self.setSidebarUrls(urls)

    def accept(self):
        path = self.selectedFiles()[0]
        stats = QFileInfo(path)
        if stats.isDir():
            self.setDirectory(path)
            return
        if not stats.exists():
            return
        loadProgram(path)
        self.hide()

    def sidbarUrlsToStringList(self):
        return [qurl.toString() for qurl in self.sidebarUrls()]

    def setSidebarUrlsFromStringList(self, urls):
        if urls is not None:
            self.setSidebarUrls([QUrl(url) for url in urls])

    def initialize(self):
        self.setViewMode(self.dm.getData('app.openFileDialog.viewMode',
                                         OpenFileDialog.Detail))

        urls = self.dm.getData('app.openFileDialog.sidebarUrls')
        self.setSidebarUrlsFromStringList(urls)

    def terminate(self):
        self.dm.setData('app.openFileDialog.viewMode',
                        self.viewMode())

        self.dm.setData('app.openFileDialog.sidebarUrls',
                        self.sidbarUrlsToStringList())
