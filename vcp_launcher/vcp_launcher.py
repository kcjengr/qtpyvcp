#!/usr/bin/env python

import os
import sys
import argparse
import QtPyVCP
from QtPyVCP.utilities import logger
from PyQt5.QtWidgets import QStyleFactory

def main():
    parser = argparse.ArgumentParser(description="LinuxCNC Virtual Control Panel")
    parser.add_argument(
        '-ini',
        help='Full path the the LinuxCNC INI file. ' +
             'This is required if a LinuxCNC instance is not already running',
        nargs='?',
        default=None,
        required=True
        )
    parser.add_argument(
        'vcp',
        help='The name of the VCP to display. ' +
             'Valid values are the full path to a Qt .ui file, a Python .py file, ' +
             'or the directory containing a VCP package.',
        nargs='?',
        default=None
        )
    parser.add_argument(
        '--chooser',
        action='store_true',
        help='Show the VCP chooser, ' +
             'allows selecting from a list of available VCP packages and files.'
        )
    parser.add_argument(
        '--perfmon',
        action='store_true',
        help='Enable performance monitoring, ' +
             'and print CPU usage to the terminal.'
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
        '--maximize',
        action='store_true',
        help='Start with main window maximized.'
        )
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Start with main window full screen.'
        )
    parser.add_argument(
        '--position',
        help='Start position of the main window, given as XPOSxYPOS,' +
             ' where XPOS and YPOS are the desired x and y coordinates from the' +
             ' top left corner of the screen in pixles.'
        )
    parser.add_argument(
        '--size',
        help='Start size of the main window, given as WIDTHxHEIGHT,' +
             ' were WIDTH and HEIGHT are the width and height of the window in pixles.'
        )
    parser.add_argument(
        '--log-level',
        help='Configure level of terminal and log messages',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
        )
    parser.add_argument(
        '--log-file',
        help='Specify the log file, overrides [DISPLAY]LOG_FILE in the INI',
        default=None
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
        '--theme',
        help='Qt theme to use, defaults to the system theme.',
        choices=QStyleFactory.keys(),
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

    ini_file = os.environ.get('INI_FILE_NAME') or args.ini
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

    if args.chooser:
        from vcp_chooser import VCPChooser
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        result = VCPChooser(args).exec_()
        if result == VCPChooser.Rejected:
            sys.exit()
        del(app)

    log_level = getattr(logger, args.log_level.upper())
    LOG = logger.initBaseLogger('QtPyVCP', log_file=args.log_file, log_level=log_level)
    print LOG

    app = QtPyVCP.VCPApplication(
        vcp=args.vcp,
        ini=args.ini,
        perfmon=args.perfmon,
        theme=args.theme,
        stylesheet=args.stylesheet,
        command_line_args=args.display_args,
        window_kwargs={'size': args.size,
                'position': args.position,
                'hide_menu_bar': args.hide_menu_bar,
                'hide_status_bar': args.hide_status_bar,
                'maximize': args.maximize,
                'fullscreen': args.fullscreen,
            }
        )

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
