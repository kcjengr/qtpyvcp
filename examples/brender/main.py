#!/usr/bin/env python

__version__ = '0.0.1'

import sys
from QtPyVCP.utilities.opt_parser import parse_opts

def main():
    opts = parse_opts(vcp_name='Brender', vcp_cmd='brender', vcp_version=__version__)
    from brender import MainWindow
    from QtPyVCP.application import VCPApplication
    app = VCPApplication(opts=opts)
    app.window = MainWindow(opts=opts)
    app.window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
