import os
from traceback import format_exception

from qtpy import uic
from qtpy.QtWidgets import QDialog

class ErrorDialog(QDialog):
    def __init__(self, exc_info):
        super(ErrorDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'error_dialog.ui'), self)

        exc_type, exc_msg, exc_tb = exc_info

        self.errorType.setText(exc_type.__name__ + ':')
        self.errorValue.setText(str(exc_msg))
        self.setWindowTitle(exc_type.__name__)
        self.tracebackText.setText("".join(format_exception(*exc_info)))
        self.show()

    def setTraceback(self, text):
        self.tracebackText.setText(text)
