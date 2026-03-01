import os
import configparser
import subprocess


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


def _detect_system_theme(default='light'):
    fallback = str(default).lower() if default else 'light'

    env_override = os.getenv('QTPYVCP_SYSTEM_THEME')
    if env_override:
        normalized = str(env_override).strip().lower()
        if normalized in ('light', 'dark'):
            return normalized

    xdg_theme = os.getenv('XDG_CURRENT_THEME', '')
    if 'dark' in xdg_theme.lower():
        return 'dark'

    try:
        proc = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
        )
        output = (proc.stdout or '').strip().lower()
        if 'dark' in output:
            return 'dark'
        if 'light' in output or 'default' in output:
            return 'light'
    except Exception:
        pass

    try:
        proc = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
        )
        output = (proc.stdout or '').strip().lower()
        if 'dark' in output:
            return 'dark'
    except Exception:
        pass

    kde_globals = os.path.expanduser('~/.config/kdeglobals')
    if os.path.exists(kde_globals):
        try:
            with open(kde_globals, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('ColorScheme=') and 'dark' in line.lower():
                        return 'dark'
        except Exception:
            pass

    return 'dark' if fallback == 'dark' else 'light'


def effective_theme_color(section, key, default='light'):
    fallback = str(default).lower() if default else 'light'
    raw_value = ini_value(section, key, fallback)
    normalized = str(raw_value).strip().lower() if raw_value is not None else fallback

    if normalized in ('light', 'dark'):
        return normalized
    if normalized == 'system':
        return _detect_system_theme(default=fallback)
    return fallback

class INIFilterModule(object):
    def filters(self):
        return {
            'from-ini': from_ini,
            'ini-value': ini_value,
            'effective-theme-color': effective_theme_color,
        }