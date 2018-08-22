#!/usr/bin/env python

import sys
import argparse
import QtPyVCP
from QtPyVCP.utilities import logger

def main():
    parser = argparse.ArgumentParser(description="LinuxCNC Virtual Control Panel")
    parser.add_argument(
        '-ini',
        help='Full path the the LinuxCNC INI file.' +
             '    This is required if a LinuxCNC instance is not already running',
        nargs='?',
        default=None
        )
    parser.add_argument(
        'vcp',
        help='A VCP to display.' +
             '    Can be either a Qt .ui file, a Python file, or a VCP package.',
        nargs='?',
        default=None
        )
    parser.add_argument(
        '--chooser',
        action='store_true',
        help='Show the VCP chooser,' +
             ' allows selecting from a list of available VCP packages and files.'
        )
    parser.add_argument(
        '--perfmon',
        action='store_true',
        help='Enable performance monitoring,' +
             ' and print CPU usage to the terminal.'
        )
    parser.add_argument(
        '--hide-nav-bar',
        action='store_true',
        help='Start with the navigation bar hidden.'
        )
    parser.add_argument(
        '--hide-menu-bar',
        action='store_true',
        help='Start with the menu bar hidden.'
        )
    parser.add_argument(
        '--hide-status-bar',
        action='store_true',
        help='Start with the status bar hidden.'
        )
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Start in full screen mode.'
        )
    parser.add_argument(
        '--position',
        help='Start position of the main window, given as 100x50,' +
             ' where 100 and 50 are the desired x and y coordinates from the' +
             ' top left corner of the screen.'
        )
    parser.add_argument(
        '--size',
        help='Start size of the main window, given as 900x750,' +
             ' were 900 and 750 are the width and height of the window.'
        )
    parser.add_argument(
        '--log-level',
        help='Configure level of terminal and log messages',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
        )
    parser.add_argument('--version', action='version',
                    version='QtPyVCP: v{version}'.format(version=QtPyVCP.__version__)
        )
    parser.add_argument(
        '--stylesheet',
        help='Full path to a QSS stylesheet, with styles to be' +
             ' applied to specific Qt/VCP widget classes.',
        default=None
        )
    parser.add_argument(
        'display_args',
        help='Arguments to be passed to the VCP application' +
             ' (which is a QApplication subclass).',
        nargs=argparse.REMAINDER,
        default=None
        )

    args = parser.parse_args()

    if args.chooser:
        from vcp_chooser import VCPChooser
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        result = VCPChooser(args).exec_()
        if result == VCPChooser.Rejected:
            sys.exit()
        del(app)

    log_level = getattr(logger, args.log_level.upper())
    LOG = logger.initBaseLogger('QtPyVCP', log_file=None, log_level=log_level)


    app = QtPyVCP.VCPApplication(
        vcp=args.vcp,
        ini=args.ini,
        command_line_args=args.display_args,
        perfmon=args.perfmon,
        hide_nav_bar=args.hide_nav_bar,
        hide_menu_bar=args.hide_menu_bar,
        hide_status_bar=args.hide_status_bar,
        fullscreen=args.fullscreen,
        stylesheet_path=args.stylesheet
        )

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
