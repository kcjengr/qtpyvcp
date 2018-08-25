# -*- coding: utf-8 -*-
import os
import threading
import ctypes
import time

from .qt import QtCore
from .qt.QtWidgets import (QTextEdit)
from .qt.QtGui import (QFontMetrics, QTextCursor)

from .interpreter import PythonInterpreter
from .stream import Stream
from .syntaxhighlighter import PythonHighlighter
from .extensions.extension import ExtensionManager
from .extensions.commandhistory import CommandHistory
from .extensions.autocomplete import AutoComplete, COMPLETE_MODE


class BaseConsole(QTextEdit):
    key_pressed_signal = QtCore.Signal(object)
    post_key_pressed_signal = QtCore.Signal(object)
    set_complete_mode_signal = QtCore.Signal(int)

    def __init__(self, parent = None):
        super(BaseConsole, self).__init__(parent)
        self._buffer_pos = 0
        self._prompt_pos = 0
        self._tab_chars = 4 * ' '
        self._ctrl_d_exits = False
        self._copy_buffer = ''

        self.stdin = Stream()
        self.stdout = Stream()
        self.stdout.write_event.connect(self._stdout_data_handler)

        font = self.document().defaultFont()
        font.setFamily("Courier New")
        font_width = QFontMetrics(font).width('M')
        self.document().setDefaultFont(font)
        geometry = self.geometry()
        geometry.setWidth(font_width*80+20)
        geometry.setHeight(font_width*40)
        self.setGeometry(geometry)
        self.resize(font_width*80+20, font_width*40)

        self.extensions = ExtensionManager(self)
        self.extensions.install(CommandHistory)
        self.extensions.install(AutoComplete)

    def insertFromMimeData(self, mime_data):
        if mime_data.hasText():
            self._keep_cursor_in_buffer()
            self.evaluate_buffer(mime_data.text(), echo_lines = True)

    def keyPressEvent(self, event):
        key = event.key()
        event.ignore()
        intercepted = False

        self.key_pressed_signal.emit(event)

        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            intercepted = self.handle_enter_key(event)
        elif key == QtCore.Qt.Key_Backspace:
            intercepted = self.handle_backspace_key(event)
        elif key == QtCore.Qt.Key_Home:
            intercepted = self.handle_home_key(event)
        elif key == QtCore.Qt.Key_Tab:
            intercepted = self.handle_tab_key(event)
        elif key == QtCore.Qt.Key_Up:
            intercepted = self.handle_up_key(event)
        elif key == QtCore.Qt.Key_Down:
            intercepted = self.handle_down_key(event)
        elif key == QtCore.Qt.Key_Left:
            intercepted = self.handle_left_key(event)
        elif key == QtCore.Qt.Key_Right:
            pass
        elif key == QtCore.Qt.Key_D:
            intercepted = self.handle_d_key(event)
        elif key == QtCore.Qt.Key_C:
            intercepted = self.handle_c_key(event)

        # Make sure that we can't move the cursor outside of the editing buffer
        # If outside buffer and no modifiers used move the cursor back into to
        # the buffer
        if not event.modifiers() and not self._in_buffer():
            self._keep_cursor_in_buffer()

        # Call the TextEdit keyPressEvent for the events that are not
        # intercepted
        if not intercepted:
            super(BaseConsole, self).keyPressEvent(event)
        else:
            event.accept()

        self.post_key_pressed_signal.emit(event)

    def handle_enter_key(self, event):
        if not event.isAccepted():
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.EndOfLine)
            self.setTextCursor(cursor)
            self._parse_buffer()

        return False

    def handle_backspace_key(self, event):
        intercepted = False

        if not self._in_buffer():
            intercepted = True
        else:
            if self._get_buffer().endswith(self._tab_chars):
                for i in range(len(self._tab_chars) - 1):
                    self.textCursor().deletePreviousChar()

        return intercepted

    def handle_tab_key(self, event):
        if not event.isAccepted():
            self._insert_in_buffer(self._tab_chars)

        return True

    def handle_home_key(self, event):
        self._keep_cursor_in_buffer()
        return True

    def handle_up_key(self, event):
        return True

    def handle_down_key(self, event):
        return True

    def handle_left_key(self, event):
        intercepted = False

        if not self._in_buffer():
            intercepted = True

        return intercepted

    def handle_d_key(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier and self._ctrl_d_exits:
            self._close()
        elif event.modifiers() == QtCore.Qt.ControlModifier:
            msg = "\nCan't use CTRL-D to exit, you have to exit the "
            msg += "application !\n"
            self._insert_prompt(msg)

        return False

    def handle_c_key(self, event):
        intercepted = False

        # Do not intercept so that the event is forwarded to the base class
        # can handle it. In this case for copy that is: CTRL-C
        if event.modifiers() == QtCore.Qt.ControlModifier:
            self._handle_ctrl_c()

        return intercepted

    def _keep_cursor_in_buffer(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _in_buffer(self):
        buffer_pos = self.textCursor().position()
        return buffer_pos > self._prompt_pos

    def _insert_prompt(self, prompt, lf=False, keep_buffer=False):
        if keep_buffer:
            self._copy_buffer = self._get_buffer()

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(prompt)
        self._prompt_pos = cursor.position()
        self.ensureCursorVisible()

        if lf:
            self.stdin.write(os.linesep)

    def _insert_welcome_message(self, message):
        self._insert_prompt(message)

    def _get_buffer(self):
        buffer_pos = self.textCursor().position()
        return str(self.toPlainText()[self._prompt_pos:buffer_pos])

    def _clear_buffer(self):
        self.textCursor().clearSelection()
        buffer_pos = self.textCursor().position()

        for i in range(self._prompt_pos,buffer_pos):
            self.textCursor().deletePreviousChar()

    def _insert_in_buffer(self, text):
        self.ensureCursorVisible()
        self.textCursor().insertText(text)

    # Asbtract
    def get_completions(self, line):
        return ['No completion support available']

    def set_auto_complete_mode(self, mode):
        self.set_complete_mode_signal.emit(mode)

    def _parse_buffer(self):
        cmd = self._get_buffer()
        self.stdin.write(cmd + os.linesep)

    def _stdout_data_handler(self, data):
        self._insert_prompt(data)

        if len(self._copy_buffer) > 0:
            self._insert_in_buffer(self._copy_buffer)
            self._copy_buffer = ''

    # Abstract
    def _close(self):
        self.stdin.write('EOF\n')

    def _evaluate_buffer(self):
        _buffer = str(self.sender().parent().parent().toPlainText())
        self.evaluate_buffer(_buffer)

    # Abstract
    def evaluate_buffer(self, _buffer, echo_lines = False):
        print(_buffer)

    def set_tab(self, chars):
        self._tab_chars = chars

    def ctrl_d_exits_console(self, b):
        self._ctrl_d_exits = b

    # Abstract
    def _handle_ctrl_c(self):
        pass

class PythonConsole(BaseConsole):
    def __init__(self, parent = None, local = {}):
        super(PythonConsole, self).__init__(parent)
        self.highlighter = PythonHighlighter(self.document())
        self.interpreter = PythonInterpreter(self.stdin, self.stdout, local=local)
        self.set_auto_complete_mode(COMPLETE_MODE.DROPDOWN)
        self._thread = None

    def _close(self):
        self.interpreter.exit()
        self.close()

    def _handle_ctrl_c(self):
        _id = threading.current_thread().ident

        if self._thread:
            _id = self._thread.ident

        if _id:
            _id, exobj = ctypes.c_long(_id), ctypes.py_object(KeyboardInterrupt)
            ctypes.pythonapi.PyThreadState_SetAsyncExc(_id, exobj)
            time.sleep(0.1)

    def closeEvent(self, event):
        self._close()
        event.accept()

    def evaluate_buffer(self, _buffer, echo_lines = False):
        self.interpreter.set_buffer(_buffer)
        if echo_lines:
            self.stdin.write('%%eval_lines\n')
        else:
            self.stdin.write('%%eval_buffer\n')

    def get_completions(self, line):
        return self.interpreter.get_completions(line)

    def push_local_ns(self, name, value):
        self.interpreter.local_ns[name] = value

    def repl_nonblock(self):
        return self.interpreter.repl_nonblock()

    def repl(self):
        return self.interpreter.repl()

    def eval_in_thread(self):
        self._thread = threading.Thread(target = self.repl)
        self._thread.start()
        return self._thread
