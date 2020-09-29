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


import linuxcnc
import os

from qtpy import uic
from qtpy.QtWidgets import QDialog

INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
LATHE = bool(INIFILE.find("DISPLAY", "LATHE"))


class ToolEditDialog(QDialog):
    def __init__(self, parent=None):
        super(ToolEditDialog, self).__init__(parent=parent)

        self.mill_ui_dialog = 'tool_edit_mill_dialog.ui'
        self.lathe_ui_dialog = 'tool_edit_lathe_dialog.ui'

        if LATHE is True:
            self.dialog_ui = self.lathe_ui_dialog
        else:
            self.dialog_ui = self.mill_ui_dialog

        uic.loadUi(os.path.join(os.path.dirname(__file__), self.dialog_ui), self)
