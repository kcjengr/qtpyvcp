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
from qtpy.QtWidgets import QVBoxLayout, QStackedWidget, QListView, QLabel, QHBoxLayout, QWidget, QPushButton

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.plugins import getPlugin


class NotificationWidget(QWidget, VCPWidget):
    def __init__(self, parent=None):
        super(NotificationWidget, self).__init__(parent)
        self.notification_channel = getPlugin("notifications")

        self.main_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.all_button = QPushButton()
        self.info_button = QPushButton()
        self.warn_button = QPushButton()
        self.error_button = QPushButton()
        self.debug_button = QPushButton()

        self.all_button.setText("all")
        self.info_button.setText("info")
        self.warn_button.setText("warn")
        self.error_button.setText("error")
        self.debug_button.setText("debug")

        self.button_layout.addWidget(self.all_button)
        self.button_layout.addWidget(self.info_button)
        self.button_layout.addWidget(self.warn_button)
        self.button_layout.addWidget(self.error_button)
        self.button_layout.addWidget(self.debug_button)

        self.notification_name = QLabel()

        self.all_notification_view = QListView()
        self.all_notification_proxyview = QListView()

        self.all_notification_model = QStandardItemModel(self.all_notification_view)

        # self.all_notification_view.setModel(self.all_notification_model)
        self.all_notification_proxyview.setModel(self.all_notification_model)

        self.all_notifications = list()

        self.main_layout.addWidget(self.notification_name)
        self.main_layout.addWidget(self.all_notification_proxyview)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)

        self.notification_channel.info_message.notify(self.on_info_message)
        self.notification_channel.warn_message.notify(self.on_warn_message)
        self.notification_channel.error_message.notify(self.on_error_message)
        self.notification_channel.debug_message.notify(self.on_debug_message)

        self.all_button.clicked.connect(self.show_all_notifications)
        self.info_button.clicked.connect(self.show_info_notifications)
        self.warn_button.clicked.connect(self.show_warn_notifications)
        self.error_button.clicked.connect(self.show_error_notifications)
        self.debug_button.clicked.connect(self.show_debug_notifications)

    def on_info_message(self, message):
        msg = 'INFO : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-information'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def on_warn_message(self, message):
        msg = 'WARNING : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-warning'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def on_error_message(self, message):
        msg = 'ERROR : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-error'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def on_debug_message(self, message):
        msg = 'DEBUG : {}'.format(message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-question'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def show_all_notifications(self):
        self.notification_name.setText("All Notifications")

    def show_info_notifications(self):
        self.notification_name.setText("Information Notifications")

    def show_warn_notifications(self):
        self.notification_name.setText("Warning Notifications")

    def show_error_notifications(self):
        self.notification_name.setText("Error Notifications")

    def show_debug_notifications(self):
        self.notification_name.setText("Debug Notifications")
