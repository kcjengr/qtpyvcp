import os

from qtpy import uic
from qtpy.QtWidgets import QWidget
from functools import partial

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class G92OffsetHandler(QWidget):

    def __init__(self, parent=None):
        super(G92OffsetHandler, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "g92_keypad.ui"), self)

    def setup_g5x(self):
        self.ui.g92Btns.buttonClicked.connect(partial(self.g92_keypad, self.ui))
        self.ui.g92BkspBtn.clicked.connect(partial(self.g92_backspace, self.ui))

    @staticmethod
    def g92_keypad(parent, button):
        char = str(button.text())
        text = parent.g92OffsetsLbl.text() or 'null'
        if text != 'null':
            text += char
        else:
            text = char
        parent.g92OffsetsLbl.setText(text)

    @staticmethod
    def g92_backspace(parent):
        if len(parent.g92OffsetsLbl.text()) > 0:
            text = parent.g92OffsetsLbl.text()[:-1]
            parent.g92OffsetsLbl.setText(text)





