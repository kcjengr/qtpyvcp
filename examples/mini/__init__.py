#!/usr/bin/env python

import os

# general information about the VCP
VERSION = '0.0.1'
AUTHORS = ['Kurt Jacobson',]
SHORT_DESCRIPTION = "Minimal VCP"
LONG_DESCRIPTION = """Absolute minimal VCP"""

# specify the object to use as the main VCP window
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

# the location of this VCP package, used as the base for other files
vcp_dir = os.path.dirname(os.path.abspath(__file__))

# path to the main QtDesigner UI file for the VCP
UI_FILE = os.path.join(vcp_dir, 'mini.ui')

# path to the default QSS style sheet to use
QSS_FILE = None

# path to the Qt recourse file
QRC_FILE = None

# the Qt theme to use, 'windows', 'fusion' ...
THEME = None
