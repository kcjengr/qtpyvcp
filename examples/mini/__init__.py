#!/usr/bin/env python

"""Main entry point for MiniVCP.

This module contains the code required to run MiniVCP directly, without
having to pass it as an argument to qtpyvcp. It handles parsing command
line args and starting the main application.

Example:
    Assuming the dir this file is located in is on the PATH, you can
    launch MiniVCP by saying::

        $ mini --ini=/path/to/config.ini [options ...]

    Run with the --help option to print a full list of options.

"""

__version__ = '0.0.1'

import os
import qtpyvcp

VCP_DIR = os.path.realpath(os.path.dirname(__file__))
VCP_CONFIG_FILE = os.path.join(VCP_DIR, 'mini.yml')


def main(opts=None):

    if opts is None:
        from qtpyvcp.utilities.opt_parser import parse_opts
        opts = parse_opts(vcp_cmd='mini',
                          vcp_name='Mini',
                          vcp_version=__version__)

    # run the main application
    qtpyvcp.app.run(opts, VCP_CONFIG_FILE)


if __name__ == '__main__':
    main()
