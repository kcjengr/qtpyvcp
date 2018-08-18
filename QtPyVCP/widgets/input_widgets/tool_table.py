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

from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTableView
from PyQt5.QtGui import QStandardItem, QStandardItemModel

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
        self.mainLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.setLayout(self.mainLayout)

        self.table_header = ["Tool", "Pocket", "Z", "Diameter", "Comment"]
        self.buttons = ["Load", "Delete", "Empty", "Add Up", "Add Down", "Save"]

        self.row_count = 0
        self.col_count = len(self.table_header)

        self.model = QStandardItemModel()

        self.model.setHorizontalHeaderLabels(self.table_header)

        self.tool_table = QTableView(self)
        self.tool_table.setFixedSize(800, 400)
        self.tool_table.setModel(self.model)

        self.tool_table.setAlternatingRowColors(True)

        self.mainLayout.addWidget(self.tool_table)
        self.mainLayout.addLayout(self.buttonLayout)

        self.tool_table_file = info.getToolTableFile()

        self.button_widgets = {}
        for button in self.buttons:
            self.button_widgets[button] = QPushButton(button)
            self.buttonLayout.addWidget(self.button_widgets[button])

        self.load_tool_table()

        self.current_row = 0

        self.tool_table.clicked.connect(self.get_row)

        self.button_widgets["Load"].clicked.connect(self.load_tool_table)
        self.button_widgets["Delete"].clicked.connect(self.delete_tool)
        self.button_widgets["Empty"].clicked.connect(self.empty_tool_table)
        self.button_widgets["Add Up"].clicked.connect(self.add_tool_up)
        self.button_widgets["Add Down"].clicked.connect(self.add_tool_down)
        self.button_widgets["Save"].clicked.connect(self.save_tool_table)

    def get_row(self, item):
        self.current_row = item.row()

    # Parse and load tool table into the treeview
    # More or less copied from Chris Morley's GladeVcp tooledit widget

    def load_tool_table(self):

        # TODO show dialogs asking here

        # self.tool_table.clearContents()

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
                    if word.startswith(i):
                        self.model.setItem(count, offset, self.handleItem(word.lstrip(i)))

            self.model.setItem(count, 4, self.handleItem(comment))

            self.row_count = count

    def delete_tool(self):

        # TODO show dialogs asking here
        self.model.removeRow(self.current_row)
        self.row_count -= 1

    def add_tool_up(self):
        self.model.insertRow(self.current_row)
        self.row_count += 1

    def add_tool_down(self):
        self.model.insertRow(self.current_row + 1)
        self.row_count += 1

    def empty_tool_table(self):
        # TODO show dialogs asking here
        for i in reversed(range(self.row_count + 1)):
            self.model.removeRow(i)

    # Save tool table
    # More or less copied from Chris Morley's GladeVcp tooledit widget

    def save_tool_table(self):

        # TODO show dialogs asking here

        fn = self.tool_table_file

        if fn is None:
            return

        self.log.debug("Saving tool table as: {0}".format(fn))

        with open(fn, "w") as f:
            for row_index in range(self.row_count):
                line = ""
                for col_index in range(self.col_count):
                    item = self.model.item(row_index, col_index)
                    if item.text() is not None:
                        if item.text() != "":
                            if col_index in (0, 1):  # tool# pocket#
                                line += "{}{} ".format(['T', 'P', 'D', 'Z', ';'][col_index], item.text())
                            else:
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

        item = QStandardItem()

        if isinstance(value, str):
            item.setText(value)
        elif isinstance(value, int):
            item.setText(str(value))
        elif isinstance(value, float):
            item.setText(str(value))
        elif value is None:
            item.setText("")

        return item
