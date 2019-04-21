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

from qtpy.QtWidgets import QVBoxLayout, QStackedWidget, QListView, QLabel,\
    QHBoxLayout, QWidget

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.plugins import getPlugin


class NotificationWidget(QWidget, VCPWidget):
    def __init__(self, parent=None):
        super(NotificationWidget, self).__init__(parent)
        self.notification = getPlugin("notifications")

        self.main_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.notification_name = QLabel("TEST")

        self.notification_list = QListView()

        self.stack = QStackedWidget()

        # self.stack.addWidget(self.stack1)
        # self.stack.addWidget(self.stack2)
        # self.stack.addWidget(self.stack3)

        self.main_layout.addWidget(self.notification_name)
        self.main_layout.addWidget(self.notification_list)
        self.main_layout.addLayout(self.button_layout)
