#import sys;sys.path.append(r'/root/.p2/pool/plugins/org.python.pydev.core_7.5.0.202001101138/pysrc')
#import pydevd;pydevd.settrace()

import os

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
DIALOGS = {}
WINDOWS = {}
SETTINGS = {}

# for backward compatibility
from qtpyvcp.app import run
def run_vcp(*args, **kwargs):
    run(*args, **kwargs)
