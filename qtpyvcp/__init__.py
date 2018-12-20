import os

import os
from collections import OrderedDict

from qtpyvcp.lib.types import DotDict

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

QTPYVCP_DIR = os.path.abspath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(QTPYVCP_DIR)

DEFAULT_CONFIG_FILE = os.path.join(QTPYVCP_DIR, 'yaml_lib/default_config.yml')

# globals
CONFIG = {}
OPTIONS = DotDict()
PLUGINS = OrderedDict()  # Ordered dict so can terminate in order initiated
DIALOGS = {}
WINDOWS = {}
SETTINGS = {}
KEYBOARDS = {}

# for backward compatibility
from qtpyvcp.app import run
def run_vcp(*args, **kwargs):
    run(*args, **kwargs)
