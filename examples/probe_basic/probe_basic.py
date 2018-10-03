#!/usr/bin/env python

import os
import time

from PyQt5.QtWidgets import QApplication

from QtPyVCP.utilities import logger
from QtPyVCP.core import Status, Action, Prefs, Info
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

# import probe_basic_ui
import probe_basic_rc

LOG = logger.getLogger('QtPyVCP.' + __name__)
STATUS = Status()
ACTION = Action()
PREFS = Prefs()
INFO = Info()

VCP_DIR = os.path.abspath(os.path.dirname(__file__))
UI_FILE = os.path.join(VCP_DIR, 'probe_basic.ui')
QSS_FILE = os.path.join(VCP_DIR, 'probe_basic.qss')

class ProbeBasic(VCPMainWindow):
    """Main window class for the ProbeBasic VCP."""
    def __init__(self, *args, **kwargs):
        super(ProbeBasic, self).__init__(*args, **kwargs)

        app = QApplication.instance()

        self.setWindowTitle("ProbeBasic")

        s = time.time()
        try:
            import xyz_ui
            print time.time() - s
            xyz_ui.Ui_Form().setupUi(self)
        except ImportError:
            self.loadUi(UI_FILE)
            print 'Loaded form'

        print time.time() - s

        self.initUi()

        app.loadStylesheet(QSS_FILE)
