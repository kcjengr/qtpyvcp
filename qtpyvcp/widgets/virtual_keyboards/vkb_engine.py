
from qtpy.QtGui import QKeySequence, QKeyEvent
from qtpy.QtCore import Qt, QObject, Signal, Slot, QEvent
from qtpy.QtWidgets import QApplication, QLineEdit, QSpinBox, QDoubleSpinBox

from qtpyvcp.widgets.virtual_keyboards import getKeyboard
from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry
from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit


class VKBEngine(QObject):

    SHIFT_MAP = {'`': '~', '1': '!', '2': '@', '3': '#', '4': '$',
                       '5': '%', '6': '^', '7': '&', '8': '*', '9': '(',
                       '0': ')', '-': '_', '=': '+', '[': '{', ']': '}',
                       '\\': '|', ';': ':', "'": '"', ',': '<', '.': '>',
                       '/': '?'}

    modifierChanged = Signal(int)
    shiftStateChanged = Signal(bool)

    def __init__(self, parent=None, enabled=True):
        super(VKBEngine, self).__init__(parent)

        self.app = QApplication.instance()
        self._enabled = enabled
        self._modifiers = Qt.NoModifier
        self._active_vkb = None
        self._receiver = None

        if self._enabled:
            self.app.focusChanged.connect(self.focusChangedEvent)


    def focusChangedEvent(self, old_w, new_w):

        if isinstance(new_w, QLineEdit):
            print("QLineEdit got focus: ", new_w)
            input_type = new_w.property('inputType') or 'default'
            self.activateVKB(new_w, input_type)

        elif isinstance(new_w, QSpinBox):
            print("QSpinBox got focus: ", new_w)
            input_type = new_w.property('inputType') or 'int'
            self.activateVKB(new_w.lineEdit(), input_type)

        elif isinstance(new_w, QDoubleSpinBox):
            print("QDoubleSpinBox got focus: ", new_w)
            input_type = new_w.property('inputType') or 'float'
            self.activateVKB(new_w.lineEdit(), input_type)

        else:
            if self._active_vkb:
                self._active_vkb.hide()

            self._active_vkb = None
            self._receiver = None

    def activateVKB(self, line_edit, input_type):

        if self._active_vkb:
            self._active_vkb.hide()

        self._receiver = line_edit

        self._active_vkb = getKeyboard(input_type)
        self._active_vkb.show()


    def emulateKeyPress(self, key_seq=None, modifiers=None):
        widget = self.sender()

        text = ''
        if key_seq is None or key_seq.count() == 0:
            text = widget.text()

            if text == '':
                return

            key_seq = QKeySequence(text)

        receiver = self.app.focusObject()
        press_event = QKeyEvent(QEvent.KeyPress, key_seq[0], self._modifiers, text)
        self.app.sendEvent(receiver, press_event)

        # self.shiftStateChanged.emit(True)

    def emulateKeyRelease(self, key_seq, modifiers=None):

        if key_seq.count() == 0:
            return

        receiver = self.app.focusObject()
        release_event = QKeyEvent(QEvent.KeyRelease, key_seq[0], self._modifiers)
        self.app.sendEvent(receiver, release_event)


    def setShifted(self, shifted):
        self._shifted = shifted
        self.shiftStateChanged.emit(shifted)


    def toKeyCode(self, seq):

        if isinstance(seq, basestring):
            seq = QKeySequence(seq)


        # We should only working with a single key here
        if seq.count() == 1:
            key_code = seq[0]

        else:
            # Should be here only if a modifier key (e.g. Ctrl, Alt) is pressed.
            assert(seq.count() == 0)

            # Add a non-modifier key "A" to the picture because QKeySequence
            # seems to need that to acknowledge the modifier. We know that A has
            # a keyCode of 65 (or 0x41 in hex)
            seq = QKeySequence(seq.toString() + "+A")
            assert(seq.count() == 1)
            assert(seq[0] > 65)
            key_code = seq[0] - 65

        return key_code
