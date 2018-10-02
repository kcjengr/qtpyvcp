import os
import sys
from QtPyVCP.utilities.opt_parser import parse_opts

VCP_DIR = os.path.abspath(os.path.dirname(__file__))
UI_FILE = os.path.join(VCP_DIR, 'mini.ui')

__version__ = '0.0.1'

# Main entry point
def main():
    opts = parse_opts(vcp_name='Mini', vcp_cmd='mini', vcp_version=__version__)
    # parse_opts sets up the environment, so we must import the app after
    from QtPyVCP.application import VCPApplication
    app = VCPApplication(opts=opts, vcp_file=UI_FILE)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
