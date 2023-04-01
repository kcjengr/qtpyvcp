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

from qtpy.QtCore import Qt, QSortFilterProxyModel, QRegExp
from qtpy.QtGui import QStandardItemModel, QStandardItem, QIcon
from qtpy.QtWidgets import QVBoxLayout, QStackedWidget, QLabel, QListView, QHBoxLayout, QWidget, QPushButton

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.plugins import getPlugin

from datetime import datetime
from time import time

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
        self.clear_button = QPushButton()

        self.all_button.setText("all")
        self.info_button.setText("info")
        self.warn_button.setText("warn")
        self.error_button.setText("error")
        self.debug_button.setText("debug")
        self.clear_button.setText("clear")

        self.all_button.setCheckable(True)
        self.info_button.setCheckable(True)
        self.warn_button.setCheckable(True)
        self.error_button.setCheckable(True)
        self.debug_button.setCheckable(True)

        self.all_button.setChecked(True)
        self.info_button.setChecked(False)
        self.warn_button.setChecked(False)
        self.error_button.setChecked(False)
        self.debug_button.setChecked(False)

        self.clear_button.clicked.connect(self.clear_all_notifications)

        self.button_layout.addWidget(self.all_button)
        self.button_layout.addWidget(self.info_button)
        self.button_layout.addWidget(self.warn_button)
        self.button_layout.addWidget(self.error_button)
        self.button_layout.addWidget(self.debug_button)
        self.button_layout.addWidget(self.clear_button)

        self.notification_name = QLabel()
        self.notification_name.setAlignment(Qt.AlignCenter)
        self.notification_name.setText("All Notifications")

        self.all_notification_view = QListView()

        self.all_notification_model = QStandardItemModel(self.all_notification_view)
        self.all_notification_model_proxy = QSortFilterProxyModel(self.all_notification_view)

        self.all_notification_model_proxy.setSourceModel(self.all_notification_model)

        # self.all_notification_view.setModel(self.all_notification_model)
        self.all_notification_view.setModel(self.all_notification_model_proxy)

        self.all_notifications = list()

        self.main_layout.addWidget(self.notification_name)
        self.main_layout.addWidget(self.all_notification_view)
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
        timestamp = time()
        dt_object = datetime.fromtimestamp(timestamp)

        current_time = str(dt_object)

        msg = 'INFO:\nTIME {}\n  {}'.format(current_time, message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-information'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def on_warn_message(self, message):
        timestamp = time()
        dt_object = datetime.fromtimestamp(timestamp)

        current_time = str(dt_object)

        msg = 'WARNING:\nTIME {}\n  {}'.format(current_time, message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-warning'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def on_error_message(self, message):
        timestamp = time()
        dt_object = datetime.fromtimestamp(timestamp)

        current_time = str(dt_object)

        msg = 'ERROR:\nTIME {}\n  {}'.format(current_time, message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-error'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def on_debug_message(self, message):
        timestamp = time()
        dt_object = datetime.fromtimestamp(timestamp)

        current_time = str(dt_object)

        msg = 'DEBUG\nTIME {}\n  {}'.format(current_time, message)
        notification_item = QStandardItem()
        notification_item.setText(msg)
        notification_item.setIcon(QIcon.fromTheme('dialog-question'))
        notification_item.setEditable(False)
        self.all_notification_model.appendRow(notification_item)

    def show_all_notifications(self):
        self.all_button.setChecked(True)
        self.info_button.setChecked(False)
        self.warn_button.setChecked(False)
        self.error_button.setChecked(False)
        self.debug_button.setChecked(False)

        self.notification_name.setText("All Notifications")
        self.all_notification_model_proxy.setFilterRegExp(None)

    def show_info_notifications(self):
        self.all_button.setChecked(False)
        self.info_button.setChecked(True)
        self.warn_button.setChecked(False)
        self.error_button.setChecked(False)
        self.debug_button.setChecked(False)

        self.notification_name.setText("Information Notifications")
        self.all_notification_model_proxy.setFilterRegExp(QRegExp("INFO", Qt.CaseSensitive,
                                                          QRegExp.FixedString))

    def show_warn_notifications(self):
        self.all_button.setChecked(False)
        self.info_button.setChecked(False)
        self.warn_button.setChecked(True)
        self.error_button.setChecked(False)
        self.debug_button.setChecked(False)

        self.notification_name.setText("Warning Notifications")
        self.all_notification_model_proxy.setFilterRegExp(QRegExp("WANRNING", Qt.CaseSensitive,
                                                          QRegExp.FixedString))

    def show_error_notifications(self):
        self.all_button.setChecked(False)
        self.info_button.setChecked(False)
        self.warn_button.setChecked(False)
        self.error_button.setChecked(True)
        self.debug_button.setChecked(False)

        self.notification_name.setText("Error Notifications")
        self.all_notification_model_proxy.setFilterRegExp(QRegExp("ERROR", Qt.CaseInsensitive,
                                                          QRegExp.FixedString))

    def show_debug_notifications(self):
        self.all_button.setChecked(False)
        self.info_button.setChecked(False)
        self.warn_button.setChecked(False)
        self.error_button.setChecked(False)
        self.debug_button.setChecked(True)

        self.notification_name.setText("Debug Notifications")
        self.all_notification_model_proxy.setFilterRegExp(QRegExp("DEBUG", Qt.CaseSensitive,
                                                          QRegExp.FixedString))

    def clear_all_notifications(self):
        self.all_notification_model.clear()
