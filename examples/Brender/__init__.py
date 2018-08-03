#!/usr/bin/env python

VERSION = '0.0.1'
AUTHOR = 'Kurt Jacobson'
SHORT_DESCRIPTION = "Brender style VCP"
LONG_DESCRIPTION = """"""

REPO_URL = ''
DOC_URL = ''

from brender import MainWindow as VCPMainWindow

import os
# file paths
VCP_DIR = os.path.dirname(os.path.abspath(__file__))

UI_FILE = os.path.join(VCP_DIR, 'ui/brender.ui')

# resources files
QSS_FILE = os.path.join(VCP_DIR, 'resources/brender.qss')
RC_FILE = os.path.join(VCP_DIR, 'resources/xyz.qrc')

# Qt theme to use
THEME = None
#THEME = 'windows'
#THEME = 'fusion'
