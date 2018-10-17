#!/usr/bin/env python

import sys
from qtpyvcp.utilities.opt_parser import parse_opts

__version__ = '0.0.1'

# parse cmd line args and set up environment
opts = parse_opts(vcp_name='Brender', vcp_cmd='brender', vcp_version=__version__)

from brender import MainWindow
from qtpyvcp.application import VCPApplication

# initialize the app
app = VCPApplication(opts=opts)

# set up the window
app.window = MainWindow(opts=opts)
app.window.show()

sys.exit(app.exec_())
