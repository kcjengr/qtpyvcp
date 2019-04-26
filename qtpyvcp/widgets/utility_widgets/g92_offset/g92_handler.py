import os

from qtpy import uic
from qtpy.QtWidgets import QWidget


WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class G92OffsetHandler(QWidget):

    def __init__(self, parent=None):
        super(G92OffsetHandler, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "g92_keypad.ui"), self)

        self.ui.keypad.buttonClicked.connect(self.g92_keypad)
        self.ui.g92BkspBtn.clicked.connect(self.g92_backspace)

    def g92_keypad(self, widget):
        char = str(widget.text())
        text = self.ui.g92OffsetsLbl.text() or 'null'
        if text != 'null':
            text += char
        else:
            text = char
        self.ui.g92OffsetsLbl.setText(text)

    def g92_backspace(self, widget):
        if len(self.ui.g92OffsetsLbl.text()) > 0:
            text = self.ui.g92OffsetsLbl.text()[:-1]
            self.ui.g92OffsetsLbl.setText(text)





