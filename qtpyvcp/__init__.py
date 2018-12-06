import os
from ruamel import yaml

QTPYVCP_DIR = os.path.abspath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(QTPYVCP_DIR)

__version__ = '0.0.1'


DEFAULT_CONFIG_FILE = os.path.join(QTPYVCP_DIR, 'default_config.yml')

# global config
CONFIG_DICT = {}


def _load_config_data(config_file):
    with open(config_file, "r") as fh:
        return yaml.load(fh, Loader=yaml.Loader)


def load_default_config():
    """Loads/Resets global config with default values."""
    global CONFIG_DICT
    CONFIG_DICT = _load_config_data(DEFAULT_CONFIG_FILE)


def load_vcp_config(config_file=None):
    """Update the global config with values from the file.

    Args:
        config_file (str) :
    """
    if config_file is None or not os.path.exists(config_file):
        print "ERROR - no such file"
        return

    new_cfg = _load_config_data(config_file)

    print new_cfg

    global CONFIG_DICT
    CONFIG_DICT.update(new_cfg)

    print yaml.dump(new_cfg, Dumper=yaml.RoundTripDumper)

def show_config(self):
    print yaml.dump(CONFIG_DICT, Dumper=yaml.RoundTripDumper)

load_default_config()

import json
print json.dumps(CONFIG_DICT, sort_keys=True, indent=4)
