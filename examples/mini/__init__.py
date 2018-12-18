
__version__ = '0.0.1'

import os

VCP_DIR = os.path.realpath(os.path.dirname(__file__))
VCP_CONFIG_FILE = os.path.join(VCP_DIR, 'mini.yml')


def run(opts):
    os.environ['VCP_CONFIG_FILES'] = VCP_CONFIG_FILE + ':' + os.environ.get(
        'VCP_CONFIG_FILES', '')

    from qtpyvcp.utilities.config_loader import load_config_files_from_env
    config = load_config_files_from_env()

    from qtpyvcp.vcp_launcher import launch_application
    launch_application(opts, config)
