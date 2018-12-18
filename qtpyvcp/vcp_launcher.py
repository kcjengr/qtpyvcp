#!/usr/bin/env python

import os
import sys
import time
import importlib
from pkg_resources import iter_entry_points

import qtpyvcp
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import loadDataPlugins


LOG = getLogger(__name__)

def log_time(task, times=[time.time(), time.time()]):
    now = time.time()
    LOG.debug("yellow<Time:> {:.3f} (green<{:+.3f}>) - {}".format(now - times[0], now - times[1], task))
    times[1] = now

log_time("in script")


def launch_application(opts, config):
    qtpyvcp.OPTIONS = opts
    qtpyvcp.CONFIG = config

    print 'Loading data plugings'
    loadDataPlugins(config['data_plugins'])
    log_time('done loading data plugins')

    print 'Initializing app'
    app = _initialize_object_from_dict(config['application'])
    log_time('done initializing app')

    print 'Loading dialogs'
    loadDialogs(config['dialogs'])
    log_time('done loading dialogs')

    print 'Loading windows'
    loadWindows(config['windows'])
    log_time('done loading windows')

    sys.exit(app.exec_())


def load_vcp(opts):

    vcp = opts.vcp
    if vcp is None:
        return

    if os.path.exists(vcp):

        vcp_path = os.path.realpath(vcp)

        if os.path.isfile(vcp_path):
            directory, filename = os.path.split(vcp_path)
            name, ext = os.path.splitext(filename)

            if ext in ['.yaml', '.yml']:
                _load_vcp_from_yaml_file(vcp_path, opts)

            elif ext == '.ui':
                _load_vcp_from_ui_file(vcp_path, opts)

        elif os.path.isdir(vcp_path):
            LOG.info("VCP is a directory")
            # TODO: Load from a directory if it has a __main__.py entry point

    else:
        _load_vcp_from_entry_point(vcp, opts)
        return

    LOG.critical("VCP could not be loaded: yellow<{}>".format(vcp))
    sys.exit()


def _load_vcp_from_yaml_file(yaml_file, opts):
    LOG.info("Loading VCP from YAML file: yellow<{}>".format(yaml_file))
    from qtpyvcp.utilities.config_loader import load_config_files
    config = load_config_files(opts.config_file, yaml_file, *os.getenv('VCP_CONFIG_FILES', '').split(':'))
    launch_application(opts, config)


def _load_vcp_from_ui_file(ui_file, opts):
    LOG.info("Loading VCP from UI file: yellow<{}>".format(ui_file))
    from qtpyvcp.utilities.config_loader import load_config_files_from_env
    config = load_config_files_from_env()
    kwargs = config['windows']['mainwindow'].get('kwargs', {})
    kwargs.update({'ui_file': ui_file})
    config['windows']['mainwindow']['kwargs'] = kwargs
    launch_application(opts, config)


def _load_vcp_from_entry_point(vcp_name, opts):
    entry_points = {}
    for entry_point in iter_entry_points(group='qtpyvcp.example_vcp'):
        entry_points[entry_point.name] = entry_point
    for entry_point in iter_entry_points(group='qtpyvcp.vcp'):
        entry_points[entry_point.name] = entry_point

    try:
        vcp = entry_points[vcp_name.lower()].load()
    except KeyError:
        LOG.exception("Failed to find entry point: {}".format(vcp_name))
    except:
        LOG.exception("Failed to load entry point: {}".format(vcp_name))
    else:
        vcp.run(opts)


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
