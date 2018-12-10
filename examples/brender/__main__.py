#!/usr/bin/env python

"""Main entry point for Brender VCP.

This module contains the code necessary to be able to launch MiniVCP
directly from the command line, without using qtpyvcp. It handles
parsing command line args and starting the main application.

Example:
    Assuming the dir this file is located in is on the PATH, you can
    launch MiniVCP by saying::

        $ brender --ini=/path/to/config.ini [options ...]

    Run with the --help option to print a full list of options.

"""

from . import __version__, run

# parse cmd line args
from qtpyvcp.utilities.opt_parser import parse_opts
opts = parse_opts(vcp_name='Mini', vcp_cmd='mini', vcp_version=__version__)

# run
run(opts)
