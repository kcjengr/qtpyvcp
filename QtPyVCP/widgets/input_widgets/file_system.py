import sys
import pyudev
import psutil

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSlot, pyqtProperty, Q_ENUMS, pyqtSignal, QFile, \
    QFileInfo, QDir
from PyQt5.QtWidgets import QFileSystemModel, QTreeView, QWidget, QComboBox, QVBoxLayout, QPushButton, QHBoxLayout, \
    QListView, QTableView

from QtPyVCP.utilities.info import Info



class TableType(object):
    Local = 0
    Remote = 1

    @classmethod
    def toString(cls, tree_type):
        return ['LOCAL', 'REMOTE'][tree_type]


class ComboBoxListModel(QAbstractListModel):
    """
    Class for list management with a QAbstractListModel.
    Implements required virtual methods rowCount() and data().
    Resizeable ListModels must implement insertRows(), removeRows().
    If a nicely labeled header is desired, implement headerData().
    """

    def __init__(self, input_list, parent=None):
        super(ComboBoxListModel, self).__init__(parent)
        self.list_data = []
        self.enabled = []
        for thing in input_list:
            self.append_item(thing)

    def append_item(self, thing):
        ins_row = self.rowCount()
        self.beginInsertRows(QModelIndex(), ins_row, ins_row + 1)
        self.list_data.append(thing)
        self.enabled.append(True)
        self.endInsertRows()

    def remove_item(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self.list_data.pop(row)
        self.enabled.pop(row)
        self.endRemoveRows()

    def set_disabled(self, row):
        self.enabled[row] = False

    def flags(self, idx):
        if self.enabled[idx.row()]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.NoItemFlags

    def rowCount(self, parent=QModelIndex()):
        return len(self.list_data)

    def data(self, idx, data_role):
        return self.list_data[idx.row()]

    def insertRows(self, row, count):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for j in range(row, row + count):
            self.list_data.insert(j, None)
        self.endInsertRows()

    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        for j in range(row, row + count)[::-1]:
            self.list_items.pop(j)
        self.endRemoveRows()

    def headerData(self, section, orientation, data_role):
        return None


class FileSystemTable(QTableView):

    def __init__(self, parent=None):
        super(FileSystemTable, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.info = Info()

        nc_files = self.info.getProgramPrefix()

        self.model = QFileSystemModel()
        self.model.setRootPath(nc_files)
        self.model.setReadOnly(True)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries)

        self.setModel(self.model)

        self.setRootIndex(self.model.index(nc_files))
        self.verticalHeader().hide()


class FileSystem(QWidget, TableType):
    Q_ENUMS(TableType)

    transferFileRequest = pyqtSignal(str)

    def __init__(self, parent=None):
        super(FileSystem, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        self._tree_type = TableType.Local

        self.path_data = dict()

        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.fileSystemTable = FileSystemTable(self)
        self.fileSystemTable.doubleClicked.connect(self.changeRoot)

        if parent is None:
            return

        self.selected_row = None

    def initLocal(self):

        self.clearLayout(self.layout())

        self.vbox.addWidget(self.fileSystemTable)

    def initRemote(self):

        self.clearLayout(self.layout())

        self.deviceList = list()

        self.fileSystemCombo = QComboBox(self)
        self.fileSystemCombo.model = ComboBoxListModel(self.deviceList, self)

        self.fileSystemCombo.setModel(self.fileSystemCombo.model)

        self.refreshfileSystemButton = QPushButton(self)
        self.refreshfileSystemButton.setText("Refresh Devices")

        path_h_box = QHBoxLayout()
        path_h_box.addWidget(self.fileSystemCombo)
        path_h_box.addWidget(self.refreshfileSystemButton)

        self.vbox.addLayout(path_h_box)
        self.vbox.addWidget(self.fileSystemTable)

        self.refreshfileSystemButton.clicked.connect(self.scanUsb)
        self.fileSystemCombo.currentIndexChanged.connect(self.changeRootCombo)

        self.scanUsb()

    def scanUsb(self):

        for i in range(self.fileSystemCombo.model.rowCount()):
            self.fileSystemCombo.model.remove_item(self.fileSystemCombo.currentIndex())

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
                    self.fileSystemCombo.model.append_item(p.mountpoint)

                self.fileSystemCombo.setCurrentIndex(0)

    def changeRoot(self, index):
        new_path = self.fileSystemTable.model.data(index)
        self.fileSystemTable.model.setRootPath(new_path)
        self.fileSystemTable.setRootIndex(index)

    def changeRootCombo(self, value):
        new_path = self.fileSystemCombo.itemText(value)
        self.fileSystemTable.model.setRootPath(new_path)
        self.fileSystemTable.setRootIndex(self.fileSystemTable.model.index(new_path))

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clearLayout(child.layout())

    @pyqtSlot()
    def copyFile(self):
        if self.selected_row:
            self.selected_row = None

    @pyqtSlot()
    def pasteFile(self):
        if self.selected_row:
            # TODO add dialog here
            fileInfo = QFileInfo(self.selected_row)
            if fileInfo.isFile():
                file = QFile(self.selected_row)
                file.remove()

            elif fileInfo.isDir():
                directory = QDir(self.selected_row)
                directory.remove()

    @pyqtSlot()
    def deleteFile(self):
        if self.selected_row:
            # TODO add dialog here
            fileInfo = QFileInfo(self.selected_row)
            if fileInfo.isFile():
                file = QFile(self.selected_row)
                file.remove()

            elif fileInfo.isDir():
                directory = QDir(self.selected_row)
                directory.remove()
    @pyqtSlot()
    def createDirectory(self):
        if self.selected_row:
            # TODO add dialog here
            fileInfo = QFileInfo(self.selected_row)
            if fileInfo.isDir() or fileInfo.isSymLink():
                directory = QDir()
                directory.mkdir("New directory")
            elif fileInfo.isFile():
                directorPath = fileInfo.absolutePath()
                directory = QDir(directorPath)
                directory.mkdir("New directory")

    @pyqtSlot()
    def goUP(self):
        file_info = QFileInfo(self.selected_row)
        directory = file_info.dir()
        new_path = directory.absolutePath()

        currentRoot = self.fileSystemTable.rootIndex()
        self.fileSystemTable.model.setRootPath(new_path)
        self.fileSystemTable.setRootIndex(currentRoot.parent())


    @pyqtSlot()
    def doFileTransfer(self):
        print("DO")
        index = self.fileSystemTable.selectionModel().currentIndex()
        path = self.fileSystemTable.model.filePath(index)
        self.transferFileRequest.emit(path)

    def updateProgress(self, progress):
        """ Updates the progress bar"""
        print("progress")
        # self.progressBar.setValue(progress)

    @pyqtSlot(str)
    def transferFile(self, src_path):
        print("Transfer")
        dest_path = self.fileSystemTable.model.rootPath()

        src_file = QFile()
        src_file.setFileName(src_path)

        src_file_info = QFileInfo(src_path)

        dst_path = "{}/{}".format(dest_path, src_file_info.fileName())

        print(src_path)
        print(dst_path)

        # src_file.bytesWritten.connect(self.updateProgress)

        if src_file.copy(dst_path):
            print("Succes")
        else:
            print("Failed")


    @pyqtSlot()
    def getSelected(self):
        return self.selected_row

    @pyqtSlot()
    def getCurrentDirectory(self):
        return self.fileSystemTable.model.rootPath()

    def _setUpAction(self):
        if self._tree_type == TableType.Local:
            self.initLocal()
        elif self._tree_type == TableType.Remote:
            self.initRemote()

    def getType(self):
        return self._tree_type

    @pyqtSlot(TableType)
    def setType(self, tree_type):
        self._tree_type = tree_type
        self._setUpAction()

    tree_type = pyqtProperty(TableType, getType, setType)
