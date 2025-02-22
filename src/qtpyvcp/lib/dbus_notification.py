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

import os
import dbus
from collections import OrderedDict

# Set up logging
from qtpyvcp.utilities import logger

log = logger.getLogger(__name__)

DBusQtMainLoop = None
try:
    from PySide6.QtDBus import QDBusConnection
except ImportError:
    log.warning("Could not import DBusQtMainLoop, is package 'python-dbus.mainloop.pyqt5' installed?")

APP_NAME = ''
DBUS_IFACE = None
NOTIFICATIONS = {}


class Urgency:
    """freedesktop.org notification urgency levels"""
    LOW, NORMAL, CRITICAL = list(range(3))


class UninitializedError(RuntimeError):
    """Error raised if you try to show an error before initializing"""
    pass


def init(app_name):
    """Initializes the DBus connection"""
    global APP_NAME, DBUS_IFACE
    APP_NAME = app_name

    name = "org.freedesktop.Notifications"
    path = "/org/freedesktop/Notifications"
    interface = "org.freedesktop.Notifications"

    mainloop = None
    if DBusQtMainLoop is not None:
        mainloop = DBusQtMainLoop(set_as_default=True)

    bus = dbus.SessionBus(mainloop)
    proxy = bus.get_object(name, path)
    DBUS_IFACE = dbus.Interface(proxy, interface)

    if mainloop is not None:
        # We have a mainloop, so connect callbacks
        DBUS_IFACE.connect_to_signal('ActionInvoked', _onActionInvoked)
        DBUS_IFACE.connect_to_signal('NotificationClosed', _onNotificationClosed)


def _onActionInvoked(nid, action):
    """Called when a notification action is clicked"""
    nid, action = int(nid), str(action)
    try:
        notification = NOTIFICATIONS[nid]
    except KeyError:
        # must have been created by some other program
        return
    notification._onActionInvoked(action)


def _onNotificationClosed(nid, reason):
    """Called when the notification is closed"""
    nid, reason = int(nid), int(reason)
    try:
        notification = NOTIFICATIONS[nid]
    except KeyError:
        # must have been created by some other program
        return
    notification._onNotificationClosed(notification)
    del NOTIFICATIONS[nid]


