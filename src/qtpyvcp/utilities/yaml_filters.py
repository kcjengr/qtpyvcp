import os
import configparser


DEFAULT_INI_DATA = {
    'traj': {'coordinates': 'XYZ'},
    'machine': {'name': 'My Machine'},
    'display': {'cycle_time': 100},
}


def _read_ini_config():
    ini_file = os.getenv("INI_FILE_NAME", False)
    if not ini_file:
        return None

    config = configparser.ConfigParser(strict=False)
    config.read(ini_file)
    return config

def from_ini():
    config = _read_ini_config()
    if config is None:
        return DEFAULT_INI_DATA

    result = {}
    for section in config.sections():
        result[section] = dict(config.items(section))

    return result


def ini_value(section, key, default=None):
    config = _read_ini_config()
    if config is None:
        section_data = DEFAULT_INI_DATA.get(str(section).lower(), {})
        return section_data.get(str(key).lower(), default)

    section_name = str(section)
    key_name = str(key)

    if not config.has_section(section_name):
        section_name_lower = section_name.lower()
        section_name_upper = section_name.upper()

        if config.has_section(section_name_lower):
            section_name = section_name_lower
        elif config.has_section(section_name_upper):
            section_name = section_name_upper
        else:
            return default

    return config.get(section_name, key_name, fallback=default)

class INIFilterModule(object):
    def filters(self):
        return {
            'from-ini': from_ini
        }