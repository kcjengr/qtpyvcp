import os

from qtpy import uic
from qtpy.QtWidgets import QWidget


WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class G5xOffsetHandler(QWidget):

    def __init__(self, parent=None):
        super(G5xOffsetHandler, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "g5x_keypad.ui"), self)

        self.ui.keypad.buttonClicked.connect(self.g5x_keypad)
        self.ui.g5xBkspBtn.clicked.connect(self.g5x_backspace)

    def g5x_keypad(self, widget):
        char = str(widget.text())
        text = self.ui.g5xOffsetLbl.text() or None
        if text:
            text += char
        else:
            text = char
        self.ui.g5xOffsetLbl.setText(text)

    def g5x_backspace(self, widget):
        if len(self.ui.g5xOffsetLbl.text()) > 0:
            text = self.ui.g5xOffsetLbl.text()[:-1]
            self.ui.g5xOffsetLbl.setText(text)
