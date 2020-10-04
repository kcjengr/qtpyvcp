import os
import subprocess

import linuxcnc
import psutil

from pyudev.pyqt5 import MonitorObserver
from pyudev import Context, Monitor, Devices

from qtpy.QtCore import Slot, Property, Signal, QFile, QFileInfo, QDir, QIODevice
from qtpy.QtWidgets import QFileSystemModel, QComboBox, QTableView, QMessageBox, \
    QApplication, QAbstractItemView, QInputDialog, QLineEdit

from qtpyvcp.plugins import getPlugin
from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.lib.decorators import deprecated


LOG = getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER') != None


class TableType(object):
    Local = 0
    Remote = 1


class RemovableDeviceComboBox(QComboBox):
    """ComboBox for choosing from a list of removable devices."""
    usbPresent = Signal(bool)
    currentPathChanged = Signal(str)
    currentDeviceEjectable = Signal(bool)

    def __init__(self, parent=None):
        super(RemovableDeviceComboBox, self).__init__(parent)

        self._first_show = True

        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self._file_locations = getPlugin('file_locations')
        self._file_locations.removable_devices.notify(self.onRemovableDevicesChanged)
        self._file_locations.new_device.notify(self.onNewDeviceAdded)

        self.info = Info()
        self._program_prefix = self.info.getProgramPrefix()

        self.currentTextChanged.connect(self.onCurrentTextChanged)

        # initialize device list
        self.onRemovableDevicesChanged(self._file_locations.removable_devices.value)

    def showEvent(self, event=None):
        if self._first_show:
            self._first_show = False
            self.setCurrentText(self._file_locations.default_location)
            data = self.currentData() or {}
            self.currentDeviceEjectable.emit(data.get('removable', False))
        super(RemovableDeviceComboBox, self).showEvent(event)

    def onCurrentTextChanged(self, text):
        data = self.currentData()
        if data:
            self.currentPathChanged.emit(data.get('path', '/'))
            self.currentDeviceEjectable.emit(data.get('removable', False))

    def onRemovableDevicesChanged(self, devices):

        self.blockSignals(True)

        self.clear()

        for label, path in self._file_locations.local_locations.items():
            self.addItem(label, {'path': os.path.expanduser(path)})

        self.insertSeparator(100)

        if devices:
            for devices_node, device_data in devices.items():
                self.addItem(device_data.get('label', 'Unknown'), device_data)

        self.blockSignals(False)

    def onNewDeviceAdded(self, device):
        if device:
            self.setCurrentText(device.get('label'))
        else:
            self.setCurrentText(self._file_locations.default_location)

    @Slot()
    def ejectDevice(self):
        data = self.currentData()
        if data:
            self._file_locations.ejectDevice(data.get('device'))

