import sys
import pyudev
import psutil

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSlot, pyqtProperty, Q_ENUMS, pyqtSignal, QFile, \
    QFileInfo, QDir
from PyQt5.QtWidgets import QFileSystemModel, QTreeView, QWidget, QComboBox, QVBoxLayout, QPushButton, QHBoxLayout, \
    QListView

from QtPyVCP.utilities.info import Info


class FileSystemTransferButton(QPushButton):

    def __init__(self, parent=None):
        super(FileSystemTransferButton, self).__init__(parent)

        self.sourceFilePath = None
        self.sourceFileName = None
        self.destinationFilePath = None
        self.destinationFileName = None

        if parent is None:
            return

        self.clicked.connect(self.transferFile)

    @pyqtSlot(str)
    def setSource(self, value):
        fileInfo = QFileInfo(value)

        self.sourceFilePath = fileInfo.absolutePath()
        if fileInfo.isFile():
            self.sourceFileName = fileInfo.fileName()
        else:
            self.sourceFileName = None

    @pyqtSlot(str)
    def setDestination(self, value):
        fileInfo = QFileInfo(value)

        self.destinationFilePath = fileInfo.absolutePath()

        if fileInfo.isFile():
            destination = "{}/{}".format(self.destinationFilePath, self.sourceFileName)

            self.destinationFilePath = destination

    def transferFile(self):

        src_path = "{}/{}".format(self.sourceFilePath, self.sourceFileName)
        dst_path = self.destinationFilePath

        src_file = QFile()

        src_file.setFileName(src_path)

        # src_file.bytesWritten.connect(self.updateProgress)

        if src_file.copy(dst_path):
            print("Succes")
        else:
            print("Failed")

    def updateProgress(self, progress):
        """ Updates the progress bar"""
        print("progress")
        # self.progressBar.setValue(progress)


class TreeType(object):
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


class FileSystemList(QListView):

    def __init__(self, parent=None):
        super(FileSystemList, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.info = Info()

        nc_files = self.info.getProgramPrefix()

        self.model = QFileSystemModel()
        self.model.setRootPath(nc_files)
        self.model.setReadOnly(True)
        self.model.setFilter(QDir.AllDirs | QDir.AllEntries)

        self.setModel(self.model)

        self.setRootIndex(self.model.index(nc_files))


class FileSystem(QWidget, TreeType):
    Q_ENUMS(TreeType)

    def __init__(self, parent=None):
        super(FileSystem, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        self._tree_type = TreeType.Local

        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.fileSystemList = FileSystemList(self)
        self.fileSystemList.clicked.connect(self.on_tree_clicked)
        self.fileSystemList.doubleClicked.connect(self.changeRoot)

        if parent is None:
            return

        self.selected_row = None

    def initLocal(self):

        self.clearLayout(self.layout())

        self.vbox.addWidget(self.fileSystemList)

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
        self.vbox.addWidget(self.fileSystemList)

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
        new_path = self.fileSystemList.model.data(index)

        if index.row() == 0:
            return
        elif index.row() == 1:
            file_info = QFileInfo(new_path)
            directory = file_info.dir()
            new_path = directory.absolutePath()

            currentRoot = self.fileSystemList.rootIndex()
            self.fileSystemList.model.setRootPath(new_path)
            self.fileSystemList.setRootIndex(currentRoot.parent())
        else:
            self.fileSystemList.model.setRootPath(new_path)
            self.fileSystemList.setRootIndex(index)

    def changeRootCombo(self, value):
        new_path = self.fileSystemCombo.itemText(value)
        self.fileSystemList.model.setRootPath(new_path)
        self.fileSystemList.setRootIndex(self.fileSystemList.model.index(new_path))

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
    def getSelected(self):
        return self.selected_row

    def _setUpAction(self):
        if self._tree_type == TreeType.Local:
            self.initLocal()
        elif self._tree_type == TreeType.Remote:
            self.initRemote()

    def getType(self):
        return self._tree_type

    @pyqtSlot(TreeType)
    def setType(self, tree_type):
        self._tree_type = tree_type
        self._setUpAction()

    tree_type = pyqtProperty(TreeType, getType, setType)

    selection = pyqtSignal('QString')

    def on_tree_clicked(self, index):
        self.selected_row = self.fileSystemList.model.filePath(index)
        self.selection.emit(self.selected_row)
