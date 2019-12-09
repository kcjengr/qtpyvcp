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
from pprint import pprint

from qtpy import uic
from qtpy.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel


class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__()

        self.ui_file = kwargs.get('ui_file')

        if self.ui_file:
            uic.loadUi(self.ui_file, self)
        else:

            self.setFixedSize(600, 200)

            self.setWindowTitle("About QtPyVCP")

            self.layout = QVBoxLayout()
            self.setLayout(self.layout)

            self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            self.button_box.accepted.connect(self.close)

            self.about_text = QLabel()

            self.about_text.setText(
                """
                <center>
                QtPyVCP is a Qt and Python based framework for LinuxCNC.<br />
                Copyright (c) 2019 Kurt Jacobson<br />
                https://qtpyvcp.kcjengr.com/
                </center>
                """
            )

            self.layout.addWidget(self.about_text)
            self.layout.addWidget(self.button_box)

