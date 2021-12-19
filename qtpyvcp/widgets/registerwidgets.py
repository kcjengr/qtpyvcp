import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

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
loadPlugins(CONFIG['data_plugins'])

from qtpyvcp.widgets.form_widgets.designer_plugins import *
from qtpyvcp.widgets.button_widgets.designer_plugins import *
from qtpyvcp.widgets.display_widgets.designer_plugins import *
from qtpyvcp.widgets.input_widgets.designer_plugins import *
from qtpyvcp.widgets.hal_widgets.designer_plugins import *
from qtpyvcp.widgets.containers.designer_plugins import *

from qtpyvcp.widgets.external_widgets import *

# Set PYSIDE_DESIGNER_PLUGINS to point to this directory and load the plugin


if __name__ == '__main__':
    QPyDesignerCustomWidgetCollection.addCustomWidget(ProbePlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ActionButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ActionCheckBoxPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ActionSpinBoxPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(MacroButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(LedButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(MDIButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(DialogButtonPlugin())
