#   Copyright (c) 2019 Kurt Jacobson
#                 2023 TurBoss
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

from qtpy.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog


class MessageDialog(BaseDialog):
    def __init__(self, *args, **kwargs):
        super(MessageDialog, self).__init__(stay_on_top=True)

        self.message = ""

        self.setFixedSize(400, 200)

        self.setWindowTitle("Notification Message")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.close)

        self.text_msg = QLabel()
        self.text_msg.setOpenExternalLinks(False)

        self.text_msg.setText(
            f"""
            <center>
            <p<{self.message}HOLAQUEHASE</p>
            </center>
            """
        )
        self.layout.addWidget(self.text_msg)
        self.layout.addWidget(self.button_box)
    
    def showDialog(self, message):
        
        self.message = message 
        
        self.text_msg.setText(
            f"""
            <center>
            {self.message}
            </center>
            """
        )
        self.show()