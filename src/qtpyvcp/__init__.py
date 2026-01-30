# import sys;sys.path.append(r'~/.p2/pool/plugins/org.python.pydev.core_10.2.1.202307021217/pysrc')
# import pydevd; pydevd.settrace()

import os

from qtpyvcp.lib.types import DotDict

try:
    # Try to get version from package metadata (for installed packages)
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("qtpyvcp")
    except PackageNotFoundError:
        # Fall back to versioneer for development installations
        from . import _version
        __version__ = _version.get_versions()['version']
except ImportError:
    # Python < 3.8 fallback
    try:
        from . import _version
        __version__ = _version.get_versions()['version']
    except:
        __version__ = "unknown"

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
