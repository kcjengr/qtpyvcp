import os
import sys

os.environ['DESIGNER'] = 'true'

from qtpyvcp.utilities.logger import initBaseLogger
LOG = initBaseLogger("qtpyvcp-designer",
                     log_level=os.getenv('QTPYVCP_LOG_LEVEL', 'ERROR'),
                     log_file=os.getenv('QTPYVCP_LOG_FILE',
                              os.path.expanduser('~/qtpyvcp-designer.log'))
                     )

from qtpyvcp import CONFIG, DEFAULT_CONFIG_FILE
os.environ['VCP_CONFIG_FILES'] = os.getenv('VCP_CONFIG_FILES', '') + \
                                 ':' + DEFAULT_CONFIG_FILE

from qtpyvcp.utilities.config_loader import load_config_files_from_env
CONFIG.update(load_config_files_from_env())

from qtpyvcp.app.launcher import loadPlugins
if CONFIG.get('data_plugins'):
    loadPlugins(CONFIG['data_plugins'])
    from qtpyvcp.plugins import _PLUGINS
    LOG.info(f"Loaded {len(_PLUGINS)} plugin(s) in designer: {', '.join(_PLUGINS.keys())}")
else:
    LOG.warning("No data_plugins found in config")

from qtpyvcp.widgets.form_widgets.designer_plugins import *
from qtpyvcp.widgets.button_widgets.designer_plugins import *
from qtpyvcp.widgets.display_widgets.designer_plugins import *
from qtpyvcp.widgets.input_widgets.designer_plugins import *
from qtpyvcp.widgets.hal_widgets.designer_plugins import *
from qtpyvcp.widgets.containers.designer_plugins import *
from qtpyvcp.widgets.db_widgets.designer_plugins import *

from qtpyvcp.widgets.external_widgets import *

# Register all custom widgets with Qt Designer
try:
    from qtpyvcp.widgets import register_widgets
    register_widgets.main()
except Exception as e:
    LOG.error(f"Failed to register custom widgets: {e}")
    import traceback
    LOG.error(traceback.format_exc())
