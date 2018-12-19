import os
import sys
import hiyapyco
from jinja2.nativetypes import NativeEnvironment
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined, make_logging_undefined

from qtpyvcp import DEFAULT_CONFIG_FILE
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

LogUndefined = make_logging_undefined(logger=LOG, base=Undefined)

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

    # files.append(DEFAULT_CONFIG_FILE)
    LOG.debug('Loading config files: {}'.format(files))

    # hiyapyco merges in order least important to most important
    files.reverse()

    expanded_files = process_templates(files)

    hiyapyco.jinja2env = NativeEnvironment(variable_start_string='(',
                                           variable_end_string=')',
                                           undefined=LogUndefined)

    cfg_dict = hiyapyco.load(expanded_files,
                             method=hiyapyco.METHOD_MERGE,
                             interpolate=True,
                             failonmissingfiles=True)

    # import json
    # print json.dumps(cfg_dict, sort_keys=True, indent=4)

    return cfg_dict


def process_templates(files):
    env = Environment(loader=FileSystemLoader(searchpath=[os.path.dirname(file) for file in files]),
                      undefined=LogUndefined,
                      )

    expanded_templates = []
    for file in files:
        file_dir, file_name = os.path.split(file)
        template = env.get_template(file_name)
        result = template.render({'file': {'path': file, 'dir': file_dir, 'name': file_name},
                                  'env': os.environ,
                                  'ini': {'traj': {'coordinates': 'XYZ'},
                                          'machine': {'name': 'My Machine'},
                                          'display': {'cycle_time': 100},
                                          },
                                  })

        expanded_templates.append(result)

    return expanded_templates


def load_config_files_from_env():
    files = os.getenv('VCP_CONFIG_FILES', '').split(':')
    return load_config_files(*files)
