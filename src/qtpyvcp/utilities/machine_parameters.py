"""Helpers for reading LinuxCNC RS274NGC parameter (.var) files."""

import os
from linuxcnc import ini

from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


def get_parameter_file_path():
    """Resolve the active RS274NGC parameter file path.

    Returns:
        str | None: Absolute path to the parameter file if resolvable.
    """
    ini_file = os.getenv("INI_FILE_NAME")
    config_dir = os.getenv("CONFIG_DIR")

    if not ini_file:
        return None

    if not config_dir:
        config_dir = os.path.dirname(ini_file)

    try:
        ini_obj = ini(ini_file)
        parameter_file = ini_obj.find("RS274NGC", "PARAMETER_FILE") or "linuxcnc.var"
    except Exception:
        LOG.exception("Failed to read RS274NGC parameter file from INI")
        return None

    if not os.path.isabs(parameter_file):
        parameter_file = os.path.join(config_dir, parameter_file)

    return os.path.realpath(parameter_file)


def read_parameter_values(parameter_file=None):
    """Read numeric parameters from a LinuxCNC .var file.

    Args:
        parameter_file (str | None): Optional explicit .var path.

    Returns:
        dict: Mapping of parameter number (int) to value (float).
    """
    parameter_file = parameter_file or get_parameter_file_path()
    if not parameter_file or not os.path.exists(parameter_file):
        return {}

    values = {}
    try:
        with open(parameter_file, "r") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith((";", "#")):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                try:
                    param = int(parts[0])
                    value = float(parts[1])
                except ValueError:
                    continue

                values[param] = value
    except Exception:
        LOG.exception("Failed reading parameter values from '%s'", parameter_file)

    return values


def get_parameter_value(values, number, default=0.0):
    """Read a single parameter from a parsed values mapping.

    Args:
        values (dict): Mapping returned by :func:`read_parameter_values`.
        number (int | str): Parameter number.
        default (object): Value returned when parameter is missing/invalid.

    Returns:
        object: Parameter value or default.
    """
    try:
        number = int(number)
    except (TypeError, ValueError):
        return default

    return values.get(number, default)
