#!/usr/bin/env python3

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

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton,
                            QVBoxLayout, QApplication,
                            QDialog, QScrollArea, QPlainTextEdit, QSizePolicy)

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog


class Message(QWidget):
    def __init__(self, title, message, parent=None):
        super(Message, self).__init__(parent)
        
        self.mainLayout = QHBoxLayout()
        
        
        
        self.setLayout(self.mainLayout)
        
        self.setMaximumWidth(600)
        self.setMaximumHeight(400)
        self.setMinimumWidth(300)
        
        self.messageLayout = QVBoxLayout()
        
        self.titleLabel = QLabel(title, self)
        self.titleLabel.setStyleSheet(
            """
            font-family: 'Roboto', sans-serif;
            font-size: 14px; font-weight: bold;
            padding: 0;
            """)
        
        self.messageLabel = QPlainTextEdit(message, self)
        self.messageLabel.setReadOnly(True)
        self.messageLabel.setStyleSheet(
            """
            font-family: 'Roboto', sans-serif;
            font-size: 12px;
            font-weight: normal;
            padding: 0;
            """)
        
        self.messageArea = QScrollArea()
        self.messageArea.setWidget(self.messageLabel)
        
        self.buttonClose = QPushButton(self)
        self.buttonClose.setIcon(QIcon.fromTheme("window-close"))
        self.buttonClose.setFixedSize(48, 48)

        self.messageLayout.addWidget(self.titleLabel)
        self.messageLayout.addWidget(self.messageArea)
        
        self.layout().addLayout(self.messageLayout)
        self.layout().addWidget(self.buttonClose)


class NativeNotification(BaseDialog):
    signNotifyClose = Signal(str)

    def __init__(self, parent=None):
        super(NativeNotification, self).__init__(parent=parent, stay_on_top=True, frameless=True)
        time = datetime.now()

        current_time = "{}:{}".format(time.hour, time.minute)

        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)

        self.resolution = QApplication.primaryScreen()
        self.screenWidth = self.resolution.size().width()
        self.screenHeight = self.resolution.size().height()


        w_size = self.frameSize()
        self.move(self.screenWidth - w_size.width(), 0)
        
        self.maxMessages = 5
        self.nMessages = 0
        self.activeMessages = list()
        self.mainLayout = QVBoxLayout(self)

    def setNotify(self, title, message):
                
        m = Message(title, message, self)
        self.mainLayout.insertWidget(0, m)
        self.mainLayout.setAlignment(Qt.AlignRight)
        
        m.buttonClose.clicked.connect(self.onClicked)
        self.nMessages += 1

        if self.nMessages > self.maxMessages:
            prev_message = self.activeMessages.pop(0)
            self.mainLayout.removeWidget(prev_message)
            prev_message.deleteLater()
            self.nMessages -= 1

        self.activeMessages.append(m)
        
        self.setMinimumSize(self.sizeHint())
        self.adjustSize()
        self.setMinimumSize(self.minimumSizeHint())

        w_size = self.frameSize()
        self.move(self.screenWidth - w_size.width(), 0)
        
        self.show()
        self.raise_()

    def onClicked(self):
        m = self.sender().parent()
        
        self.mainLayout.removeWidget(m)
        self.activeMessages.remove(m)
        
        m.deleteLater()
        
        self.nMessages -= 1
        
        self.setMinimumSize(self.sizeHint())
        self.adjustSize()
        self.setMinimumSize(self.minimumSizeHint())
        
        if self.nMessages == 0:
            self.hide()

    def popNotify(self):
        """Removes the last notification in the list"""
        pass


class Example(QWidget):
    counter = 0

    def __init__(self, parent=None):
        super(Example, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        btn = QPushButton("Send Notify", self)
        self.layout().addWidget(btn)

        self.notification = NativeNotification(parent=self)
        btn.clicked.connect(self.notify)
        self.index = 0

    def notify(self):
        self.notification.setNotify("BroadCast System",
                                    "This is a test of the broadcast system.{}".format(self.index))
        self.index += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()
    w.show()
    sys.exit(app.exec_())
