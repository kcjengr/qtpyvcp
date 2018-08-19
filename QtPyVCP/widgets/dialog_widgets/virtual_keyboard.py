import sys, os
from PyQt5 import uic
from PyQt5.QtWidgets import QPushButton, QDialog, qApp
from PyQt5.QtCore import Qt

UI_DIR = os.path.realpath(os.path.dirname(__file__))

class IntKeypad(QDialog):
    def __init__(self, parent=None):
        super(IntKeypad, self).__init__(parent)
        uic.loadUi(os.path.join(UI_DIR, 'ui/int_keypad.ui'), self)

        self.setWindowFlags(Qt.WindowDoesNotAcceptFocus | Qt.Tool |
                   Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint);

        self.entry = None

        self.setWindowTitle("Int Keypad")

        for btn in self.findChildren(QPushButton):
            print btn.text()
            btn.clicked.connect(self.onButtonClicked)

    def onButtonClicked(self):
        char = self.sender().text()
        self.entry.setText(char)

    def popup(self, entry):
        self.entry = entry
        window = qApp.activeWindow()
        self.show()

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = IntKeypad()
    w.show()
    sys.exit(app.exec_())
