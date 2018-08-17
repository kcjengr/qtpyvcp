#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   Tooltable viewer/editor.

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

UIDIR = os.path.join(PYDIR, 'ui')

import linuxcnc

# Setup logging
from utilities import status
from utilities import command
from utilities import ini_info
from utilities import entry_eval
from utilities.constants import Paths

# Setup logging
from utilities import logger
log = logger.get(__name__)


class ToolTable(Gtk.Box):

    title = "Tool Table"
    author = 'Kurt Jacobson'
    version = '0.1.0'
    date = '03/21/2018'
    description = 'Tooltable viewer/editor'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self)

        self.widget_window = widget_window

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'tool_table.ui'))
        self.builder.connect_signals(self)

        self.tooltable = self.builder.get_object('tooltable')
        self.add(self.tooltable)

        self.treeview = self.builder.get_object('tool_treeview')
        self.model = self.builder.get_object('tool_liststore')

        self.tool_table_file = ini_info.get_tool_table_file()
        self.load_tool_table()
        self.use_touchpad = False

        status.on_changed('stat.tool_in_spindle', lambda s, tn: self.highlight_tool(tn))

# =========================================================
# ToolTable handlers
# =========================================================

    # Parse and load tool table into the treeview
    # More or less copied from Chris Morley's GladeVcp tooledit widget
    def load_tool_table(self, fn=None):
        # If no valid tool table given
        if fn is None:
            fn = self.tool_table_file
        if not os.path.exists(fn):
            log.warning("Tool table does not exist")
            return
        self.model.clear()  # Clear any existing data
        log.debug("Loading tool table: {0}".format(fn))
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
                comment = (line[index+1:]).rstrip("\n")
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
                        if offset in(1, 2):
                            try:
                                array[offset] = int(word.lstrip(i))
                            except ValueError:
                                msg = 'Error reading tool table, can\'t convert "{0}" to integer in {1}' \
                                    .format(word.lstrip(i), line)
                                log.error(msg)
                                self.widget_window.show_error(msg)
                        else:
                            try:
                                array[offset] = "%.4f" % float(word.lstrip(i))
                            except ValueError:
                                msg = 'Error reading tool table, can\'t convert "{0}" to float in {1}' \
                                    .format(word.lstrip(i), line)
                                log.error(msg)
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
        log.debug("Saving tool table as: {0}".format(fn))
        fn = open(fn, "w")
        for row in self.model:
            values = [value for value in row]
            line = ""
            for num,i in enumerate(values):
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

    def get_selected_tools(self):
        tools = []
        for row in range(len(self.model)):
            if self.model[row][0] == 1:
                tools.append(int(self.model[row][1]))
        return tools

    def delete_selected_tool(self, data=None):
        rows = []
        for row in range(len(self.model)):
            if self.model[row][0] == 1:
                rows.append(row)
        rows.reverse()  # So we don't invalidate iters
        for row in rows:
            self.model.remove(self.model.get_iter(row))

    def change_to_selected_tool(self, data=None):
        selected = self.get_selected_tools()
        if len(selected) == 1:
            tool_num = selected[0]
            command.issue_mdi('M6 T{0} G43'.format(tool_num))
            self.treeview.get_selection().unselect_all()
        else:
            num = len(selected)
            msg = "{0} tools selected, you must select exactly one".format(num)
            log.error(msg)
            self.widget_window.show_error(msg, 1.5)

    def add_tool(self, data=None):
        num = len(self.model) + 1
        array = [0, num, num, '0.0000', '0.0000', 'New Tool', None]
        self.model.append(array)

    def reload_tool_table(self, data=None):
        self.load_tool_table()

    def save_changes(self, data=None):
        self.save_tool_table()

    def on_tool_num_edited(self, widget, path, new_text):
        try:
            new_int = int(new_text)
            self.model[path][1] = new_int
            self.model[path][2] = new_int
        except:
            msg = '"{0}" is not a valid tool number'.format(new_text)
            log.error(msg)
            self.widget_window.show_error(msg, 1.5)

    def on_tool_pocket_edited(self, widget, path, new_text):
        try:
            new_int = int(new_text)
            self.model[path][2] = new_int
        except:
            msg = '"{0}" is not a valid tool pocket'.format(new_text)
            log.error(msg)
            self.widget_window.show_error(msg, 1.5)

    def on_tool_dia_edited(self, widget, path, new_text):
        try:
            num = entry_eval.eval(new_text)
            self.model[path][3] = "{:.4f}".format(float(num))
        except:
            msg = '"{0}" does not evaluate to a valid tool diameter'.format(new_text)
            log.error(msg)
            self.widget_window.show_error(msg, 1.5)

    def on_z_offset_edited(self, widget, path, new_text):
        try:
            num = entry_eval.eval(new_text)
            self.model[path][4] = "{:.4f}".format(float(num))
        except:
            msg = '"{0}" does not evaluate to a valid tool length'.format(new_text)
            log.error(msg)
            self.widget_window.show_error(msg, 1.5)

    def on_tool_remark_edited(self, widget, path, new_text):
        self.model[path][5] =  new_text

    # Popup int numpad on int edit
    def on_int_editing_started(self, renderer, entry, row):
        if self.use_touchpad:
            self.int_touchpad.show(entry)

    # Popup float numpad on float edit
    def on_float_editing_started(self, renderer, entry, row):
        if self.use_touchpad:
            self.float_touchpad.show(entry, self.machine_units)

    # Popup keyboard on text edit
    def on_remark_editing_started(self, renderer, entry, row):
        if self.use_touchpad:
            self.keyboard.show(entry)

    # Toggle selection checkbox value
    def on_select_toggled(self, widget, row):
        self.model[row][0] = not self.model[row][0]

    # For single click selection and edit
    def on_treeview_button_press_event(self, widget, event):
        if event.button == 1:  # left click
            try:
                row, col, x, y = widget.get_path_at_pos(int(event.x), int(event.y))
                widget.set_cursor(row, None, True)
            except:
                pass

    # Used for indicating tool in spindle
    def highlight_tool(self, tool_num):
        for row in range(len(self.model)):
            self.model[row][0] = 0
            self.model[row][6] = None
            if self.model[row][1] == tool_num:
                self.current_tool_data = self.model[row]
                self.model[row][6] = "gray"

    # This is not used now, but might be useful at some point
    def set_selected_tool(self, toolnum):
        found = False
        for row in range(len(self.model)):
            if self.model[row][1] == toolnum:
                found = True
                break
        if found:
            self.model[row][0] = 1 # Check the box
            self.treeview.set_cursor(row)
        else:
            log.warning("Did not find tool {0} in the tool table".format(toolnum))
