"""Program -> :class:`BackplotGeometry` loading, shared by both backplots.

Uses the native C++ canon when available (fast, does not require VTK) and
falls back to the pure-Python :class:`BackplotCanon`.  Foam/jet machines and
any table-rotary case the native builder cannot shape are routed to Python.
"""

import os
import shutil

from qtpyvcp.utilities import logger

from .canon import BackplotCanon
from .geometry import BackplotGeometry
from .native import build_native_geometry

LOG = logger.getLogger(__name__)


def load_geometry(filename, datasource, *, colors=None, prefer_native=True,
                   cpp_ok=True) -> BackplotGeometry | None:
    """Parse *filename* and return its geometry, or ``None`` on failure.

    Parameters
    ----------
    filename:
        Path to the G-code file.
    datasource:
        A ``LinuxCncDataSource``-compatible object.
    colors:
        Optional mapping of motion role -> colour accepted by ``BackplotCanon``.
    prefer_native:
        Try the native builder first when *cpp_ok* is also true.
    cpp_ok:
        Caller's machine-level veto (e.g. table-rotary machines want the
        Python canon so rotary shaping happens at load time).
    """
    if datasource is None or not filename or not os.path.isfile(filename):
        return None

    unitcode = _unitcode(datasource)
    initcode = _startup_code(datasource)

    parameter_file = _parameter_file(datasource)
    temp_parameter_file = parameter_file + '.temp'

    use_native = prefer_native and cpp_ok and not datasource.isMachineFoam()

    if use_native:
        geometry = build_native_geometry(
            filename,
            datasource,
            path_colors=colors or {},
            unitcode=unitcode,
            initcode=initcode,
            parameter_file=parameter_file,
            temp_parameter_file=temp_parameter_file,
        )
        if geometry is not None:
            return geometry
        LOG.info("native backplot unavailable; using Python canon for %s", filename)

    return _load_with_python_canon(filename, datasource, colors, parameter_file,
                                   temp_parameter_file, unitcode, initcode)


def _load_with_python_canon(filename, datasource, colors, parameter_file,
                            temp_parameter_file, unitcode, initcode):
    import gcode

    stat = getattr(getattr(datasource, "_status", None), "stat", None)
    try:
        canon = BackplotCanon(datasource, colors=colors, stat=stat)
    except Exception:
        LOG.exception("Python canon construction failed for %s", filename)
        return None

    if os.path.exists(parameter_file):
        shutil.copy(parameter_file, temp_parameter_file)
    canon.parameter_file = temp_parameter_file

    try:
        result, seq = gcode.parse(filename, canon, unitcode, initcode)
        if result > gcode.MIN_ERROR:
            LOG.warning("Python canon parse error in %s line %s: %s",
                        filename, seq - 1, gcode.strerror(result))
            return None
        return canon.build_geometry()
    except KeyboardInterrupt:
        # Raised by an "(AXIS, stop)" comment to abort plot generation.
        return None
    except Exception:
        LOG.exception("Python canon parse failed for %s", filename)
        return None
    finally:
        for suffix in ("", ".bak"):
            try:
                os.unlink(temp_parameter_file + suffix)
            except OSError:
                pass


def _ini(datasource):
    return getattr(datasource, "_inifile", None)


def _unitcode(datasource):
    """Mirror ``BaseBackPlot``: G20 for inch machines, G21 for metric."""
    ini = _ini(datasource)
    stat = getattr(getattr(datasource, "_status", None), "stat", None)
    linear_units = getattr(stat, "linear_units", None)
    if linear_units is None and ini is not None:
        raw = ini.find("TRAJ", "LINEAR_UNITS")
        # LinuxCNC stat.linear_units is 1.0 for metric and 1/25.4 for inch.
        # Keep the INI fallback in that same convention.
        linear_units = (1.0 / 25.4
                        if str(raw or "").strip().lower().startswith("inch")
                        else 1.0)
    if linear_units is None:
        linear_units = 1.0 if datasource.isMachineMetric() else (1.0 / 25.4)
    return "G%d" % (20 + (linear_units == 1))


def _startup_code(datasource):
    ini = _ini(datasource)
    if ini is None:
        return ""
    return ini.find("RS274NGC", "RS274NGC_STARTUP_CODE") or ""


def _parameter_file(datasource):
    config_dir = getattr(datasource, "config_dir", None)
    ini = _ini(datasource)
    name = None
    if ini is not None:
        name = ini.find("RS274NGC", "PARAMETER_FILE")

    if config_dir:
        return os.path.join(config_dir, name or "linuxcnc.var")

    ini_file = os.getenv("INI_FILE_NAME") or ""
    return os.path.join(os.path.dirname(ini_file) or ".", name or "linuxcnc.var")
