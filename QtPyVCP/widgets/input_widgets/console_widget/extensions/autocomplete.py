# -*- coding: utf-8 -*-
from ..qt import QtCore
from ..qt.QtWidgets import QCompleter

from .extension import Extension
from ..text import columnize, long_substr


class COMPLETE_MODE(object):
    DROPDOWN = 1
    INLINE = 2


class AutoComplete(Extension, QtCore.QObject):
    def __init__(self):
        Extension.__init__(self)
        QtCore.QObject.__init__(self)
        self.mode = COMPLETE_MODE.INLINE
        self.completer = None
        self._last_key = None

    def install(self):
        self.owner().key_pressed_signal.connect(self.key_pressed_handler)
        self.owner().post_key_pressed_signal.connect(self.post_key_pressed_handler)
        self.owner().set_complete_mode_signal.connect(self.mode_set_handler)
        self.init_completion_list([])

    def mode_set_handler(self, mode):
        self.mode = mode

    def key_pressed_handler(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Tab:
            self.handle_tab_key(event)
        elif key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Space):
            self.handle_complete_key(event)
        elif key == QtCore.Qt.Key_Escape:
            self.hide_completion_suggestions()

    def post_key_pressed_handler(self, event):
        key = event.key()

        # Regardless of key pressed update list, if we are completing a
        # word, highlight the first match !
        self.update_completion(key)
        self._last_key = key

    def handle_tab_key(self, event):
        if self.mode == COMPLETE_MODE.DROPDOWN:
            if self.owner()._get_buffer().strip():
                if self.completing():
                    self.complete()
                else:
                    self.trigger_complete()

                event.accept()

        elif self.mode == COMPLETE_MODE.INLINE:
            if self._last_key == QtCore.Qt.Key_Tab:
                self.trigger_complete()

            event.accept()

    def handle_complete_key(self, event):
        if self.completing():
            self.complete()
            event.accept()

    def init_completion_list(self, words):
        self.completer = QCompleter(words, self)
        self.completer.setCompletionPrefix(self.owner()._get_buffer())
        self.completer.setWidget(self.owner())

        if self.mode == COMPLETE_MODE.DROPDOWN:
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
            self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitive)
            self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)
            self.completer.activated.connect(self.insert_completion)
        else:
            self.completer.setCompletionMode(QCompleter.InlineCompletion)
            self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitive)
            self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)

    def trigger_complete(self):
        _buffer = self.owner()._get_buffer().strip()

        if self.mode == COMPLETE_MODE.DROPDOWN:
            if len(_buffer):
                self.show_completion_suggestions(_buffer)
            else:
                self.show_completion_suggestions(_buffer)
        else:
            self.show_completion_suggestions(_buffer)

    def show_completion_suggestions(self, _buffer):
        words = self.owner().get_completions(_buffer)

        # No words to show, just return
        if len(words) == 0:
            return

        # Close any popups before creating a new one
        if self.completer.popup():
            self.completer.popup().close()

        self.init_completion_list(words)

        leastcmn = long_substr(words)
        self.insert_completion(leastcmn)

        # If only one word to complete, just return and don't display options
        if len(words) == 1:
            return

        if self.mode == COMPLETE_MODE.DROPDOWN:
            cr = self.owner().cursorRect()
            sbar_w = self.completer.popup().verticalScrollBar()
            popup_width = self.completer.popup().sizeHintForColumn(0)
            popup_width += sbar_w.sizeHint().width()
            cr.setWidth(popup_width)
            self.completer.complete(cr)
        elif self.mode == COMPLETE_MODE.INLINE:
            cl = columnize(words, colsep = '  |  ')
            self.owner()._insert_prompt('\n\n' + cl + '\n', lf=True, keep_buffer = True)

    def hide_completion_suggestions(self):
        if self.completing():
            self.completer.popup().close()

    def completing(self):
        if self.mode == COMPLETE_MODE.DROPDOWN:
            return self.completer.popup() and self.completer.popup().isVisible()
        else:
            return False

    def insert_completion(self, completion):
        _buffer = self.owner()._get_buffer().strip()

        # Handling the . operator in object oriented languages so we don't
        # overwrite the . when we are inserting the completion. Its not the .
        # operator If the buffer starts with a . (dot), but something else
        # perhaps terminal specific so do nothing.
        if '.' in _buffer and _buffer[0] != '.':
            idx = _buffer.rfind('.') + 1
            _buffer = _buffer[idx:]

        if self.mode == COMPLETE_MODE.DROPDOWN:
            self.owner()._insert_in_buffer(completion[len(_buffer):])
        elif self.mode == COMPLETE_MODE.INLINE:
            self.owner()._clear_buffer()
            self.owner()._insert_in_buffer(completion)

            words = self.owner().get_completions(completion)

            if len(words) == 1:
                self.owner()._insert_in_buffer(' ')

    def update_completion(self, key):
        if self.completing():
            _buffer = self.owner()._get_buffer()

            if len(_buffer) > 1:
                self.show_completion_suggestions(_buffer)
                self.completer.setCurrentRow(0)
                model = self.completer.completionModel()
                self.completer.popup().setCurrentIndex(model.index(0,0))
            else:
                self.completer.popup().hide()

    def complete(self):
        if self.completing() and self.mode == COMPLETE_MODE.DROPDOWN:
            index = self.completer.popup().currentIndex()
            model = self.completer.completionModel()
            word = model.itemData(index)[0]
            self.insert_completion(word)
            self.completer.popup().hide()
