"""
QtPyVCP - A PyQt5 based toolkit for LinuxCNC Virtual Control Panels (VCPs).

Usage:
  qtpyvcp <vcp> --ini=INI [--log-level=LEVEL] [--log-file=FILE] [--perfmon]
            [--theme=THEME] [--stylesheet=SYTLESHEET]
            [--size WIDTHxHEIGHT] [--position XPOSxYPOS]
            [--fullscreen] [--maximize] [--hide-menu-bar] [--hide-status-bar]
  qtpyvcp --ini=INI --chooser
  qtpyvcp (-h | --help)
  qtpyvcp (-v | --version)

Required Arguments:
    --ini INI        Path to INI file, relative to ~/linuxcnc/configs

Display  Options:
  --vcp VCP   The name of the VCP o
  --theme THEME      The Qt theme to use, defaults to system theme.
  --stylesheet STYLESHEET
                     Path to QSS file containing styles to be applied
                     to specific Qt and/or QtPyVCP widget classes.
  --size WIDTHxHEIGHT
                     Initial size of the window in pixels.
  --position XPOSxYPOS
                     Initial position of the window, specified as the coordinates
                     of the top left corner of the window relative to the top left
                     corner of the screen.
  -f --fullscreen    Flag to start with window fullscreen.
  -m --maximize      Flag to start with window maximized.
  --hide-menu-bar    Hides the menu bar, if present.
  --hide-status-bar  Hides the status bar, if present.

Application Options:
  --log-level=(DEBUG | INFO | WARN | ERROR | CRITICAL)
                     Sets the log level. [default: INFO]
  --log-file=FILE    Specifies the log file. Overrides setting in INI.
  --perfmon          Monitor and log system performance.
  --command_line_args <args>...

General Options:
  --chooser          Launches the VCP chooser dialog.
  -h --help          Show this help and exit.
  -v --version       Show version.

Note:
  If you have specified [DISPLAY]DISPLAY = qtpyvcp [...] in the INI file the --ini
  parameter will automatically be passed by the linuxcnc startup script.

"""
import sys
from docopt import docopt

from QtPyVCP import __version__

def parse_opts(doc=__doc__, vcp_name=None, vcp_version=None):
    # LinuxCNC passes the INI file as `-ini=inifile` which docopt sees as a
    # short argument which does not support an equals sign, so we loop thru
    # and add another dash to the ini argument if needed.
    for index, item in enumerate(sys.argv):
        if item.startswith('-ini'):
            sys.argv[index] = '-' + item
            break

    version_str = 'QtPyVCP v{}'.format(__version__)
    if vcp_version is not None:
        version_str += ', {} v{}'.format(vcp_name, vcp_version)

    raw_args = docopt(doc, version=version_str)

    # convert raw argument dict keys to valid python attribute names
    kwargs = {arg.strip('-<>').replace('-', '_') : value for arg, value in raw_args.items()}
    return OptDict(kwargs)

class OptDict(dict):
    """Simple dot.notation access for opt dictionary values"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
