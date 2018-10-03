# Main entry point
import os
import sys
from QtPyVCP.utilities.opt_parser import parse_opts

__version__ = '0.0.1'

opts = parse_opts(vcp_name='Mini', vcp_cmd='mini', vcp_version=__version__)

# parse_opts sets up the environment, so we must import the app after
from mini import MiniVCP
from QtPyVCP.application import VCPApplication
app = VCPApplication(opts=opts)

app.window = MiniVCP(opts=opts)
app.window.show()

sys.exit(app.exec_())
