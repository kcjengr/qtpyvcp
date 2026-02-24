import os
import sys
import traceback

# Write ALL output to a debug file — pyside6-designer swallows stdout/stderr
_DBGFILE = '/tmp/pyside6_plugin_debug.txt'
def _dbg(msg):
    try:
        with open(_DBGFILE, 'a') as _f:
            _f.write(msg + '\n')
            _f.flush()
    except Exception:
        pass

_dbg("=== qtdesigner_plugin.py loading START ===")
os.environ['DESIGNER'] = 'true'

try:
    from qtpyvcp.utilities.logger import initBaseLogger
    _dbg("initBaseLogger imported OK")
    LOG = initBaseLogger("qtpyvcp-designer",
                         log_level=os.getenv('QTPYVCP_LOG_LEVEL', 'ERROR'),
                         log_file=os.getenv('QTPYVCP_LOG_FILE',
                                  os.path.expanduser('~/qtpyvcp-designer.log'))
                         )

    from qtpyvcp import CONFIG, DEFAULT_CONFIG_FILE
    _dbg(f"qtpyvcp CONFIG imported OK, DEFAULT_CONFIG_FILE={DEFAULT_CONFIG_FILE}")
    os.environ['VCP_CONFIG_FILES'] = os.getenv('VCP_CONFIG_FILES', '') + \
                                     ':' + DEFAULT_CONFIG_FILE

    from qtpyvcp.utilities.config_loader import load_config_files_from_env
    CONFIG.update(load_config_files_from_env())
    _dbg("config loaded OK")

    from qtpyvcp.app.launcher import loadPlugins
    if CONFIG.get('data_plugins'):
        loadPlugins(CONFIG['data_plugins'])
        from qtpyvcp.plugins import _PLUGINS
        _dbg(f"Loaded {len(_PLUGINS)} plugin(s): {', '.join(_PLUGINS.keys())}")
        LOG.info(f"Loaded {len(_PLUGINS)} plugin(s) in designer: {', '.join(_PLUGINS.keys())}")
    else:
        _dbg("No data_plugins found in config")
        LOG.warning("No data_plugins found in config")

    _dbg("importing form_widgets designer_plugins")
    from qtpyvcp.widgets.form_widgets.designer_plugins import *
    _dbg("importing button_widgets designer_plugins")
    from qtpyvcp.widgets.button_widgets.designer_plugins import *
    _dbg("importing display_widgets designer_plugins")
    from qtpyvcp.widgets.display_widgets.designer_plugins import *
    _dbg("importing input_widgets designer_plugins")
    from qtpyvcp.widgets.input_widgets.designer_plugins import *
    _dbg("importing hal_widgets designer_plugins")
    from qtpyvcp.widgets.hal_widgets.designer_plugins import *
    _dbg("importing containers designer_plugins")
    from qtpyvcp.widgets.containers.designer_plugins import *
    _dbg("importing db_widgets designer_plugins")
    from qtpyvcp.widgets.db_widgets.designer_plugins import *
    _dbg("importing external_widgets")

    from qtpyvcp.widgets.external_widgets import *
    _dbg("external_widgets imported OK")

    # Register all custom widgets with Qt Designer
    try:
        from qtpyvcp.widgets import register_widgets
        _dbg("register_widgets imported OK")
        register_widgets.main()
        _dbg("register_widgets.main() completed OK")
    except Exception as e:
        _dbg(f"register_widgets FAILED: {e}\n{traceback.format_exc()}")
        LOG.error(f"Failed to register custom widgets: {e}")
        LOG.error(traceback.format_exc())

    _dbg("=== qtdesigner_plugin.py loading COMPLETE ===")

except Exception as _top_e:
    _dbg(f"FATAL ERROR in qtdesigner_plugin.py: {_top_e}\n{traceback.format_exc()}")
    raise
