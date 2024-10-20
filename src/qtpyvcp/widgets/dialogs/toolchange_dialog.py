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
from qtpyvcp.utilities.obj_status import HALStatus

from qtpyvcp import hal

class ToolChangeDialog(BaseDialog):
    """Tool Change Dialog

    Manual tool changing dialog component

    This is a qtpyvcp replacement of axis' `hal_manualtoolchange`. It
    uses the same pin names in the same way, but the HAL component they
    are under is called `qtpyvcp_manualtoolchange` instead.

    Example:
        Remove any references in .hal to ``hal_manualtoolchange``
        and remove ``net tool-change-loop`` if you have it.

        To your main `.hal` add::

            #  ---manual tool change signals---
            net tool-change-request    <= iocontrol.0.tool-change
            net tool-change-confirmed  => iocontrol.0.tool-changed
            net tool-number            <= iocontrol.0.tool-prep-number

            #  ---ignore tool prepare requests---
            net tool-prepare-loopback   iocontrol.0.tool-prepare      =>  iocontrol.0.tool-prepared

        and to you `*postgui.hal` add::

            #  ---manual tool change signals---
            net tool-change-request     =>  qtpyvcp_manualtoolchange.change
            net tool-change-confirmed   <=  qtpyvcp_manualtoolchange.changed
            net tool-number             =>  qtpyvcp_manualtoolchange.number

    """
    def __init__(self, *args, **kwargs):
        super(ToolChangeDialog, self).__init__(stay_on_top=True)
        self.hal_stat = HALStatus()

        self.tt = getPlugin('tooltable')
        self.tool_number = 0

        default_ui = os.path.join(os.path.dirname(__file__), 'toolchange_dialog.ui')

        self.ui_file = kwargs.get('ui_file', default_ui)

        self.ui = uic.loadUi(self.ui_file, self)

        # Set the tool number to existing tool
        self.ui.lblToolNumber.setText(str(self.tool_number))

        if self.ui_file == default_ui:
            self.label_1Remove = 'Manual Tool Change Requested<br>Remove the following tool and hit "Done" to continue.'
            self.btnDoneRemove = 'Done'
            self.label_1Insert = 'Manual Tool Change Requested<br>Insert the following tool and hit "Done" to continue.'
            self.btnDoneInsert = 'Done'
        else:
            self.label_1Remove = 'Tool Change Requested, Remove tool'
            self.btnDoneRemove = 'ONCE TOOL IS REMOVED - PRESS TO RESUME'
            self.label_1Insert = 'Tool Change Requested, Insert tool'
            self.btnDoneInsert = 'ONCE TOOL IS LOADED - PRESS TO RESUME'

        self.ui.label_1.setText(self.label_1Remove)
        self.ui.btnDone.setText(self.btnDoneRemove)
        self.toolRemark = "Please remove existing tool from spindle."
        self.ui.lblToolRemark.setText(self.toolRemark)

        comp = hal.getComponent("qtpyvcp_manualtoolchange")
        comp.addPin('number', 's32', 'in')
        self.change_pin = comp.addPin('change', 'bit', 'in')
        self.changed_pin = comp.addPin('changed', 'bit', 'out')
        comp.addPin('change_button', 'bit', 'in')

        comp.addListener('number', self.prepare_tool)
        comp.addListener('change', self.on_change)
        comp.addListener('change_button', self.on_change_button)
        self.startTimer(100) # Poll 10 times per second
        self.hide()

    def timerEvent(self, timer):
        if not self.change_pin.value:
            # Ensure that the changed pin is de-asserted when the change request pin is low
            self.changed_pin.value = False
            if self.isVisible():
                self.hide()
                current_tool = self.getCurrentTool()
                if current_tool != 0:
                    self.ui.lblToolNumber.setText('0') # Set this to 0, we set it to valid tool # on prep
                if current_tool == 0:
                    self.ui.lblToolRemark.setText(self.toolRemark)

    def prepare_tool(self, tool_no):
        if self.tool_number == tool_no: return  # Already prepared this tool

        current_tool = self.getCurrentTool()

        tool_data = self.tt.getToolTable().get(tool_no, {})
        tool_r = tool_data.get('R', 'UNKNOWN')

        current_tool_data = self.tt.getToolTable().get(current_tool, {})
        current_tool_r = current_tool_data.get('R', 'UNKNOWN')

        if tool_no == 0:
            self.ui.lblToolNumber.setText(str(self.tool_number))
            self.ui.label_1.setText(self.label_1Remove)
            self.ui.lblToolRemark.setText(current_tool_r)
            self.ui.btnDone.setText(self.btnDoneRemove)
        else:
            self.ui.btnDone.setText(self.btnDoneInsert)
            self.ui.label_1.setText(self.label_1Insert)
            self.ui.lblToolNumber.setText(str(tool_no))
            self.ui.lblToolRemark.setText(tool_r)

        self.tool_number = tool_no

    def on_change(self, value=True):
        if value:
            current_tool = self.getCurrentTool()
            if current_tool != 0:
                self.ui.lblToolNumber.setText(str(current_tool))
            self.show()

    def on_change_button(self, value=True):
        if value:
            self.accept()

    def reject(self):
        pass

    def accept(self):
        self.changed_pin.value = True

    def getCurrentTool(self):
        return self.hal_stat.getHALPin('halui.tool.number').getValue()
