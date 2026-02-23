"""
QtPyVCP Plugins
---------------

These package level functions provide methods for registering and initializing
plugins, as well as retrieving them for use and terminating them in the proper
order.
"""
import os
import importlib

from collections import OrderedDict

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins.base_plugins import Plugin, DataPlugin, DataChannel

LOG = getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)
_PLUGINS = OrderedDict()  # Ordered dict so we can initialize/terminate in order
_DESIGNER_PLUGINS_LOADED = False  # Track if designer plugins have been initialized


class NullPlugin:
    """Placeholder plugin that responds to any method call with safe defaults.
    
    Used in designer mode when plugins aren't available to prevent AttributeErrors.
    """
    def __getattr__(self, name):
        """Return a callable that returns False or empty data by default."""
        def null_method(*args, **kwargs):
            # Return False for boolean-like methods (is*, check*, etc)
            if name.startswith(('is', 'check', 'has', 'get')):
                return False
            # Return None for other methods
            return None
        return null_method
    
    def __call__(self, *args, **kwargs):
        """Allow calling the plugin itself."""
        return False


_NULL_PLUGIN = NullPlugin()



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
        A plugin instance, or a NullPlugin instance in designer mode if not found.
    """
    try:
       return _PLUGINS[plugin_id]
    except KeyError:
        if IN_DESIGNER:
            # In designer mode, try to auto-load commonly used plugins
            _initializeDesignerPlugins()
            # Try again after loading designer plugins
            if plugin_id in _PLUGINS:
                return _PLUGINS[plugin_id]
            # If still not found, return a null plugin that won't crash
            LOG.debug("Plugin '%s' not found, using null plugin for designer", plugin_id)
            return _NULL_PLUGIN
        else:
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


def _initializeDesignerPlugins():
    """Initialize commonly used plugins in Designer mode.
    
    This function is called automatically when getPlugin() is called in designer mode
    and the requested plugin is not found. It loads essential plugins that widgets
    commonly depend on, allowing widgets to work properly in the designer.
    """
    global _DESIGNER_PLUGINS_LOADED
    
    if _DESIGNER_PLUGINS_LOADED:
        return
    
    _DESIGNER_PLUGINS_LOADED = True
    
    # Dictionary of essential plugins to load in designer mode
    # Format: plugin_id: (module_path, class_name, kwargs)
    essential_plugins = {
        'status': ('qtpyvcp.plugins.status', 'Status', {'cycle_time': 100}),
        'position': ('qtpyvcp.plugins.positions', 'Position', {}),
        'clock': ('qtpyvcp.plugins.clock', 'Clock', {}),
        'settings': ('qtpyvcp.plugins.settings', 'Settings', {}),
        'tooltable': ('qtpyvcp.plugins.tool_table', 'ToolTable', {}),
        'offsettable': ('qtpyvcp.plugins.offset_table', 'OffsetTable', {}),
        'notifications': ('qtpyvcp.plugins.notifications', 'Notifications', {}),
        'persistent_data_manager': ('qtpyvcp.plugins.persistent_data_manager', 'PersistentDataManager', {}),
        'file_locations': ('qtpyvcp.plugins.file_locations', 'FileLocations', {}),
    }
    
    LOG.debug("Initializing essential plugins for Designer mode")
    
    for plugin_id, (module_path, class_name, kwargs) in essential_plugins.items():
        # Skip if already registered
        if plugin_id in _PLUGINS:
            continue
        
        try:
            # Import the module and get the class
            module = importlib.import_module(module_path)
            plugin_cls = getattr(module, class_name)
            
            # Instantiate and register the plugin
            plugin_inst = plugin_cls(**kwargs)
            registerPlugin(plugin_id, plugin_inst)
            LOG.debug("Loaded designer plugin: %s", plugin_id)
            
        except ImportError as e:
            # Module import failed (e.g., linuxcnc not available)
            LOG.debug("Could not import designer plugin '%s' module: %s", plugin_id, e)
        except AttributeError as e:
            # Class not found in module
            LOG.debug("Could not find class for designer plugin '%s': %s", plugin_id, e)
        except Exception as e:
            # Plugin initialization failed
            LOG.debug("Could not initialize designer plugin '%s': %s", plugin_id, e)
