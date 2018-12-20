
from qtpy.QtGui import QKeySequence, QKeyEvent
from qtpy.QtCore import Qt, QObject, Signal, Slot, QEvent
from qtpy.QtWidgets import QApplication, QLineEdit

from qtpyvcp.widgets.virtual_keyboards import getKeyboard

class VKBEngine(QObject):

    modifierChanged = Signal(int)

    def __init__(self, parent=None):
        super(VKBEngine, self).__init__(parent)

        self.app = QApplication.instance()

        self._modifiers = Qt.NoModifier | Qt.ShiftModifier

        self.app.focusChanged.connect(self.focusChangedEvent)

    def focusChangedEvent(self, old_w, new_w):
        if issubclass(new_w.__class__, QLineEdit):
            print "QLineEdit got focus: ", new_w
            getKeyboard('default').show()
        else:
            getKeyboard('default').hide()


    def emulateEvent(self, key, modifiers=None):
        print key
        print Qt.NoModifier
        print QKeySequence(key).toString()
        receiver = self.app.focusObject()
        press_event = QKeyEvent(QEvent.KeyPress, key, self._modifiers, QKeySequence(key).toString())
        release_event = QKeyEvent(QEvent.KeyRelease, key, self._modifiers)
        self.app.sendEvent(receiver, press_event)
        self.app.sendEvent(receiver, release_event)