class FileSystemTable(QTableView, TableType):

    if IN_DESIGNER:
        from PyQt5.QtCore import Q_ENUMS
        Q_ENUMS(TableType)

    gcodeFileSelected = Signal(bool)
    filePreviewText = Signal(str)
    fileNamePreviewText = Signal(str)
    transferFileRequest = Signal(str)
    rootChanged = Signal(str)
    atDeviceRoot = Signal(bool)

    def __init__(self, parent=None):
        super(FileSystemTable, self).__init__(parent)

        self._table_type = TableType.Local
        self._hidden_columns = ''

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.parent = parent
        self.path_data = dict()

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

        # open selected item on double click or enter pressed
        self.activated.connect(self.openSelectedItem)

        self.info = Info()
        self.nc_file_editor = self.info.getEditor()
        self.nc_file_dir = self.info.getProgramPrefix()
        self.nc_file_exts = self.info.getProgramExtentions()

        self.setRootPath(self.nc_file_dir)

        self.model.rootPathChanged.connect(self.onRootPathChanged)

    def showEvent(self, event=None):
        root_path = self.model.rootPath()
        self.rootChanged.emit(root_path)
        self.atDeviceRoot.emit(os.path.ismount(root_path))

    def onRootPathChanged(self, path):
        self.atDeviceRoot.emit(os.path.ismount(path))

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
            self.fileNamePreviewText.emit(path)
        else:
            self.gcodeFileSelected.emit(False)
            self.filePreviewText.emit('')
            self.fileNamePreviewText.emit('')

    @Slot()
    def openSelectedItem(self, index=None):
        """If ngc file, opens in LinuxCNC, if dir displays dir."""
        if index is None:
            selection = self.getSelection()
            if selection is None:
                return
            index = selection[0]

        path = self.model.filePath(self.rootIndex())
        name = self.model.filePath(index)

        absolute_path = os.path.join(path, name)

        file_info = QFileInfo(absolute_path)
        if file_info.isDir():
            self.model.setRootPath(absolute_path)
            self.setRootIndex(self.model.index(absolute_path))
            self.rootChanged.emit(absolute_path)

        elif file_info.isFile():
            # if file_info.completeSuffix() not in self.nc_file_exts:
            #     LOG.warn("Unsuported NC program type with extention .%s",
            #              file_info.completeSuffix())
            loadProgram(absolute_path)

    @Slot()
    def editSelectedFile(self):
        """Open the selected file in editor."""
        selection = self.getSelection()
        if selection is not None:
            path = self.model.filePath(selection[0])
            subprocess.Popen([self.nc_file_editor, path])
        return False

    @Slot()
    def loadSelectedFile(self):
        """Loads the selected file into LinuxCNC."""
        selection = self.getSelection()
        if selection is not None:
            path = self.model.filePath(selection[0])
            loadProgram(path)
            return True
        return False

    @Slot()
    def selectPrevious(self):
        """Select the previous item in the view."""
        selection = self.getSelection()
        if selection is None:
            # select last item in view
            self.selectRow(self.model.rowCount(self.rootIndex()) - 1)
        else:
            self.selectRow(selection[0].row() - 1)
        return True

    @Slot()
    def selectNext(self):
        """Select the next item in the view."""
        selection = self.getSelection()
        if selection is None:
            # select first item in view
            self.selectRow(0)
        else:
            self.selectRow(selection[-1].row() + 1)
        return True

    @Slot()
    def rename(self):
        """renames the selected file or folder"""
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        if path:
            file_info = QFileInfo(path)

            if file_info.isFile():
                filename = self.rename_dialog("file")

                if filename:
                    q_file = QFile(path)
                    file_info.absolutePath()
                    new_path = os.path.join(file_info.absolutePath(), str(filename))
                    q_file.rename(new_path)

            elif file_info.isDir():
                filename = self.rename_dialog("directory")

                if filename:
                    directory = QDir(path)
                    file_info.absolutePath()
                    new_path = os.path.join(file_info.absolutePath(), str(filename))
                    directory.rename(path, new_path)

    @Slot()
    def newFile(self):
        """Create a new empty file"""
        path = self.model.filePath(self.rootIndex())
        new_file_path = os.path.join(path, "New File.ngc")

        count = 1
        while os.path.exists(new_file_path):
            new_file_path = os.path.join(path, "New File {}.ngc".format(count))
            count += 1

        new_file = QFile(new_file_path)
        new_file.open(QIODevice.ReadWrite)

    @Slot()
    def newFolder(self):
        path = self.model.filePath(self.rootIndex())

        new_name = 'New Folder'

        count = 1
        while os.path.exists(os.path.join(path, new_name)):
            new_name = "New Folder {}".format(count)
            count += 1

        directory = QDir(path)
        directory.mkpath(new_name)
        directory.setPath(new_name)

    @Slot()
    @deprecated(replaced_by='newFolder',
                reason='for consistency with newFile method name')
    def createDirectory(self):
        self.newFolder()

    @Slot()
    def deleteItem(self):
        """Delete the selected item (either a file or folder)."""
        # ToDo: use Move2Trash, instead of deleting the file
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        if path:
            file_info = QFileInfo(path)
            if file_info.isFile():
                if not self.ask_dialog("Do you wan't to delete the selected file?"):
                    return
                q_file = QFile(path)
                q_file.remove()

            elif file_info.isDir():
                if not self.ask_dialog("Do you wan't to delete the selected directory?"):
                    return
                directory = QDir(path)
                directory.removeRecursively()

    @Slot()
    @deprecated(replaced_by='deleteItem',
                reason='because of unclear method name')
    def deleteFile(self):
        self.deleteItem()

    @Slot(str)
    def setRootPath(self, root_path):
        """Sets the currently displayed path."""

        self.rootChanged.emit(root_path)
        self.model.setRootPath(root_path)
        self.setRootIndex(self.model.index(root_path))

        return True

    @Slot()
    def viewParentDirectory(self):
        """View the parent directory of the current view."""

        path = self.model.filePath(self.rootIndex())

        file_info = QFileInfo(path)
        directory = file_info.dir()
        new_path = directory.absolutePath()

        if os.path.ismount(path):
            return

        currentRoot = self.rootIndex()

        self.model.setRootPath(new_path)
        self.setRootIndex(currentRoot.parent())
        self.rootChanged.emit(new_path)


    @Slot()
    @deprecated(replaced_by='viewParentDirectory')
    def goUP(self):
        self.viewParentDirecotry()

    @Slot()
    def viewHomeDirectory(self):
        self.setRootPath(os.path.expanduser('~/'))

    @Slot()
    def viewNCFilesDirectory(self):
        # ToDo: Make preset user definable
        path = os.path.expanduser(self._nc_files_dir)
        self.setRootPath(path)

    @Slot()
    def viewPresetDirectory(self):
        # ToDo: Make preset user definable
        preset = os.path.expanduser(self._nc_files_dir)
        self.setRootPath(preset)

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
    def getSelection(self):
        """Returns list of selected indexes, or None."""
        selection = self.selection_model.selectedIndexes()
        if len(selection) == 0:
            return None
        return selection

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
            self.setRootPath(self.nc_file_dir)
        else:
            self.setRootPath('/media/')

    @Property(str)
    def hiddenColumns(self):
        """String of comma separated column numbers to hide."""
        return self._hidden_columns

    @hiddenColumns.setter
    def hiddenColumns(self, columns):
        try:
            col_list = [int(c) for c in columns.split(',') if c != '']
        except:
            return False

        self._hidden_columns = columns

        header = self.horizontalHeader()
        for col in range(4):
            if col in col_list:
                header.hideSection(col)
            else:
                header.showSection(col)

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

    def rename_dialog(self, data_type):
        text, ok_pressed = QInputDialog.getText(self.parent, "Rename", "New {} name:".format(data_type),
                                                QLineEdit.Normal, "")

        if ok_pressed and text != '':
            return text
        else:
            return False
