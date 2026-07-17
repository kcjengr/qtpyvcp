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
from PySide6.QtWidgets import (QTableView, QHeaderView, QStyledItemDelegate,
                               QDoubleSpinBox, QMessageBox, QMenu)

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import connectSetting, getSetting

IN_DESIGNER = os.getenv('DESIGNER', False)
if not IN_DESIGNER:
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
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            editor.setDecimals(4)
            # editor.setStepType(QSpinBox.AdaptiveDecimalStepType)
            editor.setProperty('stepType', 1)  # stepType was added in 5.12

            try:
                min_range = getSetting('offset_table.min_range').value
                max_range = getSetting('offset_table.max_range').value

                if min_range and max_range:
                    editor.setRange(min_range, max_range)
                else:
                    editor.setRange(-1000, 1000)
            except:
                # In designer mode or when settings aren't available
                editor.setRange(-1000, 1000)
            return editor

        return None


class OffsetModel(QStandardItemModel):
    # persistent_data_manager key for the visible-columns set -- one entry,
    # scoped by the plugin's own per-config-folder persistence file, so no
    # per-machine namespacing needed here.
    VISIBLE_COLUMNS_KEY = 'offset_table_visible_columns'

    def __init__(self, parent=None):
        super(OffsetModel, self).__init__(parent)

        self.ot = getPlugin('offsettable')

        self.current_row_color = QColor(Qt.darkGreen)
        self.current_row_bg = None  # Add this line

        if IN_DESIGNER:
            # In designer mode, set up dummy data to show the table structure
            self._columns = [c for c in 'XYZABC']  # Default columns for designer
            self._visible_columns = list(self._columns)
            self._rows = list(range(1, 11))  # 10 rows for designer preview
            self.setColumnCount(len(self._columns))
            self.setRowCount(len(self._rows))
            # Set headers
            for i, col in enumerate(self._columns):
                self.setHeaderData(i, Qt.Horizontal, col, Qt.DisplayRole)
            for i, row in enumerate(self._rows):
                self.setHeaderData(i, Qt.Vertical, f"G5{i+1}", Qt.DisplayRole)
            return

        self._columns = self.ot.columns
        self._rows = self.ot.rows

        self._column_labels = self.ot.COLUMN_LABELS
        self._row_labels = self.ot.ROW_LABELS

        self._offset_table = self.ot.getOffsetTable()

        # Column *visibility* is a pure display-layer concern, independent
        # of self._columns above (the full set the ini's OFFSET_COLUMNS
        # configures, and the positional index space the underlying
        # offset_table array/save-to-LinuxCNC path is keyed on -- see
        # data()/setData()/saveOffsetTable() below, none of which are
        # affected by which columns are currently visible). Persisted
        # per config folder (same mechanism .vcp_persistent_data.pickle
        # already uses), not per axis-letter default -- a fresh/never-
        # toggled config shows every configured column, same as before
        # this feature existed.
        self._data_manager = getPlugin('persistent_data_manager')
        persisted = self._filterToKnownColumns(
            self._data_manager.getData(self.VISIBLE_COLUMNS_KEY, None))
        self._visible_columns = persisted or list(self._columns)

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
            LOG.debug("Offset Table update is zero length - skip it")
            return
        
        self.beginResetModel()
        self._offset_table = offset_table
        self.endResetModel()

    def setColumns(self, columns):
        self._columns = columns
        self.setColumnCount(len(columns))

    # ------------------------------------------------------ visibility

    def allColumns(self):
        """Every column this machine is configured for (OFFSET_COLUMNS),
        regardless of current visibility -- the toggle menu's universe."""
        return list(self._columns)

    def visibleColumns(self):
        return list(self._visible_columns)

    def _filterToKnownColumns(self, columns):
        """Drop any letter not in self._columns (e.g. a persisted set from
        before OFFSET_COLUMNS changed) -- never surface a column the
        underlying offset_table array has no slot for. Also normalizes to
        self._columns' own canonical order regardless of what order
        `columns` arrives in, so a column that gets hidden and re-shown
        always lands back in its original position instead of at the end
        of whatever order it was toggled in (setVisibleColumns() callers
        naturally build the list in toggle order, not display order).
        Returns None (not an empty list) if nothing valid remains, so
        callers can fall back to a sane default instead of rendering zero
        columns."""
        if not columns:
            return None
        wanted = set(columns)
        ordered = [c for c in self._columns if c in wanted]
        return ordered or None

    def setVisibleColumns(self, columns):
        visible = self._filterToKnownColumns(columns) or list(self._columns)
        self.beginResetModel()
        self._visible_columns = visible
        self.endResetModel()
        if not IN_DESIGNER:
            self._data_manager.setData(self.VISIBLE_COLUMNS_KEY, visible)

    def _realColumnIndex(self, visible_col):
        """Map a QTableView column position (an index into
        self._visible_columns) to its real position in self._columns --
        the fixed index space self._offset_table rows and the plugin's
        column.index(letter) lookups (loadOffsetTable/saveOffsetTable) are
        keyed on. Hiding a column never changes that mapping, only which
        positions the view exposes -- see data()/setData() below."""
        return self._columns.index(self._visible_columns[visible_col])

    # ---------------------------------------------------------------

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._visible_columns[section]
        elif role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            return self._row_labels[section]

        return QStandardItemModel.headerData(self, section, orientation, role)

    def columnCount(self, parent=None):
        if IN_DESIGNER:
            return 0
        return len(self._visible_columns)

    def rowCount(self, parent=None):
        if IN_DESIGNER:
            return 0
        return len(self._rows)

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if (role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole) and len(self._offset_table) > 0:
            columns_index = self._realColumnIndex(index.column())
            rows_index = index.row()

            # column_index = self._columns[index.column()]
            # index_column = self._column_labels.index(column_index)

            return self._offset_table[rows_index][columns_index]

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight

        elif role == Qt.ItemDataRole.ForegroundRole:

            offset = index.row() + 1

            if self.ot.current_index == offset:

                return QBrush(self.current_row_color)

            else:

                return QStandardItemModel.data(self, index, role)

        elif role == Qt.ItemDataRole.BackgroundRole and self.current_row_bg is not None:  # Add this block
            offset = index.row() + 1
            if self.ot.current_index == offset:
                return QBrush(self.current_row_bg)
            else:
                return QStandardItemModel.data(self, index, role)

        return QStandardItemModel.data(self, index, role)

    def setData(self, index, value, role):
        columns_index = self._realColumnIndex(index.column())
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
        self._columns = [c for c in 'XYZABCUVWR']  # Default columns
        self._current_row_color = QColor('sage')
        self._current_row_bg = None  # Add this line
        self._confirm_actions = False  # Initialize confirm_actions property

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setSourceModel(self.offset_model)

        if not IN_DESIGNER:
            self.item_delegate = ItemDelegate(columns=self._columns)
            self.setItemDelegate(self.item_delegate)

        self.setModel(self.proxy_model)

        if not IN_DESIGNER:
            # keep highlight/selection in sync with active work offset
            self.offset_model.ot.active_offset_changed.connect(self._onActiveOffsetChanged)
            # initial selection
            self._onActiveOffsetChanged(self.offset_model.ot.current_index)

        # Appearance/Behaviour settings
        self.setSortingEnabled(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        if not IN_DESIGNER:
            # per-column visibility menu, same UX as the tool table's
            header = self.horizontalHeader()
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(self._onHeaderContextMenu)

        if IN_DESIGNER:
            return
        STATUS.all_axes_homed.notify(self.handle_home_signal)

    def handle_home_signal(self, all_axes):
        if all_axes:
            self.setEnabled(True)
        else:
            self.setEnabled(False)

    # ------------------------------------------------------- column menu

    def _onHeaderContextMenu(self, position):
        header = self.horizontalHeader()
        menu = QMenu(self)

        show_all = menu.addAction('Show All Columns')
        menu.addSeparator()

        visible = set(self.offset_model.visibleColumns())
        toggles = {}
        for key in self.offset_model.allColumns():
            action = menu.addAction(key)
            action.setCheckable(True)
            action.setChecked(key in visible)
            toggles[action] = key

        selected = menu.exec(header.mapToGlobal(position))
        if selected is None:
            return

        if selected == show_all:
            self.offset_model.setVisibleColumns(self.offset_model.allColumns())
        elif selected in toggles:
            key = toggles[selected]
            cols = self.offset_model.visibleColumns()
            if selected.isChecked():
                if key not in cols:
                    cols.append(key)
            else:
                cols = [c for c in cols if c != key]
                if not cols:
                    QMessageBox.warning(self, 'Offset Table',
                                        'At least one column must remain visible.')
                    return
            self.offset_model.setVisibleColumns(cols)

    @Slot(int)
    def _onActiveOffsetChanged(self, offset_num):
        # offset_num is 1-based (G54->1). Update row highlight and selection.
        self.offset_model.refreshModel()
        row = max(0, offset_num - 1)
        self.selectRow(row)

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
                                   QMessageBox.StandardButton.Yes,
                                   QMessageBox.StandardButton.No)
        if box == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    @Property(int)
    def currentRow(self):
        return self.selectedRow()

    @currentRow.setter
    def currentRow(self, row):
        self.selectRow(row)

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

