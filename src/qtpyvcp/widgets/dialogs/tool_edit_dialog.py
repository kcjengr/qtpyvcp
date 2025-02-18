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

#from PySide6.QtUiTools import QUiLoader
#from PySide6.QtCore import QFile
from PySide6.QtWidgets import QDialog

from qtpyvcp.utilities import logger
from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.utilities.pyside_ui_loader import PySide6Ui

INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
LATHE = bool(INIFILE.find("DISPLAY", "LATHE"))
LOG = logger.getLogger(__name__)


class ToolEditDialog(BaseDialog):
    def __init__(self, parent=None):
        super(ToolEditDialog, self).__init__(parent=parent, stay_on_top=True)

        self.mill_ui_dialog = 'tool_edit_mill_dialog.ui'
        self.lathe_ui_dialog = 'tool_edit_lathe_dialog.ui'

        if LATHE is True:
            self.dialog_ui = self.lathe_ui_dialog
        else:
            self.dialog_ui = self.mill_ui_dialog

        file_path = os.path.join(os.path.dirname(__file__), self.dialog_ui)
        #ui_file = QFile(file_path)
        #ui_file.open(QFile.ReadOnly)
        
        #loader = QUiLoader()
        #self.ui = loader.load(ui_file, self)
        LOG.debug(f"ToolEditDialog UI file to load and convert: {file_path}")
        form_class, base_class = PySide6Ui(file_path).load()
        form = form_class()
        form.setupUi(self)

