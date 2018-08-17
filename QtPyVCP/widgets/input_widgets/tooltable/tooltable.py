#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
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

from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QSpinBox

# Set up logging
from QtPyVCP.utilities import logger
from QtPyVCP.utilities.info import Info

LOG = logger.getLogger(__name__)

WIDGET_PATH = os.path.abspath(os.path.dirname(__file__))


class ToolTable(QWidget):

    def __init__(self, parent=None):
        super(ToolTable, self).__init__(parent)

        self.cmd = linuxcnc.command()

        info = Info()

        self.log = LOG

        self.table_header = ["Tool", "Pocket", "Z", "Diameter", "Comment"]
        self.table_vertical_header = ["    " for i in range(99)]

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "tooltable.ui"), self)

        self.ui.tooltable.setHorizontalHeaderLabels(self.table_header)
        self.ui.tooltable.setVerticalHeaderLabels(self.table_vertical_header)

        self.tool_table_file = info.getToolTableFile()
        self.load_tool_table()

        self.toolinfo = []
        self.current_row = 0

        self.ui.tooltable.itemClicked.connect(self.get_row)

        self.ui.load_button.clicked.connect(self.load_tool_table)
        self.ui.delete_button.clicked.connect(self.delete_tool)
        self.ui.empty_button.clicked.connect(self.empty_tool_table)
        self.ui.save_button.clicked.connect(self.save_tool_table)

    def get_row(self, item):
        self.current_row = self.ui.tooltable.row(item)


    # Parse and load tool table into the treeview
    # More or less copied from Chris Morley's GladeVcp tooledit widget

    def load_tool_table(self):

        # TODO show dialogs asking here

        self.ui.tooltable.clearContents()

        fn = self.tool_table_file

        if fn is None:
            return

        if not os.path.exists(fn):
            self.log.warning("Tool table does not exist")
            return

        self.log.debug("Loading tool table: {0}".format(fn))

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

            for offset, i in enumerate(['T', 'P', 'D', 'Z', ';']):
                for word in line.split():
                    print(word)
                    if word.startswith(i):
                        self.ui.tooltable.setItem(count, offset, self.handleItem(word.lstrip(i)))

            self.ui.tooltable.setItem(count, 4, self.handleItem(comment))


    def delete_tool(self):

        # TODO show dialogs asking here

        print(self.current_row)
        for i in range(5):
            self.ui.tooltable.setItem(self.current_row, i, self.handleItem(""))


    def empty_tool_table(self):

        # TODO show dialogs asking here

        self.ui.tooltable.clearContents()

    # Save tool table
    # More or less copied from Chris Morley's GladeVcp tooledit widget

    def save_tool_table(self):

        # TODO show dialogs asking here

        fn = self.tool_table_file

        if fn is None:
            return

        self.log.debug("Saving tool table as: {0}".format(fn))

        with open(fn, "w") as f:
            for row_index in range(self.ui.tooltable.rowCount()):
                line = ""
                for col_index in range(0, self.ui.tooltable.columnCount()):
                    item = self.ui.tooltable.item(row_index, col_index)
                    if item is not None:
                        if col_index in (0, 1):  # tool# pocket#
                            print("{} {} {}".format(col_index, row_index, item.text()))
                            line += "{}{} ".format(['T', 'P', 'D', 'Z', ';'][col_index], item.text())
                        else:
                            print("{} {} {}".format(col_index, row_index, item.text()))
                            line += "{}{} ".format(['T', 'P', 'D', 'Z', ';'][col_index], item.text().strip())
                if line:
                    line += "\n"
                    f.write(line)
            f.flush()
            os.fsync(f.fileno())

        # Theses lines make sure the OS doesn't cache the data so that
        # linuxcnc will actually load the updated tool table

        self.cmd.load_tool_table()

    def handleItem(self, value):

        print(type(value), value)

        item = QTableWidgetItem()

        if isinstance(value, str):
            item.setText(value)
        elif isinstance(value, int):
            item.setText(str(value))
        elif isinstance(value, float):
            item.setText(str(value))
        elif value is None:
            item.setText("")

        return item
