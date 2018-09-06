#!/usr/bin/env python

"""
Brender - A QtPyVCP based Virtual Control Panel for LinuxCNC.

Usage:
  brender --ini=INI [--log-level=LEVEL] [--log-file=FILE] [--perfmon]
            [--theme=THEME] [--stylesheet=SYTLESHEET]
            [--size WIDTHxHEIGHT] [--position XPOSxYPOS]
            [--fullscreen] [--maximize] [--hide-menu-bar] [--hide-status-bar]
  brender (-h | --help)
  brender (-v | --version)

Required Arguments:
    --ini=INI        Path to INI file, relative to ~/linuxcnc/configs

Display  Options:
  --theme THEME      The Qt theme to use, defaults to system theme.
  --stylesheet STYLESHEET
                     Path to QSS file containing styles to be applied
                     to specific Qt and/or QtPyVCP widget classes.
  -f --fullscreen    Flag to start with window fullscreen.
  -m --maximize      Flag to start with window maximized.
  --size WIDTHxHEIGHT
                     Initial size of the window in pixels.
  --position XPOSxYPOS
                     Initial position of the window, specified as the coordinates
                     of the top left corner of the window relative to the top left
                     corner of the screen.
  --hide-menu-bar    Hides the menu bar.
  --hide-status-bar  Hides the status bar.

Application Options:
  --log-level=(DEBUG | INFO | WARN | ERROR | CRITICAL)
                     Sets the log level. [default: INFO]
  --log-file=FILE    Specifies the log file. Overrides setting in INI.
  --perfmon          Monitor and log system performance.

General Options:
  -h --help          Show this help and exit.
  -v --version       Show version.

Note:
  If you have specified [DISPLAY]DISPLAY = qcontrol in the INI file the --ini
  parameter will automatically be passed by the linuxcnc startup script.

"""

__version__ = '0.0.1'

import os

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

# Setup logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger('QtPyVCP.' + __name__)

from QtPyVCP.core import Status, Action, Prefs, Info
STATUS = Status()
ACTION = Action()
PREFS = Prefs()
INFO = Info()

VCP_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FILE = os.path.join(VCP_DIR, 'ui/brender.ui')
STYLESHEET = os.path.join(VCP_DIR, 'resources/brender.qss')

class MainWindow(VCPMainWindow):
    def __init__(self, opts):
        super(MainWindow, self).__init__(opts)

        self.loadUi(UI_FILE)
        self.loadStylesheet(STYLESHEET)

    #==========================================================================
    #  Add/Override methods and slots below to customize the main window
    #==========================================================================

    # This slot will be automatically connected to a menu item named 'Test'
    # created in QtDesigner.
    @pyqtSlot()
    def on_actionTest_triggered(self):
        print 'Test action triggered'
        # implement the action here

# Main entry point
def main():
    import sys
    from QtPyVCP.utilities.opt_parser import parse_opts
    opts = parse_opts(__doc__, vcp_name='Brender', vcp_version=__version__)
    from QtPyVCP.application import VCPApplication
    app = VCPApplication(opts)
    app.window = MainWindow(opts)
    app.window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
