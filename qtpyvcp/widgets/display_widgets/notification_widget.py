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

from qtpy.QtGui import QStandardItemModel, QStandardItem, QIcon
from qtpy.QtWidgets import QVBoxLayout, QStackedWidget, QListView, QLabel, QHBoxLayout, QWidget

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.plugins import getPlugin


class NotificationWidget(QWidget, VCPWidget):
    def __init__(self, parent=None):
        super(NotificationWidget, self).__init__(parent)
        self.notification_channel = getPlugin("notifications")

        self.main_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.notification_name = QLabel()
        self.notification_name.setText("TEST")

        self.info_notification_list = QListView()
        self.warn_notification_list = QListView()
        self.error_notification_list = QListView()
        self.debug_notification_list = QListView()

        self.info_notification_model = QStandardItemModel(self.info_notification_list)
        # self.info_notification_model.itemChanged.connect(self.info_message)

        self.warn_notification_model = QStandardItemModel(self.warn_notification_list)
        # self.warn_notification_model.itemChanged.connect(self.info_message)

        self.error_notification_model = QStandardItemModel(self.error_notification_list)
        # self.error_notification_model.itemChanged.connect(self.info_message)

        self.debug_notification_model = QStandardItemModel(self.debug_notification_list)
        # self.debug_notification_model.itemChanged.connect(self.info_message)

        self.notification_channel.info_message.notify(self.on_info_message)
        self.notification_channel.warn_message.notify(self.on_warn_message)
        self.notification_channel.error_message.notify(self.on_error_message)
        self.notification_channel.debug_message.notify(self.on_debug_message)

        self.info_notification_list.setModel(self.info_notification_model)
        self.warn_notification_list.setModel(self.warn_notification_model)
        self.error_notification_list.setModel(self.error_notification_model)
        self.debug_notification_list.setModel(self.debug_notification_model)

        self.info_notifications = list()
        self.warn_notifications = list()
        self.error_notifications = list()
        self.debug_notifications = list()

        self.stack = QStackedWidget()

        self.stack.addWidget(self.info_notification_list)
        self.stack.addWidget(self.warn_notification_list)
        self.stack.addWidget(self.error_notification_list)
        self.stack.addWidget(self.debug_notification_list)

        self.main_layout.addWidget(self.notification_name)
        self.main_layout.addWidget(self.stack)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)

    def on_info_message(self, message):
        msg = 'INFO : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-information'))
        notification_item.setEditable(False)
        # notification_item.setCheckable(True)
        self.info_notification_model.appendRow(notification_item)

    def on_warn_message(self, message):
        msg = 'WARNING : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-warning'))
        notification_item.setEditable(False)
        # notification_item.setCheckable(True)
        self.info_notification_model.appendRow(notification_item)

    def on_error_message(self, message):
        msg = 'ERROR : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-error'))
        notification_item.setEditable(False)
        # notification_item.setCheckable(True)
        self.info_notification_model.appendRow(notification_item)

    def on_debug_message(self, message):
        msg = 'DEBUG : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-question'))
        notification_item.setEditable(False)
        # notification_item.setCheckable(True)
        self.info_notification_model.appendRow(notification_item)

