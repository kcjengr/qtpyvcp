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

from qtpy.QtWidgets import QVBoxLayout, QLineEdit

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.settings import getSetting
from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.utilities import logger

INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
LATHE = bool(INIFILE.find("DISPLAY", "LATHE"))

Log = logger.getLogger(__name__)


class ToolDetailsDialog(BaseDialog):
    def __init__(self, parent=None):
        super(ToolDetailsDialog, self).__init__(parent=parent, stay_on_top=True)

        self.main_layout = QVBoxLayout()

        self.info = Info()
        self.log = Log

        self.data_manager = getPlugin('persistent_data_manager')
        self.tool_table = getPlugin('tooltable')

    def show(self):

        self.tool_table_custom = getSetting('tool_table.custom')

        for index, _ in self.tool_table.getToolTable().items():
            if index == 0:
                continue

            for setting in self.tool_table_custom.value:
                setting_id = 'tool-{}-{}'.format(index, setting)
                tool_data = self.data_manager.getData(setting_id)
                print(index, setting_id, tool_data)

                # if data:
                #     field = self.create_field(k, 'str', data[1])
                #
                #     main_layout.addWidget(field)

        self.setLayout(self.main_layout)
        self.setWindowTitle("Tool Custom Details")

    def create_field(self, name, field_type, default=None):
        if field_type == 'str':
            field = QLineEdit()
            if default:
                field.setText(default)

        return field
