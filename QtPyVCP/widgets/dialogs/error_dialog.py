import sys, os
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog

class ErrorDialog(QDialog):
    def __init__(self, traceback=''):
        super(ErrorDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'error_dialog.ui'), self)
        self.tracebackText.setText(traceback)
        self.show()

    def setTraceback(self, text):
        self.tracebackText.setText(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ErrorDialog()
    sys.exit(app.exec_())
