import os
import configparser
from pprint import pprint

def from_ini():
    ini_file = os.getenv("INI_FILE_NAME")
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