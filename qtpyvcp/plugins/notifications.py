"""
Notifications
-------------

Plugin to handle global notifications.
"""
import os
import json
import time
import linuxcnc

from qtpy.QtCore import QTimer

from qtpyvcp.utilities.misc import normalizePath

from qtpyvcp.plugins import DataPlugin, DataChannel
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin

from qtpyvcp.lib.notify import Notification, Urgency

LOG = getLogger(__name__)
STATUS = getPlugin('status')


class Notifications(DataPlugin):
    def __init__(self, persistent=True, persistent_file='.qtpyvcp_messages.json'):
        super(Notifications, self).__init__()

        self.error_channel = linuxcnc.error_channel()

        self.messages = []

        self.desktop_notifier = Notification("Demo")
        self.desktop_notifier.setUrgency(Urgency.NORMAL)
        self.desktop_notifier.setCategory("device")

        self.persistant = persistent
        self.persistent_file = normalizePath(path=persistent_file,
                                           base=os.getenv('CONFIG_DIR', '~/'))

        self.timer = QTimer()
        self.timer.timeout.connect(self.onTimeout)

        self._count = 0

    @DataChannel
    def debug_message(self, chan):
        return chan.value or ''

    @debug_message.setter
    def debug_message(self, chan, msg):
        self.captureMessage('debug', msg)
        chan.value = msg
        chan.signal.emit(msg)

    @DataChannel
    def info_message(self, chan):
        return chan.value or ''

    @info_message.setter
    def info_message(self, chan, msg):
        self.captureMessage('info', msg)
        chan.value = msg
        chan.signal.emit(msg)

    @DataChannel
    def warn_message(self, chan):
        return chan.value or ''

    @warn_message.setter
    def warn_message(self, chan, msg):
        self.captureMessage('warn', msg)
        chan.value = msg
        chan.signal.emit(msg)

    @DataChannel
    def error_message(self, chan):
        return chan.value or ''

    @error_message.setter
    def error_message(self, chan, msg):
        self.captureMessage('error', msg)
        chan.value = msg
        chan.signal.emit(msg)

    def captureMessage(self, typ, msg):
        self.showDesktopNotification(typ, msg)
        self.messages.append({'timestamp': time.time(),
                              'type': typ,
                              'message': msg,
                              'file': STATUS.file.getValue(),
                              'task_mode': STATUS.task_mode.getString(),
                              'task_state': STATUS.task_state.getString(),
                              'interp_mode': STATUS.interp_state.getString(),
                              }
                             )

    def showDesktopNotification(self, typ, msg):
        icon = {'error': 'dialog-error',
                'warn': 'dialog-warning',
                'info': 'dialog-information',
                'debug': 'dialog-information'}.get(typ, 'dialog-error')
        self.desktop_notifier.show(title=typ.capitalize(), body=msg, icon=icon)

    def initialise(self):
        if self.persistant and os.path.isfile(self.persistent_file):
            with open(self.persistent_file, 'r') as fh:
                try:
                    self.messages = json.loads(fh.read())
                except:
                    LOG.exception("Error loading messages from JSON file")

        self.timer.start(200)

    def terminate(self):
        if self.persistant:
            LOG.debug("Saving messages to %s", self.persistent_file)
            with open(self.persistent_file, 'w') as fh:
                fh.write(json.dumps(self.messages, indent=4, sort_keys=True))

    def onTimeout(self):
        error = self.error_channel.poll()

        if not error:
            return

        kind, msg = error

        if msg == "" or msg is None:
            msg = "Unknown error!"

        if kind in [linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR]:
            self.error_message.setValue(msg)
            LOG.error(msg)

        elif kind in [linuxcnc.NML_TEXT, linuxcnc.OPERATOR_TEXT]:
            self.debug_message.setValue(msg)
            LOG.debug(msg)

        elif kind in [linuxcnc.NML_DISPLAY, linuxcnc.OPERATOR_DISPLAY]:
            self.info_message.setValue(msg)
            LOG.info(msg)

        else:
            self.info_message.setValue(msg)
            LOG.error(msg)
