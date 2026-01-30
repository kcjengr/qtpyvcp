# import sys;sys.path.append(r'~/.p2/pool/plugins/org.python.pydev.core_10.2.1.202307021217/pysrc')
# import pydevd; pydevd.settrace()

import os

from qtpyvcp.lib.types import DotDict

try:
    # Try to get version from package metadata (for installed packages)
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("qtpyvcp")
        # If version is placeholder (editable install), use git version
        if __version__ in ("0.0", "0.0.0"):
            raise PackageNotFoundError
    except PackageNotFoundError:
        # Fall back to dunamai for development installations
        try:
            from dunamai import Version
            git_version = Version.from_git()
            # Format to match poetry-dynamic-versioning: base+distance.gcommit
            if git_version.distance > 0:
                __version__ = f"{git_version.base}+{git_version.distance}.g{git_version.commit}"
            else:
                __version__ = git_version.base
        except Exception:
            __version__ = "0.0.0+unknown"
except ImportError:
    # Python < 3.8 fallback
    try:
        from dunamai import Version
        git_version = Version.from_git()
        if git_version.distance > 0:
            __version__ = f"{git_version.base}+{git_version.distance}.g{git_version.commit}"
        else:
            __version__ = git_version.base
    except Exception:
        __version__ = "0.0.0+unknown"

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
