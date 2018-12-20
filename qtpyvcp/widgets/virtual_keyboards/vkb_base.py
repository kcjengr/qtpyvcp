
from qtpy import uic
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

class VKBBase(QDialog):
    def __init__(self, parent=None, ui_file=None):
        super(VKBBase, self).__init__(parent)

        if ui_file is not None:
            uic.loadUi(ui_file, self)

        self.setWindowFlags(Qt.WindowDoesNotAcceptFocus | Qt.Tool |
                            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # self.show()

