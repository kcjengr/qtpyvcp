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

from PyQt5 import uic

from PyQt5.QtCore import QByteArray, Qt, QTimer
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtWidgets import (QAction, QActionGroup, QApplication,
                             QWidget, QMessageBox)

# Set up logging
from QtPyVCP.utilities import logger

LOG = logger.getLogger(__name__)

WIDGET_PATH = os.path.abspath(os.path.dirname(__file__))


class ToolTable(QWidget):

    def __init__(self, parent=None):
        super(ToolTable, self).__init__(parent)

        self.log = LOG

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "tootable.ui"), self)


    # Parse and load tool table into the treeview
    # More or less copied from Chris Morley's GladeVcp tooledit widget

    def load_tool_table(self, fn=None):
        # If no valid tool table given
        if fn is None:
            fn = self.tool_table_file
        if not os.path.exists(fn):
            self.log.warning("Tool table does not exist")
            return
        self.model.clear()  # Clear any existing data
        self.log.debug("Loading tool table: {0}".format(fn))
        with open(fn, "r") as tf:
            tool_table = tf.readlines()

        self.toolinfo = []  # TODO move to __init__
        for line in tool_table:
            # Separate tool data from comments
            comment = ''
            index = line.find(";")  # Find comment start index
            if index == -1:  # Delimiter ';' is missing, so no comments
                line = line.rstrip("\n")
            else:
                comment = (line[index + 1:]).rstrip("\n")
                line = line[0:index].rstrip()
            array = [False, 1, 1, '0', '0', comment, None]
            # search beginning of each word for keyword letters
            # offset 0 is the checkbox so ignore it
            # if i = ';' that is the comment and we have already added it
            # offset 1 and 2 are integers the rest floats
            for offset, i in enumerate(['S', 'T', 'P', 'D', 'Z', ';']):
                if offset == 0 or i == ';':
                    continue
                for word in line.split():
                    if word.startswith(i):
                        if offset in (1, 2):
                            try:
                                array[offset] = int(word.lstrip(i))
                            except ValueError:
                                msg = 'Error reading tool table, can\'t convert "{0}" to integer in {1}' \
                                    .format(word.lstrip(i), line)
                                self.log.error(msg)
                                self.widget_window.show_error(msg)
                        else:
                            try:
                                array[offset] = "%.4f" % float(word.lstrip(i))
                            except ValueError:
                                msg = 'Error reading tool table, can\'t convert "{0}" to float in {1}' \
                                    .format(word.lstrip(i), line)
                                self.log.error(msg)
                                self.widget_window.show_error(msg)
                        break

            # Add array to liststore
            self.model.append(array)

    # Save tool table
    # More or less copied from Chris Morley's GladeVcp tooledit widget

    def save_tool_table(self, fn=None):
        if fn is None:
            fn = self.tool_table_file
        if fn is None:
            return
        self.log.debug("Saving tool table as: {0}".format(fn))
        fn = open(fn, "w")
        for row in self.model:
            values = [value for value in row]
            line = ""
            for num, i in enumerate(values):
                if num in (0, 6):
                    continue
                elif num in (1, 2):  # tool# pocket#
                    line = line + "%s%d " % (['S', 'T', 'P', 'D', 'Z', ';'][num], i)
                else:
                    line = line + "%s%s " % (['S', 'T', 'P', 'D', 'Z', ';'][num], i.strip())
            # Write line to file
            fn.write(line + "\n")
        # Theses lines make sure the OS doesn't cache the data so that
        # linuxcnc will actually load the updated tool table
        fn.flush()
        os.fsync(fn.fileno())
        linuxcnc.command().load_tool_table()