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

from collections import OrderedDict

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities import logger
from qtpyvcp.actions.machine_actions import issue_mdi

Log = logger.getLogger(__name__)


class OffsetsDialog(QDialog):

    def __init__(self, parent=None):
        super(OffsetsDialog, self).__init__(parent=parent, flags=Qt.Popup)

        self.info = Info()
        self.log = Log

        axis_list = self.info.getAxisList()

        self.axis_combo = QComboBox()
        for axis in axis_list:
            self.axis_combo.addItem(axis.upper(), axis)

        coords_msg = QLabel("Coordinate relative to workpiece:")
        system_msg = QLabel("Coordinate System:")

        self.coords_input = QLineEdit('0.0000')
        self.coords_input.setInputMask('000009.00000')

        self.system_combo = QComboBox()

        coord_systems = {"P0": "P0 Current",
                         "P1": "P1 G54",
                         "P2": "P2 G55",
                         "P3": "P3 G56",
                         "P4": "P4 G57",
                         "P5": "P5 G58",
                         "P6": "P6 G59",
                         "P7": "P7 G59.1",
                         "P8": "P8 G59.1",
                         "P9": "P9 G59.3"
                         }

        for key, value in OrderedDict(sorted(coord_systems.items(), key=lambda t: t[0])).items():
            self.system_combo.addItem(value, key)

        close_button = QPushButton("Close")
        set_button = QPushButton("Set")

        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        button_layout.addWidget(close_button)
        button_layout.addWidget(set_button)

        main_layout.addWidget(self.axis_combo, alignment=Qt.AlignTop)
        main_layout.addWidget(coords_msg, alignment=Qt.AlignLeft | Qt.AlignTop)
        main_layout.addWidget(self.coords_input, alignment=Qt.AlignTop)
        main_layout.addWidget(system_msg, alignment=Qt.AlignLeft | Qt.AlignTop)
        main_layout.addWidget(self.system_combo, alignment=Qt.AlignBottom)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Regular Offsets")

        set_button.clicked.connect(self.set_method)
        close_button.clicked.connect(self.close_method)

    def set_method(self):
        system = self.system_combo.currentData()
        axis = self.axis_combo.currentData()
        coords = self.coords_input.text()

        offset_mdi = "G10 L20 {} {}{}".format(system, axis, coords)

        if issue_mdi.ok():
            issue_mdi(offset_mdi)
        else:
            self.log.debug("Error issuing MDI: {}".format(issue_mdi.ok.msg))

    def close_method(self):
        self.hide()
