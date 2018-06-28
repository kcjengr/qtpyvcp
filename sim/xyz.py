#!/usr/bin/env python

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

# Setup logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger('QtPyVCP.' + __name__)

LOG.error('Hurray!!! ')

class MainWindow(VCPMainWindow):
    def __init__(self, ui_file):
        super(MainWindow, self).__init__()
        uic.loadUi(ui_file, self)

        self.initUi()

        self.show()

        print 'Log Path: ',self.log_file_path

    @pyqtSlot()
    def on_actionTest_triggered(self):
        print 'Action test'
        self.close


# class Actions(Actions):
#     super(Actions, self).__init__()
