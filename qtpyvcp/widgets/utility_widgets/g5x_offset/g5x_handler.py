import os

from qtpy import uic
from qtpy.QtWidgets import QWidget
from functools import partial

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class G5xOffsetHandler(QWidget):

    def __init__(self, parent=None):
        super(G5xOffsetHandler, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "g5x_keypad.ui"), self)

    def setup_g5x(self):
        self.ui.g5xBtnGrp.buttonClicked.connect(partial(self.g5xKeypad, self.ui))
        self.ui.g5xBkspBtn.clicked.connect(partial(self.g5xBackSpace, self.ui))

    @staticmethod
    def g5x_keypad(parent, button):
        char = str(button.text())
        text = parent.g5xOffsetLbl.text() or 'null'
        if text != 'null':
            text += char
        else:
            text = char
        parent.g5xOffsetLbl.setText(text)

    @staticmethod
    def g5x_backspace(parent):
        if len(parent.g5xOffsetLbl.text()) > 0:
            text = parent.g5xOffsetLbl.text()[:-1]
            parent.g5xOffsetLbl.setText(text)
