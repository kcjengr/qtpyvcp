#!/usr/bin/env python

import os

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

# Setup logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger('QtPyVCP.' + __name__)

from QtPyVCP import actions

VCP_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FILE = os.path.join(VCP_DIR, 'ui/brender.ui')
STYLESHEET = os.path.join(VCP_DIR, 'resources/brender.qss')

class MainWindow(VCPMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.loadUi(UI_FILE)
        self.initUi()
        self.loadStylesheet(STYLESHEET)

        self.setWindowTitle("Brender VCP")

    #==========================================================================
    #  Add/Override methods and slots below to customize the main window
    #==========================================================================

        actions.bindWidget(self.flood, action='coolant.flood.toggle')
        actions.bindWidget(self.floodCheckBox, action="coolant.flood.toggle")

        if actions.program.run.ok():
            actions.program.run()
        else:
            print "RUN NOT OK: ", actions.program.run.ok.msg

    # This slot will be automatically connected to a menu item named 'Test'
    # created in QtDesigner.
    @pyqtSlot()
    def on_actionTest_triggered(self):
        print 'Test action triggered'
        # implement the action here
