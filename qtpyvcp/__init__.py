from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# for backward compatibility
from qtpyvcp.app import run
def run_vcp(*args, **kwargs):
    run(*args, **kwargs)
