#!/usr/bin/env python

"""
QtPyVCP - Qt and Python based Virtual Control Panel framework for LinuxCNC.

Usage:
  qtpyvcp --ini=INI [<vcp>] [options]
  qtpyvcp (-h | --help)
  qtpyvcp (-v | --version)

Required Arguments:
  --ini INI            Path to INI file, relative to ~/linuxcnc/configs.

Display  Options:
  --vcp VCP            The name of the VCP to launch. If not specified a
                       graphical chooser dialog will be shown.
  --theme THEME        The Qt theme to use, defaults to system theme.
  --stylesheet STYLESHEET
                       Path to QSS file containing styles to be applied
                       to specific Qt and/or QtPyVCP widget classes.
  --size WIDTHxHEIGHT
                       Initial size of the window in pixels.
  --position XPOSxYPOS
                       Initial position of the window, specified as the
                       coordinates of the top left corner of the window
                       relative to the top left corner of the screen.
  --fullscreen BOOL    Flag to start with window fullscreen.
  --maximize BOOL      Flag to start with window maximized.
  --hide-menu-bar      Hides the menu bar, if present.
  --hide-status-bar    Hides the status bar, if present.
  --hide-cursor        Hide the mouse cursor.
  --confirm-exit BOOL  Whether to show dialog to confirm exit.

Application Options:
  --log-level=(DEBUG | INFO | WARN | ERROR | CRITICAL)
                       Sets the log level. Default INFO
  --config-file=FILE   Specifies the YML config file.
  --log-file=FILE      Specifies the log file. Overrides INI setting.
  --pref-file=FILE     Specifies the preference file. Overrides INI setting.
  --qt-api=(pyqt5 | pyqt | pyside2 | pyside)
                       Specify the Qt Python binding to use.
  --perfmon            Monitor and log system performance.
  --command_line_args <args>...
                       Additional args passed to the QtApplication.

General Options:
  --chooser            Forces the graphical VCP chooser to be shown. If a VCP
                       was specified it will be ignored. Useful for overriding
                       a VCP specified in an INI file.
  -h --help            Show this help and exit.
  -v --version         Show version.

Note:
  When specifying QtPyVCP in the INI using [DISPLAY]DISPLAY=qtpyvcp [...]
  the --ini parameter will be passed by the linuxcnc startup script so does
  not need to be specified.

"""

import os
from collections import OrderedDict
from qtpyvcp.lib.types import DotDict

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

QTPYVCP_DIR = os.path.abspath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(QTPYVCP_DIR)

DEFAULT_CONFIG_FILE = os.path.join(QTPYVCP_DIR, 'yaml_lib/default_config.yml')

# globals
CONFIG = {}
OPTIONS = DotDict()
PLUGINS = OrderedDict()  # Ordered dict so can terminate in order initiated
DIALOGS = {}
WINDOWS = {}
SETTINGS = {}


def main():
    """QtPyVCP Main entry point

    This method is called when running `qtpyvcp` directly from the
    command line. The command line options are generated from the
    docstring at the beginning of this module.
    """
    from qtpyvcp.utilities.opt_parser import parse_opts
    opts = parse_opts(__doc__)
    run_vcp(opts, None)


def run_vcp(opts, config_file=None):
    """VCP Entry Point

    This method is used by individual VCPs to launch QtPyVCP. This
    method should NOT be called directly. Options are generated either
    from a specification in the VCP, or from a generic fallback generated
    by the `opt_parser` utility.

    Args:
        opts (OptDict) : Dictionary of command line options as generated
            by the opt_parser utility.
        config_file (str, optional) : A YAML format config file to load.
            If `config_file` is not None it will be merged with any other
            config files and the VCP will be loaded from that info, else
            the VCP will be loaded solely from the options passed in the
            options dict.
    """
    if config_file is None:
        # we are probably running from a entry point or a bare .ui file
        from qtpyvcp.vcp_launcher import load_vcp
        load_vcp(opts)

    else:
        # almost certainly being called from a VCP's __init__.py file

        # list of YAML config files, in order of highest to lowest priority
        config_files = list()

        # cmd line or INI files should have highest priority
        if opts.config_file is not None:
            config_files.append(opts.config_file)

        # env files should have second highest priority
        env_cfgs = os.getenv('VCP_CONFIG_FILES')
        if env_cfgs is not None:
            config_files.extend(env_cfgs.strip(':').split(':'))

        # VCP specific config files
        config_files.append(config_file)

        # default config file has lowest priority
        config_files.append(DEFAULT_CONFIG_FILE)

        from qtpyvcp.utilities.config_loader import load_config_files
        config = load_config_files(*config_files)

        from qtpyvcp.vcp_launcher import launch_application
        launch_application(opts, config)


if __name__ == '__main__':
    main()
