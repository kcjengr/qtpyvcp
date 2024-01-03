# import sys;sys.path.append(r'~/.p2/pool/plugins/org.python.pydev.core_10.2.1.202307021217/pysrc')
# import pydevd; pydevd.settrace()

import os

from qtpyvcp.lib.types import DotDict

from . import _version
__version__ = _version.get_versions()['version']

QTPYVCP_DIR = os.path.abspath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(QTPYVCP_DIR)

DEFAULT_CONFIG_FILE = os.path.join(QTPYVCP_DIR, 'yaml_lib/default_config.yml')

# globals
CONFIG = {}
OPTIONS = DotDict()
DIALOGS = {}
WINDOWS = {}
SETTINGS = {}

# for backward compatibility
from qtpyvcp.app import run
def run_vcp(*args, **kwargs):
    run(*args, **kwargs)