class DBusNotification(object):
    """Notification object"""

    id = 0
    timeout = -1
    _onNotificationClosed = lambda *args: None

    def __init__(self, appname):
        """
            Initializes a new notification object.

        """
        init(appname)

        self.title = ""  # title of the notification
        self.body = ""  # Fix for legacy use
        self.icon = ""  # the path to the icon to use
        self.timeout = -1  # time in ms before the notification disappears

        self.hints = {}  # dict of various display hints
        self.actions = OrderedDict()  # actions names and their callbacks
        self.data = {}  # arbitrary user data

    def show(self, title, body="", icon="", timeout=-1):
        """
        Args:
            title (str):              The title of the notification
            body (str, optional):     The body text of the notification
            icon (str, optional):     The icon to display with the notification
            timeout (TYPE, optional): The time in ms before the notification hides, -1 for default, 0 for never:return:
        """

        self.title = title
        self.body = body
        self.icon = icon  # the path to the icon to use
        self.timeout = timeout  # time in ms before the notification disappears

        if DBUS_IFACE is None:
            raise UninitializedError("You must call 'notify.init()' before 'notify.show()'")

        """Asks the notification server to show the notification"""
        nid = DBUS_IFACE.Notify(APP_NAME,
                                self.id,
                                self.icon,
                                self.title,
                                self.body,
                                self._makeActionsList(),
                                self.hints,
                                self.timeout,
                                )

        self.id = int(nid)

        NOTIFICATIONS[self.id] = self
        return True

    def setNotify(self, title, message):
        self.show(title, message)

    def close(self):
        """Ask the notification server to close the notification"""
        if self.id != 0:
            DBUS_IFACE.CloseNotification(self.id)

    def onClose(self, callback):
        """Set the callback called when the notification is closed"""
        self._onNotificationClosed = callback

    def setUrgency(self, value):
        """Set the freedesktop.org notification urgency level"""
        if value not in list(range(3)):
            raise ValueError("Unknown urgency level '%s' specified" % value)
        self.hints['urgency'] = dbus.Byte(value)

    def setSoundFile(self, sound_file):
        """Sets a sound file to play when the notification shows"""
        if os.path.isfile(sound_file):
            self.hints['sound-file'] = sound_file

    def setSoundName(self, sound_name):
        """Set a freedesktop.org sound name to play when notification shows"""
        self.hints['sound-name'] = sound_name

    def setIconPath(self, icon_path):
        """Set the URI of the icon to display in the notification"""
        # "image-path" hint should be either a URI (file:// is the only URI
        # schema supported right now) or a freedesktop.org-compliant icon name
        if os.path.isfile(icon_path):
            # it is a file, so format as a URI
            self.hints['image-path'] = 'file://' + icon_path
        else:
            # probably is a icon name
            self.hints['image-path'] = icon_path

    def setQIcon(self, q_icon):
        # ToDO: implement setting image-data from a QIcon
        # The "image-data" hint should be a raw image data structure of
        # signature (iiibiiay) which describes the width, height, rowstride,
        # has alpha, bits per sample, channels and image data respectively.
        raise NotImplementedError

    def setLocation(self, x_pos, y_pos):
        """Sets the location to display the notification"""
        self.hints['x'] = int(x_pos)
        self.hints['y'] = int(y_pos)

    def setCategory(self, category):
        """Sets the the freedesktop.org notification category"""
        self.hints['category'] = category

    def setTimeout(self, timeout):
        """Set the display duration in milliseconds, -1 for default"""
        if not isinstance(timeout, int):
            raise TypeError("Timeout value '%s' was not int" % timeout)
        self.timeout = timeout

    def setHint(self, key, value):
        """Set one of the other hints"""
        self.hints[key] = value

    def addAction(self, action, label, callback, user_data=None):
        """Add an action to the notification.

        Args:
            action (str):               A sort key identifying the action
            label (str):                The text to display on the action button
            callback (bound method):    The method to call when the action is activated
            user_data (any, optional):  Any user data to be passed to the action callback
        """
        self.actions[action] = (label, callback, user_data)

    def _makeActionsList(self):
        """Make the actions array to send over DBus"""
        arr = []
        for action, (label, callback, user_data) in list(self.actions.items()):
            arr.append(action)
            arr.append(label)
        return arr

    def _onActionInvoked(self, action):
        """Called when the user activates a notification action"""
        try:
            label, callback, user_data = self.actions[action]
        except KeyError:
            return

        if user_data is None:
            callback(self, action)
        else:
            callback(self, action, user_data)


# ----------------------- E X A M P L E -----------------------

def onHelp(n, action):
    assert (action == "help"), "Action was not help!"
    print("You clicked Help action")
    n.close()


def onIgnore(n, action, data):
    assert (action == "ignore"), "Action was not ignore!"
    print("You clicked Ignore action")
    print(("Passed user data was: ", data))
    n.close()


def onClose(n):
    print("Notification closed")
    app.quit()


if __name__ == "__main__":
    import sys
    from PySide6.QtCore import QCoreApplication

    app = QCoreApplication(sys.argv)

    # Initialize the DBus connection to the notification server
    # Initialize a new notification object
    n = DBusNotification("Demo")
    n.setUrgency(Urgency.NORMAL)
    n.setCategory("device")
    n.setIconPath("dialog-error")
    # no user data
    n.addAction("help", "Help", onHelp)
    # passing arbitrary user data to the callback
    n.addAction("ignore", "Ignore", onIgnore, 12345)
    n.onClose(onClose)

    n.show("Demo Notification",
           "This notification is very important as it " +
           "notifies you that notifications are working.",
           timeout=3000)

    app.exec_()
