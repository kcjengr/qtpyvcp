import os
from qtpyvcp.lib.types import DotDict

__version__ = '0.0.1'

QTPYVCP_DIR = os.path.abspath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(QTPYVCP_DIR)

DEFAULT_CONFIG_FILE = os.path.join(QTPYVCP_DIR, 'default_config.yml')


# globals
CONFIG = {}
OPTIONS = DotDict()
PLUGINS = {}
DIALOGS = {}
WINDOWS = {}
