import os
from ._version import get_versions
from qtpyvcp.lib.types import DotDict

__version__ = get_versions()['version']
del get_versions

QTPYVCP_DIR = os.path.abspath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(QTPYVCP_DIR)

DEFAULT_CONFIG_FILE = os.path.join(QTPYVCP_DIR, 'yaml_lib/default_config.yml')


# globals
CONFIG = {}
OPTIONS = DotDict()
PLUGINS = {}
DIALOGS = {}
WINDOWS = {}
