import sys, os
from PyQt5 import Qt, uic

class ErrorDialog(Qt.QDialog):
    def __init__(self, traceback=''):
        super(ErrorDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'error_dialog.ui'), self)
        self.tracebackText.setText(traceback)
        self.show()

    def setTraceback(self, traceback):
        self.tracebackText.setText(traceback)

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv)
    window = ErrorDialog()
    sys.exit(app.exec_())
