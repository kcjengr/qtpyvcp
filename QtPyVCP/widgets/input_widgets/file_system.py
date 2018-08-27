import sys
from PyQt5.QtWidgets import QFileSystemModel, QTreeView
from QtPyVCP.utilities.info import Info


class FileSystem(QTreeView):

    def __init__(self, parent=None):
        super(FileSystem, self).__init__(parent)

        self.info = Info()

        nc_files = self.info.getProgramPrefix()

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.model = QFileSystemModel()
        self.model.setRootPath(nc_files)
        self.model.setReadOnly(False)

        self.setModel(self.model)

        self.setRootIndex(self.model.index(nc_files))

        self.setAnimated(False)
        self.setIndentation(20)
        self.setSortingEnabled(True)
