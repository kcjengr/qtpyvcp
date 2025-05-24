import os
import configparser
from pprint import pprint

def from_ini():
    ini_file = os.getenv("INI_FILE_NAME", False)
    if not ini_file:
        return {'traj': {'coordinates': 'XYZ'},
                'machine': {'name': 'My Machine'},
                'display': {'cycle_time': 100},
                }
        
    config = configparser.ConfigParser(strict=False)
    config.read(ini_file)
    result = {}
    for section in config.sections():
        result[section] = dict(config.items(section))
    
    # pprint(result)
    
    return result

class INIFilterModule(object):
    def filters(self):
        return {
            'from-ini': from_ini
        }