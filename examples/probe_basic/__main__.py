#!/usr/bin/env python

"""Main entry point for ProbeBasic.

This module contains the code necessary to be able to launch ProbeBasic
directly from the command line, without using QtPyVCP. It handles
parsing command line args and starting the main application.

Example:
    Assuming the dir this file is located in is on the PATH, you can
    launch ProbeBasic by saying::

        $ probebasic --ini=/path/to/config.ini [options ...]

    Run with --help to print a full list of options.

"""

import os
import sys

from QtPyVCP.utilities.opt_parser import parse_opts

# import version number from __init__.py
from . import __version__

# parse cmd line args and set up environment
opts = parse_opts(vcp_name='ProbeBasic', vcp_cmd='probebasic', vcp_version=__version__)

# import window and app AFTER the environment has been set
from probe_basic import ProbeBasic
from QtPyVCP.application import VCPApplication

# initialize the app
app = VCPApplication(opts=opts)

# set up the window
app.window = ProbeBasic(opts=opts)
app.window.show()

# execute the application
sys.exit(app.exec_())
