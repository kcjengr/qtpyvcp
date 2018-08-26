#!/usr/bin/env python

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

# Description:
# Tool table viewer/editor.

import os
import sys

import linuxcnc

from PyQt5.QtCore import pyqtSlot, pyqtProperty, Qt, QItemSelectionModel
from PyQt5.QtWidgets import QTableView, QMessageBox, QAbstractItemView
from PyQt5.QtGui import QStandardItem, QStandardItemModel

# Set up logging
from QtPyVCP.utilities import logger
from QtPyVCP.utilities.info import Info

LOG = logger.getLogger(__name__)
INFO = Info()


class ToolTable(QTableView):

    def __init__(self, parent=None):
        super(ToolTable, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.parent = parent

        self.cmd = linuxcnc.command()

        self.table_header = ["Tool", "Pocket", "Z", "Diameter", "Comment"]
        self.col_count = len(self.table_header)

        self.model = QStandardItemModel(0, 0, self)
        self.model.setHorizontalHeaderLabels(self.table_header)

        self.setModel(self.model)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().hide()

        self.tool_table_file = INFO.getToolTableFile()

        self.tool_table_loaded = False
        self.loadToolTable()
        self.tool_table_loaded = True

    @pyqtSlot()
    def loadToolTable(self):
        if self.tool_table_loaded:
            if not self.ask_dialog("Do you wan't to re-load the tool table?\n all unsaved changes will be lost."):
                return

        self.removeAllTools(confirm=False)

        fn = self.tool_table_file

        if fn is None:
            return

        if not os.path.exists(fn):
            LOG.warning("Tool table does not exist")
            return

        LOG.debug("Loading tool table: {0}".format(fn))

        with open(fn, "r") as tf:
            tool_table = tf.readlines()

        for count, line in enumerate(tool_table):

            # Separate tool data from comments
            comment = ''
            index = line.find(";")  # Find comment start index

            if index == -1:  # Delimiter ';' is missing, so no comments
                line = line.rstrip("\n")
            else:
                comment = (line[index + 1:]).rstrip("\n")
                line = line[0:index].rstrip()

            # search beginning of each word for keyword letters
            # offset 0 is the checkbox so ignore it
            # if i = ';' that is the comment and we have already added it
            # offset 1 and 2 are integers the rest floats

            for offset, i in enumerate(['T', 'P', 'Z', 'D', ';']):
                for word in line.split():
                    if word.startswith(i):
                        item = self.handleItem(word.lstrip(i))
                        if i in ('T', 'P'):
                            item.setTextAlignment(Qt.AlignCenter)
                        elif i in ('Z', 'D'):
                            item.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)

                        self.model.setItem(count, offset, item)

            item = self.handleItem(comment)
            self.model.setItem(count, 4, item)

    @pyqtSlot()
    def saveToolTable(self):
        if not self.ask_dialog("Do you wan't to save and load this tool table into the system?"):
            return

        fn = self.tool_table_file

        if fn is None:
            return

        LOG.debug("Saving tool table as: {0}".format(fn))

        with open(fn, "w") as f:
            for row_index in range(self.model.rowCount()):
                line = ""
                for col_index in range(self.col_count):
                    item = self.model.item(row_index, col_index)
                    if item.text() is not None:
                        if item.text() != "":
                            if col_index in (0, 1):  # tool# pocket#
                                line += "{}{} ".format(['T', 'P', 'Z', 'D', ';'][col_index], item.text())
                            else:
                                line += "{}{} ".format(['T', 'P', 'Z', 'D', ';'][col_index], item.text().strip())
                if line:
                    line += "\n"
                    f.write(line)

            f.flush()
            os.fsync(f.fileno())

        self.cmd.load_tool_table()

    @pyqtSlot()
    def appendTool(self):
        row_num = self.model.rowCount() + 1
        self.model.appendRow(self.newRow(row_num))
        self.selectRow(row_num - 1)

    @pyqtSlot()
    def insertToolAbove(self):
        row_num = self.selectedRow()
        self.model.insertRow(row_num, self.newRow(row_num))
        self.selectRow(row_num)

    @pyqtSlot()
    def insertToolBelow(self):
        row_num = self.selectedRow() + 1
        self.model.insertRow(row_num, self.newRow(row_num))
        self.selectRow(row_num)

    @pyqtSlot()
    def deleteSelectedTool(self):
        current_row = self.selectedRow()
        current_tool = self.model.item(current_row, 0)

        if not self.ask_dialog("Do yo wan't to delete T{} ?".format(current_tool.text())):
            return

        self.model.removeRow(current_row)

    @pyqtSlot()
    def removeAllTools(self, confirm=True):
        if confirm:
            if not self.ask_dialog("Do yo wan't to delete the whole tool table?"):
                return

        for i in reversed(range(self.model.rowCount() + 1)):
            self.model.removeRow(i)

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

    def newRow(self, row_num=0):
        new_data = [row_num, row_num, 0.0, 0.0, 'New Tool']
        row_items = [self.handleItem(item) for item in new_data]
        return row_items

    def handleItem(self, value):
        item = QStandardItem()

        if isinstance(value, str):
            item.setText(value)
        elif isinstance(value, int):
            item.setText(str(value))
        elif isinstance(value, float):
            item.setText('{:0.4f}'.format(value))
        elif value is None:
            item.setText("")
        return item

    def selectedRow(self):
        return self.selectionModel().currentIndex().row()
