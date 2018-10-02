#!/usr/bin/env python

"""
Brender - A QtPyVCP based Virtual Control Panel for LinuxCNC.

Usage:
  brender --ini=INI [--log-level=LEVEL] [--log-file=FILE] [--perfmon]
            [--theme=THEME] [--stylesheet=SYTLESHEET] [--pref-file=FILE]
            [--size=WIDTHxHEIGHT] [--position=XPOSxYPOS]
            [--fullscreen] [--maximize] [--hide-menu-bar] [--hide-status-bar]
  brender (-h | --help)
  brender (-v | --version)

Display  Options:
  --vcp VCP          The name of the VCP to launch. If not specified a
                     graphical chooser dialog will be shown.
  --theme THEME      The Qt theme to use, defaults to system theme.
  --stylesheet STYLESHEET
                     Path to QSS file containing styles to be applied
                     to specific Qt and/or QtPyVCP widget classes.
  --size WIDTHxHEIGHT
                     Initial size of the window in pixels.
  --position XPOSxYPOS
                     Initial position of the window, specified as the
                     coordinates of the top left corner of the window
                     relative to the top left corner of the screen.
  -f --fullscreen    Flag to start with window fullscreen.
  -m --maximize      Flag to start with window maximized.
  --hide-menu-bar    Hides the menu bar, if present.
  --hide-status-bar  Hides the status bar, if present.

Application Options:
  --log-level=(DEBUG | INFO | WARN | ERROR | CRITICAL)
                     Sets the log level. [default: INFO]
  --log-file=FILE    Specifies the log file. Overrides INI setting.
  --pref-file=FILE   Specifies the preference file. Overrides INI setting.
  --perfmon          Monitor and log system performance.
  --command_line_args <args>...

General Options:
  -h --help          Show this help and exit.
  -v --version       Show version.

Note:
  When specifying Brender in the INI using [DISPLAY]DISPLAY=brender [...]
  the --ini parameter will be passed by the linuxcnc startup script so does
  not need to be specified.

"""

__version__ = '0.0.1'

import sys
from QtPyVCP.utilities.opt_parser import parse_opts

if __name__ == '__main__':
    opts = parse_opts(__doc__, vcp_name='Brender', vcp_version=__version__)
    from brender import MainWindow
    from QtPyVCP.application import VCPApplication
    app = VCPApplication(opts=opts)
    app.window = MainWindow(opts=opts)
    app.window.show()
    sys.exit(app.exec_())
