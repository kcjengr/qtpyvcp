import os
import sys
import time
import importlib
from pkg_resources import iter_entry_points

from qtpy.QtWidgets import QApplication

import qtpyvcp
from qtpyvcp import hal
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import loadDataPlugins
from qtpyvcp.utilities.settings import addSetting
from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog, IGNORE_LIST

from qtpyvcp.utilities.info import Info

LOG = getLogger(__name__)
INFO = Info()

# Catch unhandled exceptions and display in dialog
def excepthook(exc_type, exc_msg, exc_tb):
    try:
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lineno = exc_tb.tb_lineno
    except AttributeError:
        # AttributeError: 'NoneType' object has no attribute 'tb_frame'
        filename = 'unknown file'
        lineno = -1


    if len(IGNORE_LIST) > 0 and (str(exc_type), str(exc_msg), lineno) in IGNORE_LIST:
        LOG.debug('Ignoring unhandled exception in %s line %i', filename, lineno,
                     exc_info=(exc_type, exc_msg, exc_tb))
        return

    LOG.critical('Unhandled exception in %s line %i', filename, lineno,
                 exc_info=(exc_type, exc_msg, exc_tb))

    # if an exception occurs early on a qApp may not have been created yet,
    # so create one so the dialog will be able to run without errors.
    if QApplication.instance() is None:
        app = QApplication([])

    error_dialog = ErrorDialog(exc_info=(exc_type, exc_msg, exc_tb))
    error_dialog.exec_()

sys.excepthook = excepthook

def log_time(task, times=[time.time(), time.time()]):
    now = time.time()
    LOG.debug("yellow<Time:> {:.3f} (green<{:+.3f}>) - {}"
              .format(now - times[0], now - times[1], task))
    times[1] = now

log_time("in script")


def launch_application(opts, config):
    qtpyvcp.OPTIONS.update(opts)
    qtpyvcp.CONFIG.update(config)

    hal_comp = hal.component('qtpyvcp')

    LOG.debug('Loading data plugings')
    loadDataPlugins(config['data_plugins'])
    log_time('done loading data plugins')

    LOG.debug('Initializing app')
    app = _initialize_object_from_dict(config['application'])
    log_time('done initializing app')

    LOG.debug('Loading dialogs')
    loadDialogs(config['dialogs'])
    log_time('done loading dialogs')

    LOG.debug('Loading windows')
    loadWindows(config['windows'])
    log_time('done loading windows')

    LOG.debug('Initializing widgets')
    app.initialiseWidgets()
    log_time('done initializing widgets')

    hal_comp.ready()

    # load any post GUI hal file
    postgui_halfile = INFO.getPostguiHalfile()
    if postgui_halfile is not "":
        if not os.path.exists(postgui_halfile):
            raise IOError('The specified POSTGUI_HALFILE does not exist: %s' %
                          postgui_halfile)

        ini_path = INFO.INI_FILE

        LOG.info('Loading POSTGUI_HALFILE: %s', postgui_halfile)

        res = os.spawnvp(os.P_WAIT, "halcmd", ["halcmd", "-i", ini_path, "-f", postgui_halfile])

        if res:
            raise SystemExit("Failed to load POSTGUI_HALFILE with error: %s" % res)

    sys.exit(app.exec_())


def load_vcp(opts):

    vcp = opts.vcp
    if vcp is None:
        return

    vcp_path = os.path.realpath(os.path.join(os.getenv('OLDPWD', '~'), vcp))
    if os.path.isfile(vcp_path):

        LOG.debug("Attempting to load VCP from file: {}".format(vcp_path))

        directory, filename = os.path.split(vcp_path)
        name, ext = os.path.splitext(filename)

        if ext.lower() in ['.yaml', '.yml']:
            _load_vcp_from_yaml_file(vcp_path, opts)
            return

        elif ext.lower() == '.ui':
            _load_vcp_from_ui_file(vcp_path, opts)
            return

    if _load_vcp_from_entry_point(vcp, opts):
        return

    LOG.error("Could not load {}, make sure that the name or "
              "file path is correct.".format(vcp_path))


def _load_vcp_from_yaml_file(yaml_file, opts):
    LOG.info("Loading VCP from YAML file: yellow<{}>".format(yaml_file))
    from qtpyvcp.utilities.config_loader import load_config_files
    cfg_files = [opts.config_file or '']
    cfg_files.extend(os.getenv('VCP_CONFIG_FILES', '').split(':'))
    cfg_files.append(yaml_file)
    cfg_files.append(qtpyvcp.DEFAULT_CONFIG_FILE)
    config = load_config_files(*cfg_files)
    # add the YAML file dir to path so can import relative modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(yaml_file)))
    launch_application(opts, config)


def _load_vcp_from_ui_file(ui_file, opts):
    LOG.info("Loading VCP from UI file: yellow<{}>".format(ui_file))
    from qtpyvcp.utilities.config_loader import load_config_files
    cfg_files = [opts.config_file or '']
    cfg_files.extend(os.getenv('VCP_CONFIG_FILES', '').split(':'))
    cfg_files.append(qtpyvcp.DEFAULT_CONFIG_FILE)
    config = load_config_files(*cfg_files)
    kwargs = config['windows']['mainwindow'].get('kwargs', {})
    kwargs.update({'ui_file': ui_file})
    config['windows']['mainwindow']['kwargs'] = kwargs
    launch_application(opts, config)


def _load_vcp_from_entry_point(vcp_name, opts):
    entry_points = {}
    for entry_point in iter_entry_points(group='qtpyvcp.example_vcp'):
        entry_points[entry_point.name] = entry_point
    for entry_point in iter_entry_points(group='qtpyvcp.test_vcp'):
        entry_points[entry_point.name] = entry_point
    for entry_point in iter_entry_points(group='qtpyvcp.vcp'):
        entry_points[entry_point.name] = entry_point

    try:
        vcp = entry_points[vcp_name.lower()].load()
    except KeyError:
        LOG.exception("Failed to find entry point: {}".format(vcp_name))
    except Exception as e:
        LOG.debug(e)
        LOG.exception("Failed to load entry point: {}".format(vcp_name))
    else:
        vcp.main(opts)

        LOG.info("Loading VCP from entry point: {}".format(vcp_name))
        vcp.main(opts)
        return True


def _get_object_by_referance(object_ref):
    modname, sep, attrname = object_ref.partition(':')
    try:
        return getattr(importlib.import_module(modname), attrname)
    except Exception:
        LOG.critical("Failed to get object by reference: {}".format(object_ref))
        raise


def _initialize_object_from_dict(object_dict, parent=None):
    """Initialize a python object from dict."""
    provider = object_dict['provider']
    args = object_dict.get('args') or []
    kwargs = object_dict.get('kwargs') or {}

    obj = _get_object_by_referance(provider)

    if parent is not None:
        kwargs.update({'parent': parent})

    return obj(*args, **kwargs)


def loadWindows(windows):
    for window_id, window_dict in windows.items():

        window = _initialize_object_from_dict(window_dict)
        qtpyvcp.WINDOWS[window_id] = window

        # show the window by default
        if window_dict.get('show', True):
            window.show()


def loadDialogs(dialogs):
    for dialogs_id, dialogs_dict in dialogs.items():

        inst = _initialize_object_from_dict(dialogs_dict)
        qtpyvcp.DIALOGS[dialogs_id] = inst
