"""
QtPyVCP Plugins
---------------

These package level functions provide methods for registering and initializing
plugins, as well as retrieving them for use and terminating them in the proper
order.
"""
import os
import importlib

from pprint import pprint
from collections import OrderedDict

import qtpyvcp

from qtpyvcp import DEFAULT_CONFIG_FILE, CONFIG
from qtpyvcp.utilities.config_loader import load_config_files_from_env
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins.base_plugins import Plugin, DataPlugin, DataChannel

LOG = getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)
_PLUGINS = OrderedDict()  # Ordered dict so we can initialize/terminate in order


CONFIG_DATA = None


def _initializeDesignerPlugin(plugin_id):
    
    global CONFIG_DATA
    
    if CONFIG_DATA is None:
        
        CONFIG_DATA = load_config_files_from_env()
    
    
    plugin = CONFIG_DATA["data_plugins"][plugin_id]
    
    module_path = plugin["provider"].split(':')[0]
    class_name = plugin["provider"].split(':')[1]
    class_kwards = plugin.get("kwargs")
    
    module = importlib.import_module(module_path)
    
    plugin_cls = getattr(module, class_name)
    if class_kwards:
        plugin_inst = plugin_cls(**class_kwards)
    else:
        plugin_inst = plugin_cls()
    
    registerPlugin(plugin_id, plugin_inst)
    
    LOG.debug("Loaded designer plugin: %s", plugin_id)


def registerPlugin(plugin_id, plugin_inst):
    """Register a Plugin instance.

    Args:
        plugin_id (str) : The unique name to register the plugin under.
        plugin_inst(plugin_inst) : The plugin instance to register.
    """

    if plugin_id in _PLUGINS:
            
        LOG.warning(f"Plugin '{plugin_id}' already loaded")    
        # LOG.warning("Replacing {} with {} for use with '{}' plugin"
        #             .format(_PLUGINS[plugin_id].__class__, plugin_inst.__class__, plugin_id))
    else:
        _PLUGINS[plugin_id] = plugin_inst


def registerPluginFromClass(plugin_id, plugin_cls, args=[], kwargs={}):
    """Register a plugin from a class.

    This is primarily used for registering plugins defined in the YAML config.

    .. code-block:: yaml

        data_plugins:
          my_plugin:
            provider: my_package.my_module:MyPluginClass
            args:
              - 10
              - False
            kwargs:
              my_number: 75
              my_string: A string argument

    Args:
        plugin_id (str) : A unique name to register the plugin under.
        plugin_cls (class, str) : A :py:class:`.Plugin` subclass, or a fully
            qualified class spec of format ``package.module:Class`` specifying
            the location of an importable :py:class:`.Plugin` subclass.
        args (list) : Arguments to pass to the plugin's __init__ method.
        kwargs (dict) : Keyword argument to pass to the plugin's __init__ method.

    Returns:
        The plugin instance
    """

    if isinstance(plugin_cls, str):
        LOG.debug("Loading plugin '{}' from '{}'".format(plugin_id, plugin_cls))

        modname, sep, clsname = plugin_cls.partition(':')

        try:
            plugin_cls = getattr(importlib.import_module(modname), clsname)
        except Exception:
            LOG.critical("Failed to import data plugin.")
            raise

    assert issubclass(plugin_cls, Plugin), "Not a valid plugin, must be a qtpyvcp.plugins.Plugin subclass."

    try:
        inst = plugin_cls(*args, **kwargs)
        registerPlugin(plugin_id, inst)
        return inst
    except TypeError:
        LOG.critical("Error initializing plugin: {}(*{}, **{})".format(plugin_cls, args, kwargs))
        raise


def getPlugin(plugin_id):
    """Get plugin instance from ID.

    Args:
        plugin_id (str) : The ID of the plugin to retrieve.

    Returns:
        A plugin instance, or None.
    """
    if plugin_id not in _PLUGINS:
        _initializeDesignerPlugin(plugin_id)
        
    try:
        return _PLUGINS[plugin_id]
    except KeyError:
        LOG.error("Failed to find plugin with ID '%s'", plugin_id)
        return None



def iterPlugins():
    """Returns an iterator for the plugins dict."""
    return iter(_PLUGINS.items())


def initialisePlugins():
    """Initializes all registered plugins.

        Plugins are initialized in the order they were registered in.
        Plugins defined in the YAML file are registered in the order they
        were defined.
    """
    for plugin_id, plugin_inst in list(_PLUGINS.items()):
        LOG.debug("Initializing '%s' plugin", plugin_id)
        plugin_inst.initialise()


def postGuiInitialisePlugins(main_window):
    """Initializes all registered plugins after main window is shown.

        Plugins are initialized in the order they were registered in.
        Plugins defined in the YAML file are registered in the order they
        were defined.
    """
    for plugin_id, plugin_inst in list(_PLUGINS.items()):
        LOG.debug("Post GUI Initializing '%s' plugin", plugin_id)
        plugin_inst.postGuiInitialise(main_window)


def terminatePlugins():
    """Terminates all registered plugins.

        Plugins are terminated in the reverse order they were registered in.
        If an error is encountered while terminating a plugin it will be ignored
        and the remaining plugins will still be terminated.
    """
    # terminate in reverse order, this is to prevent problems
    # when terminating plugins that make use of other plugins.
    for plugin_id, plugin_inst in reversed(list(_PLUGINS.items())):
        LOG.debug("Terminating '%s' plugin", plugin_id)
        try:
            # try so that other plugins are terminated properly
            # even if one of them fails.
            plugin_inst.terminate()
        except Exception:
            LOG.exception("Error terminating '%s' plugin", plugin_id)
