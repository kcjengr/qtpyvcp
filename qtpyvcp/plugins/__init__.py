"""Data Plugins.

This module handles the initialization of standard and custom data plugins,
and maintains a global registry of plugin protocols vs. plugin instances.
"""
import importlib
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins.plugin import QtPyVCPDataPlugin, QtPyVCPDataChannel

LOG = getLogger(__name__)

# Global registry of plugin protocols vs. plugin instances
DATA_PLUGIN_REGISTRY = {}

DEFAULT_PLUGINS = (
    'qtpyvcp.plugins.status:Status',
    # 'qtpyvcp.plugins.hal_status:HALStatus',
    'qtpyvcp.plugins.positions:Position',
    'qtpyvcp.plugins.tool_table:ToolTable',
)


class NoSuchPlugin(Exception):
    pass


def loadDataPlugins(plugins):
    """Load data plugins from list of object references.

    Args:
        plugins (list) : List of string references to QtPyVCPDataPlugin subclasses
            in the format ``package.plugin_module:PluginClass``.
    """
    for object_ref in plugins:
        LOG.debug("Loading data plugin: {}".format(object_ref))

        modname, sep, clsname = object_ref.partition(':')

        try:
            plugin = getattr(importlib.import_module(modname), clsname)
        except Exception:
            LOG.critical("Failed to import data plugin.")
            raise

        assert issubclass(plugin, QtPyVCPDataPlugin), "Not a valid plugin, must be a QtPyVCPDataPlugin subclass."

        if plugin.protocol in DATA_PLUGIN_REGISTRY:
            LOG.warning("Replacing {} with {} for use with protocol {}"
                        .format(plugin,
                                DATA_PLUGIN_REGISTRY[plugin.protocol].__class__,
                                plugin.protocol)
                        )

        DATA_PLUGIN_REGISTRY[plugin.protocol] = plugin()


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


loadDataPlugins(DEFAULT_PLUGINS)