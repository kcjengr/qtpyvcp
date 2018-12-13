import os
import sys
import hiyapyco
from qtpyvcp import DEFAULT_CONFIG_FILE

from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

def load_config_files(*files):
    """Load and merge YAML config files.

    Files that come earlier in the list take precedence over files
    that come later in the list.

    Args:
        *files (list) : Variable number of file paths.

    Example::

        load_config_files(file1, file2, file3, ...):
    """

    files = [file for file in files if file is not None and file != '']

    for file in files:
        sys.path.insert(0, os.path.dirname(file))

    files.append(DEFAULT_CONFIG_FILE)
    LOG.debug('Loading config files: {}'.format(files))

    # hiyapyco merges in order least important to most important
    files.reverse()

    expanded_files = [expand_vars(file) for file in files]

    cfg_dict = hiyapyco.load(expanded_files,
                             method=hiyapyco.METHOD_MERGE,
                             interpolate=True,
                             failonmissingfiles=True)

    # import json
    # print json.dumps(cfg_dict, sort_keys=True, indent=4)

    return cfg_dict


def expand_vars(fname):

    file_dir = os.path.dirname(os.path.abspath(fname))

    # Read in the file
    with open(fname, 'r') as fh:
        filedata = fh.read()

    # Replace the target string
    filedata = filedata.replace('$YAML_DIR$', file_dir)

    return filedata


def load_config_files_from_env():
    files = os.getenv('VCP_CONFIG_FILES', '').split(':')
    return load_config_files(*files)

