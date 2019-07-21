"""
Notifications Plugin
--------------------

Plugin to handle error status notifications.
"""
import os
import json
import time
import linuxcnc

from qtpyvcp.utilities.misc import normalizePath

from qtpyvcp.plugins import DataPlugin, DataChannel
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin

LOG = getLogger(__name__)
STATUS = getPlugin('status')


class Notifications(DataPlugin):
    def __init__(self, persistent=True, persistent_file='.qtpyvcp_messages.json'):
        super(Notifications, self).__init__()

        self.error_channel = linuxcnc.error_channel()

        self.messages = []

        self.persistant = persistent
        self.persistent_file = normalizePath(path=persistent_file,
                                             base=os.getenv('CONFIG_DIR', '~/'))

    @DataChannel
    def debug_message(self, chan):
        return chan.value or ''

    @DataChannel
    def info_message(self, chan):
        return chan.value or ''

    @DataChannel
    def warn_message(self, chan):
        return chan.value or ''

    @DataChannel
    def error_message(self, chan):
        return chan.value or ''

    def captureMessage(self, typ, msg):
        self.messages.append({'timestamp': time.time(),
                              'message_type': typ,
                              'message_text': msg,
                              'operator_id': '',
                              'loaded_file': STATUS.file.getValue(),
                              'task_mode': STATUS.task_mode.getString(),
                              'task_state': STATUS.task_state.getString(),
                              'interp_mode': STATUS.interp_state.getString(),
                              }
                             )

    def timerEvent(self, event):
        """Called every 200ms to poll error channel"""
        error = self.error_channel.poll()

        if not error:
            return

        kind, msg = error

        if msg == "" or msg is None:
            msg = "No message text set."

        if kind in [linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR]:
            self.error_message.setValue(msg)
            self.captureMessage('error', msg)
            LOG.error(msg)

        elif kind in [linuxcnc.NML_TEXT, linuxcnc.OPERATOR_TEXT]:
            self.debug_message.setValue(msg)
            self.captureMessage('debug', msg)
            LOG.debug(msg)

        elif kind in [linuxcnc.NML_DISPLAY, linuxcnc.OPERATOR_DISPLAY]:
            self.info_message.setValue(msg)
            self.captureMessage('info', msg)
            LOG.info(msg)

        else:
            self.info_message.setValue(msg)
            self.captureMessage('info', msg)
            LOG.error(msg)

    def initialise(self):
        if self.persistant and os.path.isfile(self.persistent_file):
            with open(self.persistent_file, 'r') as fh:
                try:
                    self.messages = json.loads(fh.read())
                except:
                    LOG.exception("Error loading messages from JSON file")

        self.startTimer(200)

    def terminate(self):
        if self.persistant:
            LOG.debug("Saving messages to %s", self.persistent_file)
            with open(self.persistent_file, 'w') as fh:
                fh.write(json.dumps(self.messages, indent=4, sort_keys=True))
