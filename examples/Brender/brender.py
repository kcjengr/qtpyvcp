#!/usr/bin/env python

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

# Setup logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger('QtPyVCP.' + __name__)

# from QtPyVCP.core import Status, Action, Prefs, Info
# STATUS = Status()
# ACTION = Action()
# PREFS = Prefs()
# INFO = Info()

from QtPyVCP.utilities import action
from QtPyVCP.actions import program_actions, bindWidget

class MainWindow(VCPMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

    #==========================================================================
    #  Add/Override methods and slots below to customize the main window
    #==========================================================================

        bindWidget(self.flood, action='coolant.flood.toggle')
        bindWidget(self.floodCheckBox, action="coolant.flood.toggle")

        if program_actions.runOk():
            program_actions.run()
        else:
            print "RUN NOT OK: ", program_actions.runOk.msg

    # This slot will be automatically connected to a menu item named 'Test'
    # created in QtDesigner.
    @pyqtSlot()
    def on_actionTest_triggered(self):
        print 'Test action triggered'
        # implement the action here
