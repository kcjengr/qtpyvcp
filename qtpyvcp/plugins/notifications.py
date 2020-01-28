"""
Notifications Plugin
--------------------

Plugin to handle error and status notifications.

Supports evaluating arbitrary python expressions placed in gcode DEBUG statements.


    ::

        example.ngc
        #1 = 12.345

        ; this will set my_label's text to the value of variable #1
        (DEBUG, EVAL[vcp.getWidget{"my_label"}.setText{'%4.2f' % #1}])

        ; this will change the text color of my_label to red
        (DEBUG, EVAL[vcp.getWidget{"my_label"}.setStyleSheet{"color: red"}])
"""

import time
import linuxcnc

from qtpy.QtWidgets import QApplication

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin
from qtpyvcp.lib.native_notification import NativeNotification
from qtpyvcp.lib.dbus_notification import DBusNotification

LOG = getLogger(__name__)
STATUS = getPlugin('status')


class Notifications(DataPlugin):
    """
    Notification data plugin

    Args:
        enabled (bool, optional):                      Enable or disable notification popups (Default = True)
        mode (str, optional):                          native or dbus (Default = 'native')
        max_messages (int, optional)                   Max number of notification popups to show.
        persistent (bool, optional):                   Save notifications on shutdown (Default = True)
    """
    def __init__(self, enabled=True, mode="native", max_messages=5,
                 persistent=True, **kwargs):
        super(Notifications, self).__init__()

        self.enabled = enabled
        self.mode = mode
        self.max_messages = max_messages

        self.error_channel = linuxcnc.error_channel()

        self.messages = []
        self.notification_dispatcher = None

        self.persistent = persistent

        self.data_manager = getPlugin('persistent_data_manager')

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

    def captureMessage(self, m_type, msg):

        if self.enabled:
            self.notification_dispatcher.setNotify(m_type, msg)

        self.messages.append({'timestamp': time.time(),
                              'message_type': m_type,
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

        kind, msg_text = error
        msg_text = msg_text.strip()

        message_words = msg_text.split(' ')

        index = 1
        max_words = 5
        tmp_message = list()

        for word in message_words:
            tmp_message.append(word)
            if index == max_words:
                tmp_message.append('\n')
                index = 1
            else:
                index += 1

        msg = ' '.join(tmp_message)

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

            if msg_text.lower().startswith('eval['):
                exp = msg_text[5:].strip(']')
                exp = exp.replace('{', '(').replace('}', ')')

                LOG.debug("Evaluating gcode DEBUG expression: '%s'", exp)

                try:
                    app = QApplication.instance()
                    eval(exp, {"vcp": app})
                except Exception:
                    LOG.exception("Error evaluating DEBUG expression: '%s'", exp)

            else:
                self.info_message.setValue(msg)
                self.captureMessage('info', msg)
                LOG.info(msg)

        else:
            self.info_message.setValue(msg)
            self.captureMessage('info', msg)
            LOG.error(msg)

    def initialise(self):

        if self.enabled:
            if self.mode == "native":
                self.notification_dispatcher = NativeNotification()
                self.notification_dispatcher.maxMessages = self.max_messages
            elif self.mode == "dbus":
                self.notification_dispatcher = DBusNotification("qtpyvcp")
            else:
                raise Exception("error notification mode {}".format(self.mode))

        if self.persistent:
            self.messages = self.data_manager.getData('messages', [])

        self.startTimer(200)

    def terminate(self):
        if self.persistent:
            self.data_manager.setData('messages', self.messages)
