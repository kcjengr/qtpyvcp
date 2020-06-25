#!/usr/bin/env python

"""Main entry point for Actions examples VCP."""

__version__ = '0.0.1'

import os
import qtpyvcp

VCP_DIR = os.path.realpath(os.path.dirname(__file__))
VCP_CONFIG_FILE = os.path.join(VCP_DIR, 'config.yml')


def main(opts=None):

    if opts is None:
        from qtpyvcp.utilities.opt_parser import parse_opts
        opts = parse_opts(vcp_cmd='actions',
                          vcp_name='Actions Example VCP',
                          vcp_version=__version__)

    # run the main application
    qtpyvcp.app.run(opts, VCP_CONFIG_FILE)


if __name__ == '__main__':
    main()
