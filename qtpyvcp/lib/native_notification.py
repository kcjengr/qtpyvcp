#!/usr/bin/env python

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

import sys

from datetime import datetime

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QDesktopWidget, QVBoxLayout, QApplication, QDialog


class Message(QWidget):
    def __init__(self, title, message, parent=None):
        super(Message, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.titleLabel = QLabel(title, self)
        self.titleLabel.setStyleSheet(
            """
            font-family: 'Roboto', sans-serif;
            font-size: 14px; font-weight: bold;
            padding: 0;
            """)
        self.messageLabel = QLabel(message, self)
        self.messageLabel.setStyleSheet(
            """
            font-family: 'Roboto', sans-serif;
            font-size: 12px;
            font-weight: normal;
            padding: 0;
            """)
        self.buttonClose = QPushButton(self)
        self.buttonClose.setIcon(QIcon.fromTheme("window-close"))
        self.buttonClose.setFixedSize(32, 32)
        self.layout().addWidget(self.titleLabel, 0, 0)
        self.layout().addWidget(self.messageLabel, 1, 0)
        self.layout().addWidget(self.buttonClose, 0, 1, 2, 1)


class NativeNotification(QDialog):
    signNotifyClose = Signal(str)

    def __init__(self, parent=None):
        super(NativeNotification, self).__init__(parent=parent)
        time = datetime.now()

        current_time = "{}:{}".format(time.hour, time.minute)

        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)

        resolution = QDesktopWidget().screenGeometry(-1)
        screenWidth = resolution.width()
        screenHeight = resolution.height()

        self.nMessages = 0
        self.mainLayout = QVBoxLayout(self)
        self.move(screenWidth, 0)

    def setNotify(self, title, message):
        m = Message(title, message, self)
        self.mainLayout.addWidget(m)
        m.buttonClose.clicked.connect(self.onClicked)
        self.nMessages += 1
        self.show()
        self.raise_()

    def onClicked(self):
        self.mainLayout.removeWidget(self.sender().parent())
        self.sender().parent().deleteLater()
        self.nMessages -= 1
        self.adjustSize()
        if self.nMessages == 0:
            self.close()


class Example(QWidget):
    counter = 0

    def __init__(self, parent=None):
        super(Example, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        btn = QPushButton("Send Notify", self)
        self.layout().addWidget(btn)

        self.notification = NativeNotification()
        btn.clicked.connect(self.notify)

    def notify(self):
        self.notification.setNotify("BroadCast System",
                                    "This is a test of the broadcast system.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()
    w.show()
    sys.exit(app.exec_())
