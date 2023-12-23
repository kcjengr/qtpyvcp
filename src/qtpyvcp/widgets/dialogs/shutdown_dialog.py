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
from qtpy import uic
from qtpy.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel, QMenu, QAction

from qtpyvcp import actions
from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.plugins import getPlugin

class ShutDownDialog(BaseDialog):
    def __init__(self, *args, **kwargs):
        super(ShutDownDialog, self).__init__(title=None,stay_on_top=True,frameless=True)

        default_ui = os.path.join(os.path.dirname(__file__), 'shutdown_dialog.ui')

        self.ui_file = kwargs.get('ui_file', default_ui)

        self.ui = uic.loadUi(self.ui_file, self)

    def reject(self):
        self.hide();

    def accept(self):
        self.hide();
