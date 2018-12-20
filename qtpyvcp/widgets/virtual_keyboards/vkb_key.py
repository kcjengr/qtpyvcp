
from qtpy.QtGui import QKeySequence, QKeyEvent
from qtpy.QtCore import Qt, Signal, Slot, Property, QEvent
from qtpy.QtWidgets import QPushButton, QApplication

from qtpyvcp.widgets.virtual_keyboards import getKeyboard

class VKBKey(QPushButton):
    def __init__(self, parent=None):
        super(VKBKey, self).__init__(parent)

        self.app = QApplication.instance()
        # self.setFocusPolicy(Qt.NoFocus)

        self.engine = getKeyboard('engine')

        self._key = 123

        self.pressed.connect(self.onPressEvent)
        self.released.connect(self.onReleaseEvent)

    def onPressEvent(self):
        print "pressed"
        self.engine.emulateEvent(self._key)

    def onReleaseEvent(self):
        print "released"
        self.engine.emulateEvent(self._key)

    # @Property(QKeySequence)
    # def key(self):
    #     print self._key
    #     return self._key
    #
    # @key.setter
    # def key(self, key):
    #     print self._key
    #     self._key = key
    #     # print QKeySequence.fromString(self._key)