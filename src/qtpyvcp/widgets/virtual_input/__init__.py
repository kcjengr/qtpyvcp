import sys

from . import qtpyvcp_rc as _virtual_input_qtpyvcp_rc

# Generated UI modules import `qtpyvcp_rc` as a top-level module name.
# Alias it to this package-local resource module so runtime loading works.
sys.modules.setdefault("qtpyvcp_rc", _virtual_input_qtpyvcp_rc)
