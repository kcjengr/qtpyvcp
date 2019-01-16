"""
{vcp_name} - A QtPyVCP based Virtual Control Panel for LinuxCNC.

Usage:
  {vcp_cmd} --ini=INI [options]
  {vcp_cmd} (-h | --help)
  {vcp_cmd} (-v | --version)

Required Arguments:
  --ini INI          Path to INI file, relative to ~/linuxcnc/configs.

Display  Options:
  --theme=THEME      The Qt theme to use, defaults to system theme.
  --stylesheet=STYLESHEET
                     Path to QSS file containing styles to be applied
                     to specific Qt and/or QtPyVCP widget classes.
  --size=WIDTHxHEIGHT
                     Initial size of the window in pixels.
  --position=XPOSxYPOS
                     Initial position of the window, specified as the
                     coordinates of the top left corner of the window
                     relative to the top left corner of the screen.
  -f --fullscreen    Flag to start with window fullscreen.
  -m --maximize      Flag to start with window maximized.
  --hide-menu-bar    Hides the menu bar, if present.
  --hide-status-bar  Hides the status bar, if present.
  --confirm-exit BOOL
                    Whether to show dialog to confirm exit.

Application Options:
  --log-level=(DEBUG | INFO | WARN | ERROR | CRITICAL)
                     Sets the log level. [default: INFO]
  --config-file=FILE Specifies the YML config file.
  --log-file=FILE    Specifies the log file. Overrides INI setting.
  --pref-file=FILE   Specifies the preference file. Overrides INI setting.
  --qt-api=(pyqt5 | pyqt | pyside2 | pyside)
                     Specify the Qt Python binding to use.
  --perfmon          Monitor and log system performance.
  --command_line_args <args>...

General Options:
  -h --help          Show this help and exit.
  -v --version       Show version.

Note:
  When specifying {vcp_name} in the INI using [DISPLAY]DISPLAY={vcp_cmd} [...]
  the --ini parameter will be passed by the linuxcnc startup script so does
  not need to be specified.

"""
import os
import sys
import json
from linuxcnc import ini
from docopt import docopt

from qtpyvcp import __version__
from qtpyvcp.lib.types import DotDict
from qtpyvcp.utilities.misc import normalizePath

def parse_opts(doc=__doc__, vcp_name='NotSpecified', vcp_cmd='notspecified', vcp_version=None):
    # LinuxCNC passes the INI file as `-ini=inifile` which docopt sees as a
    # short argument which does not support an equals sign, so we loop thru
    # and add another dash to the ini argument if needed.
    for index, item in enumerate(sys.argv):
        if item.startswith('-ini'):
            sys.argv[index] = '-' + item
            break

    version_str = 'QtPyVCP {}'.format(__version__)
    if vcp_version is not None:
        version_str += ', {} v{}'.format(vcp_name, vcp_version)

    doc = doc.format(vcp_name=vcp_name, vcp_cmd=vcp_cmd)

    raw_args = docopt(doc, version=version_str)

    def convType(val):
        if isinstance(val, basestring):
            if val.lower() in ['true', 'on', 'yes', 'false', 'off', 'no']:
                return val.lower() in ['true', 'on', 'yes']

            try:
                return int(val)
            except ValueError:
                pass

            try:
                return float(val)
            except ValueError:
                pass

        return val

    # convert raw argument dict keys to valid python attribute names
    opts = DotDict({arg.strip('-<>').replace('-', '_') : convType(value) for arg, value in raw_args.items()})

    # read options from INI file and merge with cmd line options
    ini_file = ini(normalizePath(opts.ini, os.path.expanduser('~/linuxcnc/configs')))
    for k, v in opts.iteritems():
        ini_val = ini_file.find('DISPLAY', k.upper().replace('-', '_'))
        if ini_val is None:
            continue

        # convert str values to bool
        if type(v) == bool:
            # TODO: Find a way to prefer cmd line values over INI values
            ini_val = ini_val.lower() in ['true', 'on', 'yes', '1']

        # if its a non bool value and it was specified on the cmd line
        # then prefer the cmd line value
        elif v is not None:
            continue

        opts[k] = convType(ini_val)

    # Check if LinuxCNC is running
    if not os.path.isfile('/tmp/linuxcnc.lock'):
        # LinuxCNC is not running.
        # TODO: maybe launch LinuxCNC using subprocess?
        print 'LinuxCNC must be running to launch a VCP'
        sys.exit()

    # setup the environment variables
    ini_file = os.environ.get('INI_FILE_NAME') or opts.ini
    if ini_file is None:
        print 'LinuxCNC is running, but you must specify the INI file'
        sys.exit()

    if not os.getenv('INI_FILE_NAME'):
        base_path = os.path.expanduser('~/linuxcnc/configs')
        ini_file = os.path.realpath(normalizePath(ini_file, base_path))
        if not os.path.isfile(ini_file):
            print 'Specified INI file does not exist: {}'.format(ini_file)
            sys.exit()
        os.environ['INI_FILE_NAME'] = ini_file
        os.environ['CONFIG_DIR'] = os.path.dirname(ini_file)

    if opts.qt_api:
        os.environ['QT_API'] = opts.qt_api

    if opts.config_file is not None:
        # cmd line config file should be relative to INI file
        config_dir = os.getenv('CONFIG_DIR', '')
        config_file_path = normalizePath(opts.config_file, config_dir)
        if not os.path.isfile(config_file_path):
            print 'Specified YAML file does not exist: {}'.format(config_file_path)
            sys.exit()
        opts.config_file = config_file_path

    # show the chooser if the --chooser flag was specified
    if opts.chooser or not opts.get('vcp', True):
        from qtpyvcp.vcp_chooser import VCPChooser
        from qtpy.QtWidgets import QApplication, qApp
        app = QApplication([])
        result = VCPChooser(opts).exec_()
        if result == VCPChooser.Rejected:
            sys.exit()

        # destroy the evidence
        qApp.deleteLater()
        del app

    # normalize log file path
    log_file = normalizePath(opts.log_file,
                             os.getenv('CONFIG_DIR') or
                             os.getenv('HOME'))

    if log_file is None or os.path.isdir(log_file):
        log_file = os.path.expanduser('~/qtpyvcp.log')

    opts.log_file = log_file

    # init the logger
    from qtpyvcp.utilities import logger
    LOG = logger.initBaseLogger('qtpyvcp',
                                log_file=opts.log_file,
                                log_level=opts.log_level)

    if LOG.getEffectiveLevel() == logger.LOG_LEVEL_MAPPING['DEBUG']:
        LOG.debug("Command line options:\n%s",
                  json.dumps(opts, sort_keys=True, indent=4))

    return opts
