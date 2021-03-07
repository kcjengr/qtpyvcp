#   Copyright (c) 2019 Kurt Jacobson
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

from qtpy import uic
from qtpy.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.widgets.base_widgets.bar_indicator import BarIndicatorBase



class LoadingDialog(BaseDialog):
    def __init__(self, *args, **kwargs):
        super(LoadingDialog, self).__init__(stay_on_top=True)

        self.ui_file = kwargs.get('ui_file')

        if self.ui_file:
            uic.loadUi(self.ui_file, self)
        else:

            self.setFixedSize(600, 100)

            self.setWindowTitle("Loading File")

            self.layout = QVBoxLayout()
            self.setLayout(self.layout)

            self.loading_text = QLabel()
            self.loading_text.setText(
                """
                <center>Loading File</center>
                """
                )
            
            self.loading_bar = BarIndicatorBase()

            self.layout.addWidget(self.loading_text)
            self.layout.addWidget(self.loading_bar)

