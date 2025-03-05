#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

import os

from PySide6.QtCore import Qt, Slot, Property, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QColor, QBrush
from PySide6.QtWidgets import QTableView, QHeaderView, QStyledItemDelegate, QDoubleSpinBox, QMessageBox

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import connectSetting, getSetting

STATUS = getPlugin('status')
LOG = getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)


class ItemDelegate(QStyledItemDelegate):

    def __init__(self, columns):
        super(ItemDelegate, self).__init__()

        self._columns = columns
        self._padding = ' ' * 2

    def setColumns(self, columns):
        self._columns = columns

    def displayText(self, value, locale):

        if type(value) == float:
            return "{0:.4f}".format(value)

        return "{}{}".format(self._padding, value)

    def createEditor(self, parent, option, index):
        # ToDo: set dec placed for IN and MM machines
        col = self._columns[index.column()]

        if col in 'XYZABCUVWR':
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

        return None


class OffsetModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(OffsetModel, self).__init__(parent)

        self.ot = getPlugin('offsettable')

        self.current_row_color = QColor(Qt.darkGreen)
        self.current_row_bg = None  # Add this line

        if IN_DESIGNER:
            return 
        
        self._columns = self.ot.columns
        self._rows = self.ot.rows

        self._column_labels = self.ot.COLUMN_LABELS
        self._row_labels = self.ot.ROW_LABELS

        self._offset_table = self.ot.getOffsetTable()

        self.setColumnCount(len(self._columns))
        self.setRowCount(len(self._rows))  # (self.rowCount())

        self.ot.offset_table_changed.connect(self.updateModel)

    def refreshModel(self):
        # refresh model so current row gets highlighted
        self.beginResetModel()
        self.endResetModel()

    def updateModel(self, offset_table):
        # update model with new data
        if len(offset_table) == 0:
            LOG.warn("Offset Table update is zero length - skip it")
            return
        
        self.beginResetModel()
        self._offset_table = offset_table
        self.endResetModel()

    def setColumns(self, columns):
        self._columns = columns
        self.setColumnCount(len(columns))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._columns[section]
        elif role == Qt.DisplayRole and orientation == Qt.Vertical:
            return self._row_labels[section]

        return QStandardItemModel.headerData(self, section, orientation, role)

    def columnCount(self, parent=None):
        if IN_DESIGNER:
            return 0
        return len(self._columns)

    def rowCount(self, parent=None):
        if IN_DESIGNER:
            return 0
        return len(self._rows)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if (role == Qt.DisplayRole or role == Qt.EditRole) and len(self._offset_table) > 0:
            columns_index = index.column()
            rows_index = index.row()

            # column_index = self._columns[index.column()]
            # index_column = self._column_labels.index(column_index)

            return self._offset_table[rows_index][columns_index]

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter | Qt.AlignRight

        elif role == Qt.ForegroundRole:

            offset = index.row() + 1

            if self.ot.current_index == offset:

                return QBrush(self.current_row_color)

            else:

                return QStandardItemModel.data(self, index, role)

        elif role == Qt.BackgroundRole and self.current_row_bg is not None:  # Add this block
            offset = index.row() + 1
            if self.ot.current_index == offset:
                return QBrush(self.current_row_bg)
            else:
                return QStandardItemModel.data(self, index, role)

        return QStandardItemModel.data(self, index, role)

    def setData(self, index, value, role):
        columns_index = index.column()
        rows_index = index.row()

        # column_index = self._columns[index.column()]
        # index_column = self._column_labels.index(column_index)

        self._offset_table[rows_index][columns_index] = value

        return True

    def clearRow(self, row):

        for col in range(len(self._columns)):
            # index_column = self._column_labels.index(self._columns[col])
            self._offset_table[row][col] = 0.0

        self.refreshModel()

    def clearRows(self):

        for row in range(len(self._rows)):
            for col in range(len(self._columns)):
                # index_column = self._column_labels.index(self._columns[col])
                self._offset_table[row][col] = 0.0

        self.refreshModel()

    def offsetDataFromRow(self, row):
        o_num = sorted(self._offset_table)[row]
        return self._offset_table[o_num]

    def saveOffsetTable(self):
        self.ot.saveOffsetTable(self._offset_table, columns=self._columns)
        return True

    def loadOffsetTable(self):
        # the tooltable plugin will emit the tool_table_changed signal
        # so we don't need to do any more here
        self.ot.loadOffsetTable()
        return True


