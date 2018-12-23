
from qtpy.QtGui import QKeySequence, QKeyEvent
from qtpy.QtCore import Qt, QObject, Signal, Slot, QEvent
from qtpy.QtWidgets import QApplication, QLineEdit

from qtpyvcp.widgets.virtual_keyboards import getKeyboard

class VKBEngine(QObject):

    modifierChanged = Signal(int)

    def __init__(self, parent=None):
        super(VKBEngine, self).__init__(parent)

        self.app = QApplication.instance()

        self._modifiers = Qt.ControlModifier

        self.app.focusChanged.connect(self.focusChangedEvent)

    def focusChangedEvent(self, old_w, new_w):
        if issubclass(new_w.__class__, QLineEdit):
            print "QLineEdit got focus: ", new_w
            getKeyboard('default').show()
        else:
            getKeyboard('default').hide()


    def emulateKeyPress(self, key_seq, modifiers=None):
        widget = self.sender()

        if key_seq.count() == 0:
            return

        print self.toKeyCode(key_seq)
        print key_seq.toString()
        receiver = self.app.focusObject()
        press_event = QKeyEvent(QEvent.KeyPress, key_seq[0], self._modifiers, widget.text()) #QKeySequence(key).toString())
        self.app.sendEvent(receiver, press_event)

    def emulateKeyRelease(self, key_seq, modifiers=None):

        if key_seq.count() == 0:
            return

        print self.toKeyCode(key_seq)
        print QKeySequence(key_seq).toString()
        receiver = self.app.focusObject()
        release_event = QKeyEvent(QEvent.KeyRelease, key_seq[0], self._modifiers)
        self.app.sendEvent(receiver, release_event)


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
