#!/usr/bin/env python

from qcontrol import QControlMainWindow as VCPMainWindow

import os
# file paths
VCP_DIR = os.path.dirname(os.path.abspath(__file__))

# QSS style sheet
QSS_FILE = os.path.join(VCP_DIR, 'ui/qcontrol.qss')

UI_FILE = os.path.join(VCP_DIR, 'ui/qcontrol.ui')

RC_FILE = os.path.join(VCP_DIR, 'recourses/qcontrol.qrc')

# the Qt theme to use, 'windows', 'fusion' ...
THEME = None


VERSION = '0.0.1'
AUTHOR = 'Kurt Jacobson'
SHORT_DESCRIPTION = "Example VCP for QtPyVCP"
LONG_DESCRIPTION = """This is a long description."""
