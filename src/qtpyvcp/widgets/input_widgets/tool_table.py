from PySide6.QtCore import Qt, Slot, Signal, Property, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QColor, QBrush
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QTableView, QStyledItemDelegate, QDoubleSpinBox, \
     QSpinBox, QLineEdit, QMessageBox

from qtpyvcp.actions.machine_actions import issue_mdi

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import connectSetting, getSetting
from qtpyvcp.plugins.db_tool_table import DBToolTable
from qtpyvcp.actions import IN_DESIGNER

LOG = getLogger(__name__)


class ItemDelegate(QStyledItemDelegate):

    def __init__(self, columns):
        super(ItemDelegate, self).__init__()

        self._columns = columns
        self._padding = ' ' * 2

    def setColumns(self, columns):
        self._columns = columns

    def displayText(self, value, locale):

        if type(value) == float:
            return f"{value:.4f}"
        if type(value) == str:
            return f"{self._padding}{value}"

        return f"{self._padding}{value}"

    def createEditor(self, parent, option, index):
        # ToDo: set dec placed for IN and MM machines
        col = self._columns[index.column()]

        if col == 'R':
            editor = QLineEdit(parent)
            editor.setFrame(False)
            margins = editor.textMargins()
            padding = editor.fontMetrics().width(self._padding) + 1
            margins.setLeft(margins.left() + padding)
            editor.setTextMargins(margins)
            return editor

        elif col in 'TPQ':
            editor = QSpinBox(parent)
            editor.setFrame(False)
            editor.setAlignment(Qt.AlignCenter)
            if col == 'Q':
                editor.setMaximum(9)
            else:
                editor.setMaximum(99999)
            return editor

        elif col in 'XYZABCUVWD':
            editor = QDoubleSpinBox(parent)
            editor.setFrame(False)
            editor.setAlignment(Qt.AlignCenter)
            editor.setDecimals(4)
            # editor.setStepType(QSpinBox.AdaptiveDecimalStepType)
            editor.setProperty('stepType', 1)  # stepType was added in 5.12

            min_range = getSetting('offset_table.min_range').value
            max_range = getSetting('offset_table.max_range').value

            if min_range and max_range:
                editor.setRange(min_range, max_range)
            else:
                editor.setRange(-1000, 1000)

            return editor

        elif col in 'IJ':
            editor = QDoubleSpinBox(parent)
            editor.setFrame(False)
            editor.setAlignment(Qt.AlignCenter)
            editor.setMaximum(360.0)
            editor.setMinimum(0.0)
            editor.setDecimals(4)
            # editor.setStepType(QSpinBox.AdaptiveDecimalStepType)
            editor.setProperty('stepType', 1)  # stepType was added in 5.12
            return editor

        return None


class ToolModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(ToolModel, self).__init__(parent)

        if IN_DESIGNER:
            return
        self.status = getPlugin('status')
        self.stat = self.status.stat
        self.tt = getPlugin('tooltable')

        self.current_tool_color = QColor(Qt.darkGreen)
        self.current_tool_bg = None

        self._columns = self.tt.columns
        self._column_labels = self.tt.COLUMN_LABELS

        self._tool_table = self.tt.getToolTable()

        self.setColumnCount(self.columnCount())
        self.setRowCount(1000)  # (self.rowCount())

        self.status.tool_in_spindle.notify(self.refreshModel)
        self.tt.tool_table_changed.connect(self.updateModel)
        
        self.row_offset = 1
        tool_table = getPlugin("tooltable")
        if isinstance(tool_table, DBToolTable):
            self.row_offset = 0


    def refreshModel(self):
        # refresh model so current tool gets highlighted
        self.beginResetModel()
        self.endResetModel()

    def updateModel(self, tool_table):
        # update model with new data
        self.beginResetModel()
        self._tool_table = tool_table
        self.endResetModel()

    def setColumns(self, columns):
        self._columns = columns
        self.setColumnCount(len(columns))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._column_labels[self._columns[section]]

        return QStandardItemModel.headerData(self, section, orientation, role)

    def columnCount(self, parent=None):
        return len(self._columns)

    def rowCount(self, parent=None):
        return len(self._tool_table) - 1


    def flags(self, index):
        
        row = index.row()
        col = index.column()
            
        header_text = self.headerData(col, Qt.Horizontal, Qt.DisplayRole)
        
        tnum = sorted(self._tool_table)[row + self.row_offset]
        
        # check tool in spindle and make Tool No. read-only
        if tnum == self.stat.tool_in_spindle and header_text == "Tool":
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
    

    def data(self, index, role=Qt.DisplayRole):
        

        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            key = self._columns[index.column()]
            tnum = sorted(self._tool_table)[index.row() +self.row_offset]
            return self._tool_table[tnum][key]

        elif role == Qt.TextAlignmentRole:
            col = self._columns[index.column()]
            if col == 'R':      # Remark
                return Qt.AlignVCenter | Qt.AlignLeft
            elif col in 'TPQ':  # Integers (Tool, Pocket, Orient)
                return Qt.AlignVCenter | Qt.AlignCenter
            else:               # All the other floats
                return Qt.AlignVCenter | Qt.AlignRight

        elif role == Qt.ForegroundRole:
            tnum = sorted(self._tool_table)[index.row() + self.row_offset]
            if self.stat.tool_in_spindle == tnum:
                return QBrush(self.current_tool_color)
            else:
                return QStandardItemModel.data(self, index, role)

        elif role == Qt.BackgroundRole and self.current_tool_bg is not None:
            tnum = sorted(self._tool_table)[index.row() + self.row_offset]
            if self.stat.tool_in_spindle == tnum:
                return QBrush(self.current_tool_bg)
            else:
                return QStandardItemModel.data(self, index, role)

        return QStandardItemModel.data(self, index, role)

    def setData(self, index, value, role):
        key = self._columns[index.column()]
        tnum = sorted(self._tool_table)[index.row() + self.row_offset]
        self._tool_table[tnum][key] = value
        return True

    def removeTool(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        tnum = sorted(self._tool_table)[row + self.row_offset]
        del self._tool_table[tnum]
        self.endRemoveRows()
        return True

    def addTool(self):
        try:
            tnum = sorted(self._tool_table)[-1] + self.row_offset
        except IndexError:
            tnum = 1

        row = len(self._tool_table) - 1

        if row == 1000:
            # max 1000 tools
            return False

        self.beginInsertRows(QModelIndex(), row, row)
        self._tool_table[tnum] = self.tt.newTool(tnum=tnum)
        self.endInsertRows()
        return True

    def toolDataFromRow(self, row):
        """Returns dictionary of tool data"""
        tnum = sorted(self._tool_table)[row + self.row_offset]
        return self._tool_table[tnum]

    def saveToolTable(self):
        self.tt.saveToolTable(self._tool_table, self._columns)
        return True

    def clearToolTable(self):
        self.beginRemoveRows(QModelIndex(), 0, 100)
        # delete all but the spindle, which can't be deleted
        self._tool_table = {0: self._tool_table[0]}
        self.endRemoveRows()
        return True

    def loadToolTable(self):
        # the tooltable plugin will emit the tool_table_changed signal
        # so we don't need to do any more here
        self.tt.loadToolTable()
        return True


class ToolTable(QTableView):
    toolSelected = Signal(int)

    def __init__(self, parent=None):
        super(ToolTable, self).__init__(parent)

        self.clicked.connect(self.onClick)

        self.tool_model = ToolModel(self)

        self.item_delegate = ItemDelegate(columns=self.tool_model._columns)
        self.setItemDelegate(self.item_delegate)

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setSourceModel(self.tool_model)

        self.setModel(self.proxy_model)

        # Properties
        self._columns = self.tool_model._columns
        self._confirm_actions = False
        self._current_tool_color = QColor('sage')
        self._current_tool_bg = None

        # Appearance/Behaviour settings
        self.setSortingEnabled(True)
        self.verticalHeader().hide()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)

    @Slot()
    def saveToolTable(self):
        if not self.confirmAction("Do you want to save changes and\n"
                                  "load tool table into LinuxCNC?"):
            return
        self.tool_model.saveToolTable()

    @Slot()
    def loadToolTable(self):
        if not self.confirmAction("Do you want to re-load the tool table?\n"
                                  "All unsaved changes will be lost."):
            return
        self.tool_model.loadToolTable()

    @Slot()
    def deleteSelectedTool(self):
        """Delete the currently selected item"""
        current_row = self.selectedRow()
        if current_row == -1:
            # no row selected
            return

        tdata = self.tool_model.toolDataFromRow(current_row)
        tnum = tdata['T']

        # should not delete tool if currently loaded in spindle. Warn user
        if tnum == self.tool_model.stat.tool_in_spindle:

            box = QMessageBox(QMessageBox.Warning,
                              "Can't delete current tool!",
                              "Tool #{} is currently loaded in the spindle.\n"
                              "Please remove tool from spindle and try again.".format(tnum),
                              QMessageBox.Ok,
                              parent=self)
            box.show()
            return False

        if not self.confirmAction('Are you sure you want to delete T{tdata[T]}?\n'
                                  '"{tdata[R]}"'.format(tdata=tdata)):
            return

        self.tool_model.removeTool(current_row)

    @Slot()
    def selectPrevious(self):
        """Select the previous item in the view."""
        self.selectRow(self.selectedRow() - 1)
        return True

    @Slot()
    def selectNext(self):
        """Select the next item in the view."""
        self.selectRow(self.selectedRow() + 1)
        return True

    @Slot()
    def clearToolTable(self, confirm=True):
        """Remove all items from the model"""
        if confirm:
            if not self.confirmAction("Do you want to delete the whole tool table?"):
                return

        self.tool_model.clearToolTable()

    @Slot()
    def addTool(self):
        """Appends a new item to the model"""
        self.tool_model.addTool()
        self.selectRow(self.tool_model.rowCount() - 1)

    @Slot()
    def loadSelectedTool(self):
        """Loads the currently selected tool"""
        # see: https://forum.linuxcnc.org/41-guis/36042?start=50#151820
        current_row = self.selectedRow()
        if current_row == -1:
            # no row selected
            return

        tnum = self.tool_model.toolDataFromRow(current_row)['T']
        issue_mdi("T%s M6" % tnum)

    def selectedRow(self):
        """Returns the row number of the currently selected row, or 0"""
        tool_no = self.selectionModel().currentIndex().row()
        return tool_no

    def onClick(self, index):
        row = index.row()
        tnum = self.tool_model.toolDataFromRow(row)['T']

        self.toolSelected.emit(tnum)

    def confirmAction(self, message):
        if not self._confirm_actions:
            return True

        box = QMessageBox.question(self,
                                   'Confirm Action',
                                   message,
                                   QMessageBox.Yes,
                                   QMessageBox.No)

        if box == QMessageBox.Yes:
            return True
        else:
            return False

    @Property(bool)
    def confirmActions(self):
        return self._confirm_actions

    @confirmActions.setter
    def confirmActions(self, confirm):
        self._confirm_actions = confirm

    @Property(QColor)
    def currentToolColor(self):
        return self.tool_model.current_tool_color

    @currentToolColor.setter
    def currentToolColor(self, color):
        self.tool_model.current_tool_color = color

    @Property(QColor)
    def currentToolBackground(self):
        return self.tool_model.current_tool_bg or QColor()

    @currentToolBackground.setter
    def currentToolBackground(self, color):
        self.tool_model.current_tool_bg = color

    @Property(int)
    def currentRow(self):
        return self.selectedRow()

    @currentRow.setter
    def currentRow(self, row):
        self.selectRow(row)

    def insertToolAbove(self):
        # it does not make sense to insert tools, since the numbering
        # of all the other tools would have to change.
        self.addTool()
        raise DeprecationWarning("insertToolAbove() will be removed in "
                                 "the future, use addTool() instead")

    def insertToolBelow(self):
        self.addTool()
        raise DeprecationWarning("insertToolBelow() will be removed in "
                                 "the future, use addTool() instead")
