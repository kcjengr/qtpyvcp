"""QtPyVCP Plugins.

This module handles the initialization of standard and custom plugins,
and maintains a global registry of plugin IDs vs. plugin instances.
"""
import importlib

from collections import OrderedDict

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins.base_plugins import Plugin, DataPlugin, DataChannel

LOG = getLogger(__name__)

_PLUGINS = OrderedDict()  # Ordered dict so we can initialize/terminate in order


def registerPlugin(plugin_id, plugin_inst):
    """Register a Plugin instance.

    Args:
        plugin_id (str) : The unique name to register the plugin under.
        plugin_inst(plugin_inst) : The plugin instance to register.
    """

    if plugin_id in _PLUGINS:
        LOG.warning("Replacing {} with {} for use with '{}' plugin"
                    .format(_PLUGINS[plugin_id].__class__, plugin_inst.__class__, plugin_id))

    _PLUGINS[plugin_id] = plugin_inst


def registerPluginFromClass(plugin_id, plugin_cls, args=[], kwargs={}):
    """Register a plugin from a class.

    Args:
        plugin_id (str) : The unique name to register the plugin under.
        plugin_cls (Plugin, str) : The python class defining the plugin. Can be either
            a class reference, or a specifier with format ``package.module:Class``.
        args (list) : A arguments to pass to the plugin class.
        kwargs (dict) : A keyword argument to pass to the plugin class.

    Returns:
        The plugin instance
    """

    if isinstance(plugin_cls, basestring):
        LOG.debug("Loading plugin '{}' from '{}'".format(plugin_id, plugin_cls))

        modname, sep, clsname = plugin_cls.partition(':')

        try:
            plugin_cls = getattr(importlib.import_module(modname), clsname)
        except Exception:
            LOG.critical("Failed to import data plugin.")
            raise

    assert issubclass(plugin_cls, Plugin), "Not a valid plugin, must be a DataPlugin subclass."

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

    Raises:
        ValueError if no plugin matching ``plugin_id`` is found.
    """
    try:
        return _PLUGINS[plugin_id]
    except KeyError:
        raise ValueError("Failed to find plugin with ID: {}.".format(plugin_id))


def iterPlugins():
    """Returns an iter for the plugins dict."""
    return _PLUGINS.iteritems()


def initialisePlugins():
    """Initialize all registered plugins"""
    for plugin_id, plugin_inst in _PLUGINS.items():
        LOG.debug("Initializing '%s' plugin", plugin_id)
        plugin_inst.initialise()


def terminatePlugins():
    """Terminate all registered plugins"""
    # terminate in reverse order, this is to prevent problems
    # when terminating plugins that make use of other plugins.
    for plugin_id, plugin_inst in reversed(_PLUGINS.items()):
        LOG.debug("Terminating '%s' plugin", plugin_id)
        try:
            # try so that other plugins are terminated properly
            # even if one of them fails.
            plugin_inst.terminate()
        except Exception:
            LOG.exception("Error terminating '%s' plugin", plugin_id)
