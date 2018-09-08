import os
import pyudev
import psutil

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSlot, pyqtProperty, \
    Q_ENUMS, pyqtSignal, QFile, QFileInfo, QDir, QIODevice

from PyQt5.QtWidgets import QFileSystemModel, QWidget, QComboBox, \
    QPushButton, QTableView, QMessageBox, QApplication, QAbstractItemView

from QtPyVCP.utilities.info import Info


class TableType(object):
    Local = 0
    Remote = 1

class RemovableDeviceComboBox(QComboBox):
    """
    ComboBox for choosing from a list of removable devices.
    """
    def __init__(self, parent=None):
        super(RemovableDeviceComboBox, self).__init__(parent)
        # self.refreshDeviceList()

    def showPopup(self):
        # refresh the device list just before showing popup
        self.refreshDeviceList()
        super(RemovableDeviceComboBox, self).showPopup()

    @pyqtSlot()
    def refreshDeviceList(self):

        # clear existing items
        self.clear()

        context = pyudev.Context()

        removable = [device for device in context.list_devices(subsystem='block', DEVTYPE='disk') if
                     device.attributes.asstring('removable') == "1"]

        for device in removable:
            partitions = [device.device_node for device in
                          context.list_devices(subsystem='block', DEVTYPE='partition', parent=device)]

            # print("All removable partitions: {}".format(", ".join(partitions)))
            # print("Mounted removable partitions:")
            for p in psutil.disk_partitions():
                if p.device in partitions:
                    # print("  {}: {}".format(p.device, p.mountpoint))
                    # self.model.append_item(p.mountpoint)
                    self.addItem(p.mountpoint, None)

        self.setCurrentIndex(0)

class FileSystemTable(QTableView, TableType):
    Q_ENUMS(TableType)

    transferFileRequest = pyqtSignal(str)

    def __init__(self, parent=None):
        super(FileSystemTable, self).__init__(parent)

        self._table_type = TableType.Local

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.parent = parent
        self.path_data = dict()
        self.doubleClicked.connect(self.changeRoot)
        self.selected_row = None
        self.clipboard = QApplication.clipboard()

        self.model = QFileSystemModel()
        self.model.setReadOnly(True)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries)

        self.setModel(self.model)

        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.info = Info()
        self._nc_file_dir = self.info.getProgramPrefix()
        self.setRootPath(self._nc_file_dir)

    def changeRoot(self, index):
        new_path = self.model.data(index)
        self.model.setRootPath(new_path)
        self.setRootIndex(index)

    @pyqtSlot()
    def newFile(self):
        path = self.model.filePath(self.rootIndex())
        new_file = QFile(os.path.join(path, "New File"))
        new_file.open(QIODevice.ReadWrite)

    @pyqtSlot()
    def deleteFile(self):
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        if path:
            fileInfo = QFileInfo(path)
            if fileInfo.isFile():
                if not self.ask_dialog("Do yo wan't to delete the selected file?"):
                    return
                file = QFile(path)
                file.remove()

            elif fileInfo.isDir():
                if not self.ask_dialog("Do yo wan't to delete the selected directory?"):
                    return
                directory = QDir(path)
                directory.removeRecursively()

    @pyqtSlot()
    def createDirectory(self):
        path = self.model.filePath(self.rootIndex())
        directory = QDir()
        directory.setPath(path)
        directory.mkpath("New Folder")

    @pyqtSlot(str)
    def setRootPath(self, root_path):
        self.model.setRootPath(root_path)
        self.setRootIndex(self.model.index(root_path))

    @pyqtSlot()
    def goUP(self):
        file_info = QFileInfo(self.selected_row)
        directory = file_info.dir()
        new_path = directory.absolutePath()

        currentRoot = self.rootIndex()
        self.model.setRootPath(new_path)
        self.setRootIndex(currentRoot.parent())

    @pyqtSlot()
    def doFileTransfer(self):
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        self.transferFileRequest.emit(path)

    @pyqtSlot(str)
    def transferFile(self, src_path):
        dest_path = self.model.filePath(self.rootIndex())

        src_file = QFile()
        src_file.setFileName(src_path)

        src_file_info = QFileInfo(src_path)

        dst_path = os.path.join(dest_path, src_file_info.fileName())

        src_file.copy(dst_path)

    @pyqtSlot()
    def getSelected(self):
        return self.selected_row

    @pyqtSlot()
    def getCurrentDirectory(self):
        return self.model.rootPath()

    @pyqtProperty(TableType)
    def tableType(self):
        return self._table_type

    @tableType.setter
    def tableType(self, table_type):
        self._table_type = table_type
        if table_type == TableType.Local:
            self.setRootPath(self._nc_file_dir)
        else:
            self.setRootPath('/media/')


    def ask_dialog(self, message):
        box = QMessageBox.question(self.parent,
                                   'Are you sure?',
                                   message,
                                   QMessageBox.Yes,
                                   QMessageBox.No)
        if box == QMessageBox.Yes:
            return True
        else:
            return False
