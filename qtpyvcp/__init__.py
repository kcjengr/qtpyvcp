import os

import os
from collections import OrderedDict

from qtpyvcp.lib.types import DotDict

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

QTPYVCP_DIR = os.path.abspath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(QTPYVCP_DIR)

# globals
CONFIG = {}
OPTIONS = DotDict()
PLUGINS = OrderedDict()  # Ordered dict so can terminate in order initiated
DIALOGS = {}
WINDOWS = {}
SETTINGS = {}

# for backward compatibility
from qtpyvcp.app import run
def run_vcp(*args, **kwargs):
    run(*args, **kwargs)
