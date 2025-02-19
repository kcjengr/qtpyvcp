#   Copyright (c) 2023 Jose I. Romero
#      <jir@electrumee.com>
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

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel, QMenu

from qtpyvcp import actions
from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.pyside_ui_loader import PySide6Ui

class ShutDownDialog(BaseDialog):
    def __init__(self, *args, **kwargs):
        super(ShutDownDialog, self).__init__(title=None,stay_on_top=True,frameless=True)

        default_ui = os.path.join(os.path.dirname(__file__), 'shutdown_dialog.ui')

        self.ui_file = kwargs.get('ui_file', default_ui)

        file_path = os.path.join(os.path.dirname(__file__), self.ui_file)
        #ui_file = QFile(file_path)
        #ui_file.open(QFile.ReadOnly)
        
        #loader = QUiLoader()
        #self.ui = loader.load(ui_file, self)
        form_class, base_class = PySide6Ui(file_path).load()
        form = form_class()
        form.setupUi(self)


    def reject(self):
        self.hide();

    def accept(self):
        self.hide();
