import os
import sys
if (sys.version_info > (3, 0)):
    print("ERROR: It appears QtDesigner is trying to load the QtPyVCP widgets \n"
          "using a python version greater than 2.7, this is not supported. \n"
          "Make sure that you have the correct version of the libpyqt5.so \n"
          "file in /usr/lib/x86_64-linux-gnu/qt5/plugins/designer/, see the \n"
          "Installation Trouble Shooting section of the QtPyVCP Documents for more info.")
    sys.exit()

import qtpy
if qtpy.API != 'pyqt5':
    print("ERROR: You must use the PyQt5 bindings in order to use the custom \n"
          "widgets in QtDesigner.")
    sys.exit()

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

from qtpyvcp.plugins import loadDataPlugins
loadDataPlugins(CONFIG['data_plugins'])

from qtpyvcp.widgets.form_widgets.designer_plugins import *
from qtpyvcp.widgets.button_widgets.designer_plugins import *
from qtpyvcp.widgets.display_widgets.designer_plugins import *
from qtpyvcp.widgets.input_widgets.designer_plugins import *
from qtpyvcp.widgets.hal_widgets.designer_plugins import *
from qtpyvcp.widgets.containers.designer_plugins import *

# load external designer plugins
from pkg_resources import iter_entry_points

for entry_point in iter_entry_points(group='qtpyvcp.widgets'):

    group_name = entry_point.name
    mod = entry_point.load()

    for name in dir(mod):
        if name.startswith('_'):
            continue

        plugin_cls = getattr(mod, name)
        plugin_cls.group_name = group_name
        globals()[name] = plugin_cls