class OffsetTable(QTableView):
    def __init__(self, parent=None):
        super(OffsetTable, self).__init__(parent)

        self.setEnabled(False)

        self.offset_model = OffsetModel(self)

        # Properties
        self._current_row_color = QColor('sage')
        if not IN_DESIGNER:
            self._columns = self.offset_model._columns
        self._confirm_actions = False
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setSourceModel(self.offset_model)

        if not IN_DESIGNER:
            self.item_delegate = ItemDelegate(columns=self._columns)
            self.setItemDelegate(self.item_delegate)

        self.setModel(self.proxy_model)

        # Appearance/Behaviour settings
        self.setSortingEnabled(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        if IN_DESIGNER:
            return
        STATUS.all_axes_homed.notify(self.handle_home_signal)

    def handle_home_signal(self, all_axes):
        if all_axes:
            self.setEnabled(True)
        else:
            self.setEnabled(False)

    @Slot()
    def saveOffsetTable(self):

        if self.isEnabled():
            if not self.confirmAction("Do you want to save changes and\n"
                                      "load offset table into LinuxCNC?"):
                return
            self.offset_model.saveOffsetTable()

    @Slot()
    def loadOffsetTable(self):
        if not self.confirmAction("Do you want to re-load the offset table?\n"
                                  "All unsaved changes will be lost."):
            return
        self.offset_model.loadOffsetTable()

    @Slot()
    def deleteSelectedOffset(self):
        """Delete the currently selected item"""
        current_row = self.selectedRow()
        if current_row == -1:
            # no row selected
            return

        if not self.confirmAction("Are you sure you want to delete offset {}?".format(current_row)):
            return

        self.offset_model.clearRow(current_row)

    # @Slot()
    # def selectPrevious(self):
    #     """Select the previous item in the view."""
    #     self.selectRow(self.selectedRow() - 1)
    #     return True

    # @Slot()
    # def selectNext(self):
    #     """Select the next item in the view."""
    #     self.selectRow(self.selectedRow() + 1)
    #     return True

    @Slot()
    def clearOffsetTable(self, confirm=True):
        """Remove all items from the model"""
        if confirm:
            if not self.confirmAction("Do you want to delete the whole offsets table?"):
                return

        self.offset_model.clearRows()

    def selectedRow(self):
        """Returns the row number of the currently selected row, or 0"""
        return self.selectionModel().currentIndex().row()

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

    # @Property(str)
    # def displayColumns(self):
    #     return "".join(self._columns)
    #
    # @displayColumns.setter
    # def displayColumns(self, columns):
    #     self._columns = [col for col in columns.upper() if col in 'XYZABCUVWR']
    #     self.offset_model.setColumns(self._columns)
    #     self.itemDelegate().setColumns(self._columns)

    @Property(bool)
    def confirmActions(self):
        return self._confirm_actions

    @confirmActions.setter
    def confirmActions(self, confirm):
        self._confirm_actions = confirm

    @Property(QColor)
    def currentRowColor(self):
        return self.offset_model.current_row_color

    @currentRowColor.setter
    def currentRowColor(self, color):
        self.offset_model.current_row_color = color

    @Property(QColor)
    def currentRowBackground(self):
        return self.offset_model.current_row_bg or QColor()

    @currentRowBackground.setter 
    def currentRowBackground(self, color):
        self.offset_model.current_row_bg = color
