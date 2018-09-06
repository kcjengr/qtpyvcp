#!/usr/bin/env python

import os
import sys
from PyQt5.QtWidgets import QStyleFactory

import QtPyVCP
from QtPyVCP.utilities.opt_parser import parse_opts

def main():
    # parser = VCPArgParser(description="LinuxCNC Virtual Control Panel")
    opts = parse_opts()

    ini_file = os.environ.get('INI_FILE_NAME') or opts.ini
    if ini_file is None:
        # Check if LinuxCNC is running
        if os.path.isfile('/tmp/linuxcnc.lock'):
            # LinuxCNC is running, but in a different environment.
            # TODO: find some way to get the INI file LCNC was launched with
            print 'LinuxCNC is running, no INI file specifed on command line'
            sys.exit()
        else:
            # LinuxCNC is not running
            # TODO: Maybe launch LinuxCNC using subprocess
            print 'LinuxCNC is not running, no INI file specified on command line'
            sys.exit()

    if not os.getenv('INI_FILE_NAME'):
        from QtPyVCP.utilities.misc import normalizePath
        base_path = os.path.expanduser('~/linuxcnc/configs')
        ini_file = os.path.realpath(normalizePath(ini_file, base_path))
        if not os.path.exists(ini_file):
            print 'Specifed INI file does not exist: {}'.format(ini_file)
            sys.exit()
        os.environ['INI_FILE_NAME'] = ini_file
        os.environ['CONFIG_DIR'] = os.path.dirname(ini_file)

    if opts.chooser:
        from vcp_chooser import VCPChooser
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        result = VCPChooser(opts).exec_()
        if result == VCPChooser.Rejected:
            sys.exit()
        del(app)

    from QtPyVCP.utilities import logger
    try:
        log_level = getattr(logger, opts.log_level.upper())
    except:
        log_level = 'DEBUG'
    LOG = logger.initBaseLogger('QtPyVCP', log_file=opts.log_file, log_level=log_level)
    print LOG

    from QtPyVCP.application import VCPApplication
    app = VCPApplication(opts=opts)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
