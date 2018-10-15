#!/usr/bin/env python

"""Main entry point for MiniVCP.

This module contains the code necessary to be able to launch MiniVCP
directly from the command line, without using qtpyvcp. It handles
parsing command line args and starting the main application.

Example:
    Assuming the dir this file is located in is on the PATH, you can
    launch MiniVCP by saying::

        $ mini --ini=/path/to/config.ini [options ...]

    Run with the --help option to print a full list of options.

"""

import os
import sys

from qtpyvcp.utilities.opt_parser import parse_opts

# import version number from __init__.py
from . import __version__

# parse cmd line args and set up environment
opts = parse_opts(vcp_name='Mini', vcp_cmd='mini', vcp_version=__version__)

# import window and app AFTER the environment has been set
from mini import MiniVCP
from qtpyvcp.application import VCPApplication

# initialize the app
app = VCPApplication(opts=opts)

# set up the window
app.window = MiniVCP(opts=opts)
app.window.show()

# execute the application
sys.exit(app.exec_())
