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
from qtpy.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.plugins import getPlugin

from qtpyvcp import hal

class ToolChangeDialog(BaseDialog):
    """Tool Change Dialog

    Manual tool changing dialog component

    This is a qtpyvcp replacement of axis' `hal_manualtoolchange`. It
    uses the same pin names in the same way, but the HAL component they
    are under is called `qtpyvcp_manualtoolchange` instead.
    """
    def __init__(self, *args, **kwargs):
        super(ToolChangeDialog, self).__init__(stay_on_top=True)

        self.tt = getPlugin('tooltable')
        self.tool_number = 0

        default_ui = os.path.join(os.path.dirname(__file__), 'toolchange_dialog.ui')

        self.ui_file = kwargs.get('ui_file', default_ui)

        self.ui = uic.loadUi(self.ui_file, self)

        comp = hal.getComponent("qtpyvcp_manualtoolchange")
        comp.addPin('number', 's32', 'in')
        comp.addPin('change', 'bit', 'in')
        self.changed_pin = comp.addPin('changed', 'bit', 'out')
        comp.addPin('change_button', 'bit', 'in')

        comp.addListener('number', self.prepare_tool)
        comp.addListener('change', self.on_change)
        comp.addListener('change_button', self.on_change_button)
        self.hide()

    def prepare_tool(self, tool_no):
        if self.tool_number == tool_no: return  # Already prepared this tool
        tool_data = self.tt.getToolTable().get(tool_no, {})
        tool_r = tool_data.get('R', 'UNKNOWN')
        self.ui.lblToolNumber.setText(str(tool_no))
        self.ui.lblToolRemark.setText(tool_r)
        self.tool_number = tool_no

    def on_change(self, value=True):
        if value:
            self.show()
        else:
            self.changed_pin.value = False

    def on_change_button(self, value=True):
        if value:
            self.accept()

    def reject(self):
        pass

    def accept(self):
        self.changed_pin.value = True
        self.hide()