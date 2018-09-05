import os
import pyudev
import psutil

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSlot, pyqtProperty, Q_ENUMS, pyqtSignal, QFile, \
    QFileInfo, QDir, QIODevice

from PyQt5.QtWidgets import QFileSystemModel, QWidget, QComboBox, QVBoxLayout, QPushButton, QHBoxLayout,\
    QTableView, QMessageBox, QApplication

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

        self.parent = parent

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        self._table_type = TableType.Local

        self.path_data = dict()

        self.vbox = QVBoxLayout()

        self.setLayout(self.vbox)

        self.fileSystemTable = FileSystemTable(self)
        self.fileSystemTable.doubleClicked.connect(self.changeRoot)

        # self._initWidget()

        self.selected_row = None

        self.clipboard = QApplication.clipboard()

    def _initLocal(self):

        self.clearLayout(self.layout())

        self.vbox.addWidget(self.fileSystemTable)

    def _initRemote(self):

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
    def newFile(self):
        path = self.fileSystemTable.model.filePath(self.fileSystemTable.rootIndex())
        new_file = QFile(os.path.join(path, "New File"))
        new_file.open(QIODevice.ReadWrite)



    @pyqtSlot()
    def deleteFile(self):
        index = self.fileSystemTable.selectionModel().currentIndex()
        path = self.fileSystemTable.model.filePath(index)
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
        path = self.fileSystemTable.model.filePath(self.fileSystemTable.rootIndex())
        directory = QDir()
        directory.setPath(path)
        directory.mkpath("New Folder")

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
        index = self.fileSystemTable.selectionModel().currentIndex()
        path = self.fileSystemTable.model.filePath(index)
        self.transferFileRequest.emit(path)

    @pyqtSlot(str)
    def transferFile(self, src_path):
        dest_path = self.fileSystemTable.model.filePath(self.fileSystemTable.rootIndex())

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
        return self.fileSystemTable.model.rootPath()

    def _initWidget(self):
        if self._table_type == TableType.Local:
            self._initLocal()
        elif self._table_type == TableType.Remote:
            self._initRemote()

    def getType(self):
        return self._table_type

    @pyqtSlot(TableType)
    def setType(self, table_type):
        self._table_type = table_type
        self._initWidget()

    table_type = pyqtProperty(TableType, getType, setType)

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
