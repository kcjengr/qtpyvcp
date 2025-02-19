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

import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.utilities.pyside_ui_loader import PySide6Ui


class AboutDialog(BaseDialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(stay_on_top=True)

        self.ui_file = kwargs.get('ui_file')

        if self.ui_file:
            file_path = os.path.join(os.path.dirname(__file__), self.ui_file)
            #ui_file = QFile(file_path)
            #ui_file.open(QFile.ReadOnly)
            
            #loader = QUiLoader()
            #self.ui = loader.load(ui_file, self)
            form_class, base_class = PySide6Ui(file_path).load()
            form = form_class()
            form.setupUi(self)

        else:

            self.setFixedSize(600, 200)

            self.setWindowTitle("About QtPyVCP")

            self.layout = QVBoxLayout()
            self.setLayout(self.layout)

            self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            self.button_box.accepted.connect(self.close)

            self.about_text = QLabel()
            self.about_text.setOpenExternalLinks(True)
            self.about_text.setText(
                """
                <center>
                QtPyVCP is a Qt and Python based framework for LinuxCNC.<br />
                Copyright (c) 2018 - 2024 Kurt Jacobson<br />
                <a href="https://www.qtpyvcp.com">https://www.qtpyvcp.com</a>
                </center>
                """
            )

            self.layout.addWidget(self.about_text)
            self.layout.addWidget(self.button_box)

