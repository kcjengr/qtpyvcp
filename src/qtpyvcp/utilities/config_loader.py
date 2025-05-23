import os
import sys

import hiyapyco

from jinja2.nativetypes import NativeEnvironment
from jinja2 import Environment, FileSystemLoader, Undefined, make_logging_undefined

from qtpyvcp.utilities.logger import getLogger, logLevelFromName
from qtpyvcp.utilities.yaml_filters import INIFilterModule

LOG = getLogger(__name__)

hiyapyco_logger = getLogger('qtpyvcp.config_loader.hiyapyco')
hiyapyco_logger.setLevel(os.getenv('HIYAPYCO_LOG_LEVEL', 'ERROR'))
hiyapyco.logger = hiyapyco_logger

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

    LOG.debug('Loading config files: {}'.format(files))

    # hiyapyco merges in order least important to most important
    files.reverse()

    expanded_files = process_templates(files)

    hiyapyco.jinja2env = NativeEnvironment(variable_start_string='(',
                                           variable_end_string=')',
                                           undefined=LogUndefined)
    

        
    cfg_dict = hiyapyco.load(expanded_files,
                             method=hiyapyco.METHOD_SUBSTITUTE,
                             interpolate=True,
                             failonmissingfiles=True)

    if LOG.getEffectiveLevel() == logLevelFromName("DEBUG"):
        LOG.debug("Merged YAML config:\n\n%s\n",
                  hiyapyco.dump(cfg_dict,
                                default_flow_style=False))

    return cfg_dict


def process_templates(files):
    env = Environment(loader=FileSystemLoader(searchpath=[os.path.dirname(config_file) for config_file in files]),
                      undefined=Undefined)
    
    filter_module = INIFilterModule()
    
    for name, func in filter_module.filters().items():
        print(f"Filter name: {name} func: {func}")
        env.filters[name] = func
    
    expanded_templates = []
    
    for config_file in files:
        if os.path.exists(config_file):
            
            file_dir, file_name = os.path.split(os.path.realpath(config_file))
            
            template = env.get_template(file_name)
            
            
            ini_data = env.filters["from-ini"]()

                        
            result = template.render({'file': {'path': config_file, 'dir': file_dir, 'name': file_name},
                                      'env': os.environ,
                                      'ini': ini_data})
            

            expanded_templates.append(result)
    
    return expanded_templates


def load_config_files_from_env():
    files = os.getenv('VCP_CONFIG_FILES', '').split(':')
    return load_config_files(*files)
