
from qtpy.QtGui import QKeySequence, QKeyEvent
from qtpy.QtCore import Qt, Signal, Slot, Property, QEvent
from qtpy.QtWidgets import QPushButton, QApplication

from qtpyvcp.widgets.virtual_keyboards import getKeyboard

class VBKModifierKey(QPushButton):
    def __init__(self, parent=None):
        super(VBKModifierKey, self).__init__(parent)

        # self.setFocusPolicy(Qt.NoFocus)

        self.engine = getKeyboard('engine')

        # self.pressed.connect(self.onPressEvent)
        # self.released.connect(self.onReleaseEvent)

        self.toggled.connect(self.onToggled)
        # self.engine.shiftStateChanged.connect(self.onShiftStateChanged)

    def onToggled(self, state):
        print 'shift toggled'
        self.engine.setShifted(state)

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
