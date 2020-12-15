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

from qtpy.QtWidgets import QVBoxLayout, QLineEdit, QHBoxLayout, QLabel, QComboBox, QSpinBox

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

        self.tool_table_custom = getSetting('tool_table.custom')

        for index, _ in self.tool_table.getToolTable().items():
            print(index)
            if index == 0:
                continue
            layout = QHBoxLayout()
            label = QLabel("Tool {}".format(index))
            layout.addWidget(label)
            for setting in self.tool_table_custom.getValue():
                setting_id = 'tool-{:02d}-{}'.format(index, setting)
                tool_data = self.data_manager.getData(setting_id)

                if isinstance(tool_data, int):
                    Log.debug("{} {} {}".format(index, setting_id, tool_data))

                    field_layout = self.create_field(setting_id, int, tool_data)
                    layout.addLayout(field_layout)
                elif isinstance(tool_data, str):
                    Log.debug("{} {} {}".format(index, setting_id, tool_data))

                    field_layout = self.create_field(setting_id, str, tool_data)
                    layout.addLayout(field_layout)
                elif isinstance(tool_data, list):
                    Log.debug("{} {} {}".format(index, setting_id, tool_data))

                    field_layout = self.create_field(setting_id, list, tool_data)
                    layout.addLayout(field_layout)

            self.main_layout.addLayout(layout)

        self.setLayout(self.main_layout)
        self.setWindowTitle("Tool Custom Details")

    def create_field(self, name, field_type, default=None):

        layout = QVBoxLayout()
        label = QLabel(name)
        layout.addWidget(label)

        if field_type == int:
            field = QSpinBox()
            field.setRange(-999999, 999999)
            if default:
                field.setValue(default)
            layout.addWidget(field)
        if field_type == str:
            field = QLineEdit()
            field.setPlaceholderText(name)
            if default:
                field.setText(default)
            layout.addWidget(field)
        elif field_type == list:
            field = QComboBox()
            if default:
                for index, item in enumerate(default):
                    field.addItem(str(item), index)

            layout.addWidget(field)

        return layout
