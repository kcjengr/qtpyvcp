
from qtpy.QtGui import QKeySequence, QKeyEvent
from qtpy.QtCore import Qt, Signal, Slot, Property, QEvent
from qtpy.QtWidgets import QPushButton, QApplication

from qtpyvcp.widgets.virtual_keyboards import getKeyboard

class VKBKey(QPushButton):
    def __init__(self, parent=None):
        super(VKBKey, self).__init__(parent)

        self._text = ''
        self._key = QKeySequence()

        self.engine = getKeyboard('engine')

        self.pressed.connect(self.onPressEvent)
        self.released.connect(self.onReleaseEvent)

        self.engine.shiftStateChanged.connect(self.onShiftStateChanged)

    def onPressEvent(self):
        print "pressed"
        self.engine.emulateKeyPress(self._key)

    def onReleaseEvent(self):
        print "released"
        self.engine.emulateKeyRelease(self._key)

    def onShiftStateChanged(self, shift):
        if shift:
            self.setText(self.text().lower())
        else:
            self.setText(self.text().upper())


    # @Property(str)
    # def text(self):
    #     print self._text
    #     return self._text
    #
    # @text.setter
    # def text(self, text):
    #     print self._text
    #     self._text = text


    @Property(QKeySequence)
    def key(self):
        print self._key
        return self._key

    @key.setter
    def key(self, key):
        print self._key
        self._key = key
    #     # print QKeySequence.fromString(self._key)