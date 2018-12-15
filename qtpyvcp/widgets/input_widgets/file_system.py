import os
import pyudev
import psutil

from qtpy.QtCore import Slot, Property, Signal, QFile, QFileInfo, QDir, QIODevice
from qtpy.QtWidgets import QFileSystemModel, QComboBox, QTableView, QMessageBox, \
    QApplication, QAbstractItemView

from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.utilities.info import Info

IN_DESIGNER = os.getenv('DESIGNER') != None

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

    def showEvent(self, event=None):
        self.refreshDeviceList()

    def showPopup(self):
        # refresh the device list just before showing popup
        self.refreshDeviceList()
        super(RemovableDeviceComboBox, self).showPopup()

    @Slot()
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
                    self.addItem(p.mountpoint, p.device)

        if not self.count():
            self.addItem("No Devide Found", "NONONONONO")

        self.setCurrentIndex(0)

    @Slot()
    def ejectDevice(self):
        mount_point = self.currentData()

        if mount_point == "NONONONONO":
            return

        os.system("udisksctl unmount --block-device {}".format(mount_point))
        os.system("udisksctl power-off --block-device {}".format(mount_point))

        self.refreshDeviceList()

        self.setCurrentIndex(0)


class FileSystemTable(QTableView, TableType):

    if IN_DESIGNER:
        from PyQt5.QtCore import Q_ENUMS
        Q_ENUMS(TableType)


    gcodeFileSelected = Signal(bool)
    filePreviewText = Signal(str)
    transferFileRequest = Signal(str)
    rootChanged = Signal(str)

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

        self.selection_model = self.selectionModel()
        self.selection_model.selectionChanged.connect(self.onSelectionChanged)

        self.info = Info()
        self._nc_file_dir = self.info.getProgramPrefix()
        self.nc_file_exts = self.info.getProgramExtentions()
        self.setRootPath(self._nc_file_dir)

    def showEvent(self, event=None):
        self.rootChanged.emit(self._nc_file_dir)

    def onSelectionChanged(self, selected, deselected):

        if len(selected) == 0:
            return

        index = selected.indexes()[0]
        path = self.model.filePath(index)

        if os.path.isfile(path):
            self.gcodeFileSelected.emit(True)
            with open(path, 'r') as fh:
                content = fh.read()
            self.filePreviewText.emit(content)
        else:
            self.gcodeFileSelected.emit(False)
            self.filePreviewText.emit('')

    def changeRoot(self, index):

        path = self.model.filePath(self.rootIndex())
        new_path = self.model.filePath(index)

        absolute_path = os.path.join(path, new_path)

        file_info = QFileInfo(absolute_path)
        if file_info.isDir():
            self.model.setRootPath(absolute_path)
            self.setRootIndex(self.model.index(absolute_path))

            self.rootChanged.emit(absolute_path)

        elif file_info.isFile():
            print self.nc_file_exts
            print absolute_path
            # if os.path.splitext(new_path)[1] in self.nc_file_exts:
            #     print absolute_path
            loadProgram(absolute_path)

    @Slot()
    def loadSelectedFile(self):
        selection = self.selection_model.selectedIndexes()
        if len(selection) == 0:
            return

        path = self.model.filePath(selection[0])
        loadProgram(path)

    @Slot()
    def newFile(self):
        path = self.model.filePath(self.rootIndex())
        new_file = QFile(os.path.join(path, "New File"))
        new_file.open(QIODevice.ReadWrite)

    @Slot()
    def deleteFile(self):
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        if path:
            fileInfo = QFileInfo(path)
            if fileInfo.isFile():
                if not self.ask_dialog("Do you wan't to delete the selected file?"):
                    return
                file = QFile(path)
                file.remove()

            elif fileInfo.isDir():
                if not self.ask_dialog("Do you wan't to delete the selected directory?"):
                    return
                directory = QDir(path)
                directory.removeRecursively()

    @Slot()
    def createDirectory(self):
        path = self.model.filePath(self.rootIndex())
        directory = QDir()
        directory.setPath(path)
        directory.mkpath("New Folder")

    @Slot(str)
    def setRootPath(self, root_path):

        self.rootChanged.emit(root_path)
        self.model.setRootPath(root_path)
        self.setRootIndex(self.model.index(root_path))

        return True

    @Slot()
    def goUP(self):

        path = self.model.filePath(self.rootIndex())

        file_info = QFileInfo(path)
        directory = file_info.dir()
        new_path = directory.absolutePath()

        currentRoot = self.rootIndex()

        self.model.setRootPath(new_path)
        self.setRootIndex(currentRoot.parent())
        self.rootChanged.emit(new_path)

    @Slot()
    def doFileTransfer(self):
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        self.transferFileRequest.emit(path)

    @Slot(str)
    def transferFile(self, src_path):
        dest_path = self.model.filePath(self.rootIndex())

        src_file = QFile()
        src_file.setFileName(src_path)

        src_file_info = QFileInfo(src_path)

        dst_path = os.path.join(dest_path, src_file_info.fileName())

        src_file.copy(dst_path)

    @Slot()
    def getSelected(self):
        return self.selected_row

    @Slot()
    def getCurrentDirectory(self):
        return self.model.rootPath()

    @Property(TableType)
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
