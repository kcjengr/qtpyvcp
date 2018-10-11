#!/usr/bin/env python

import os
import time

from PyQt5.QtWidgets import QApplication

from QtPyVCP.utilities import logger
from QtPyVCP.core import Status, Action, Prefs, Info
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

# try:
#     import probe_basic_ui
# except ImportError:
#     from QtPyVCP.tools.qcompile import compile
#     compile(packages=[os.path.dirname(__file__),])
#     import probe_basic_ui

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

        s = time.time()

        app = QApplication.instance()

        # probe_basic_ui.Ui_Form().setupUi(self)
        self.loadUi(UI_FILE)

        self.initUi()

        app.loadStylesheet(QSS_FILE)
        self.setWindowTitle("ProbeBasic")

        LOG.debug('UI load time: {}s'.format(time.time() - s))
