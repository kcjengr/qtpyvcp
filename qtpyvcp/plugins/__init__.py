"""Data Plugins.

This module handles the initialization of standard and custom data plugins,
and maintains a global registry of plugin protocols vs. plugin instances.
"""
import importlib

from qtpyvcp import CONFIG_DICT
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins.plugin import QtPyVCPDataPlugin, QtPyVCPDataChannel

LOG = getLogger(__name__)

# Global registry of plugin protocols vs. plugin instances
DATA_PLUGIN_REGISTRY = {}


class NoSuchPlugin(Exception):
    pass


def loadDataPlugins(plugins):
    """Load data plugins from list of object references.

    Args:
        plugins (list) : List of dictionaries.
    """

    for plugin_dict in plugins:

        protocol = plugin_dict['role']
        object_ref = plugin_dict['provider']
        args = plugin_dict.get('args', [])
        kwargs = plugin_dict.get('kwargs', {})

        LOG.debug("Loading data plugin: {}".format(object_ref))

        modname, sep, clsname = object_ref.partition(':')

        try:
            plugin = getattr(importlib.import_module(modname), clsname)
        except Exception:
            LOG.critical("Failed to import data plugin.")
            raise

        assert issubclass(plugin, QtPyVCPDataPlugin), "Not a valid plugin, must be a QtPyVCPDataPlugin subclass."

        if protocol in DATA_PLUGIN_REGISTRY:
            LOG.warning("Replacing {} with {} for use with protocol {}"
                        .format(DATA_PLUGIN_REGISTRY[protocol].__class__,
                                plugin,
                                protocol)
                        )

        try:
            DATA_PLUGIN_REGISTRY[protocol] = plugin(*args, **kwargs)
        except TypeError:
            LOG.critical("Error initializing plugin: {}(*{}, **{})".format(object_ref, args, kwargs))
            raise


def getPluginFromProtocol(protocol):
    """Get data plugin instance from a protocol name.

    Args:
        protocol (str) : The protocol of the plugin to retrieve.

    Returns:
        A plugin instance, or None.

    Raises:
        NoSuchPlugin if the no plugin for ``protocol`` is found.
    """
    try:
        return DATA_PLUGIN_REGISTRY[protocol]
    except KeyError:
        raise NoSuchPlugin("Failed to find plugin for '{}' protocol.".format(protocol))


loadDataPlugins(CONFIG_DICT['data_plugins'])