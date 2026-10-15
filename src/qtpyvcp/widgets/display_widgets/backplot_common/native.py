"""Native (C++) backplot geometry, returned as plain NumPy data.

The compiled ``_backplot_cpp`` extension already emits renderer-independent
arrays; the VTK bridge then wraps them in ``vtkPoints``/``vtkCellArray``.
This module keeps the raw arrays in :class:`BackplotGeometry` form so the Qt3D
backplot can consume them without importing VTK.
"""

import os
import shutil

import numpy as np
from PySide6.QtGui import QColor

from qtpyvcp.native.backplot_cpp.native_module import import_native_module
from qtpyvcp.utilities import logger

from .canon import DEFAULT_ROLE_COLORS
from .geometry import BackplotGeometry, OffsetTransition, PathGeometry

LOG = logger.getLogger(__name__)


def build_native_geometry(filename, datasource, *, path_colors, unitcode, initcode,
                          parameter_file, temp_parameter_file):
    """Load *filename* with the native canon and return ``BackplotGeometry``.

    Returns ``None`` when the native module is unavailable or the payload is
    unusable, so the caller can fall back to the Python canon.
    """
    try:
        native = import_native_module()
    except ImportError as ex:
        LOG.debug("native backplot module unavailable: %s", ex)
        return None

    try:
        canon = native.NativeCanon(_native_colors(path_colors))
    except Exception:
        LOG.exception("failed to construct native canon")
        return None

    try:
        machine_is_metric = bool(datasource.isMachineMetric())
        canon.set_external_length_units(1.0 if machine_is_metric else (1.0 / 25.4))
    except Exception:
        LOG.exception("failed to configure native external length units")

    try:
        axis_mask = int(datasource.getAxisMask())
        canon.set_axis_mask(axis_mask if axis_mask > 0 else 0x1FF)
    except Exception:
        pass

    parse_start = None
    try:
        from time import perf_counter

        import gcode  # heavy; only needed on the native path

        if os.path.exists(parameter_file):
            shutil.copy(parameter_file, temp_parameter_file)
        canon.parameter_file = temp_parameter_file

        parse_start = perf_counter()
        result, seq = gcode.parse(filename, canon, unitcode, initcode)
        if result > gcode.MIN_ERROR:
            LOG.warning("native parse error in %s line %s: %s",
                        filename, seq - 1, gcode.strerror(result))
            return None
        parse_ms = (perf_counter() - parse_start) * 1000.0

        payload = native.build_from_canon(canon, datasource)
        geometry = _payload_to_geometry(payload)
        if geometry is None:
            return None

        getter = getattr(canon, "get_floating_wcs", None)
        if callable(getter):
            try:
                geometry.floating_wcs = set(getter())
            except Exception:
                LOG.exception("native canon get_floating_wcs() failed")
        LOG.debug("[backplot-native] file=%s draw_ms=%.2f parse_ms=%.2f",
                  filename, float(payload.get("draw_ms", 0.0)), parse_ms)
        return geometry
    except Exception:
        LOG.exception("native canon parse/build failed")
        return None
    finally:
        for suffix in ("", ".bak"):
            try:
                os.unlink(temp_parameter_file + suffix)
            except OSError:
                pass


def _native_colors(colors):
    """Native canon calls ``QColor.getRgb()``; accept tuples or QColors."""
    source = dict(DEFAULT_ROLE_COLORS)
    if colors:
        source.update(colors)

    resolved = {}
    for role, rgba in source.items():
        if hasattr(rgba, 'getRgb'):
            resolved[role] = rgba
        else:
            r, g, b, a = (list(rgba) + [255])[:4]
            resolved[role] = QColor(int(r), int(g), int(b), int(a))
    return resolved


def _payload_to_geometry(payload):
    if not isinstance(payload, dict):
        return None
    wcs_payload = payload.get("wcs_payload")
    if not isinstance(wcs_payload, (list, tuple)):
        LOG.warning("native payload missing wcs_payload")
        return None

    geometry = BackplotGeometry(added_segments=int(payload.get("added_segments", 0) or 0))

    for entry in wcs_payload:
        if not isinstance(entry, dict):
            continue
        wcs_index = entry.get("wcs_index")
        segment_count = int(entry.get("segment_count", 0) or 0)

        points = np.asarray(entry.get("points"), dtype=np.float32)
        colors = np.asarray(entry.get("colors"), dtype=np.uint8)
        line_numbers_raw = entry.get("line_numbers")
        line_numbers = (np.asarray(line_numbers_raw, dtype=np.int32)
                        if line_numbers_raw is not None
                        else np.zeros((0,), dtype=np.int32))

        if points.ndim != 2 or points.shape[1] != 3:
            LOG.warning("native points shape invalid for wcs=%s", wcs_index)
            return None
        if colors.ndim != 2 or colors.shape[1] != 4:
            LOG.warning("native colors shape invalid for wcs=%s", wcs_index)
            return None
        if line_numbers.ndim != 1 or (segment_count and line_numbers.shape[0] != segment_count):
            line_numbers = np.zeros((0,), dtype=np.int32)

        geometry.paths[wcs_index] = PathGeometry(
            wcs_index=wcs_index,
            points=points,
            colors=colors,
            line_numbers=line_numbers,
        )

    for transition in payload.get("offset_transitions") or ():
        try:
            geometry.offset_transitions.append(OffsetTransition(
                from_wcs=transition["from_wcs"],
                to_wcs=transition["to_wcs"],
                from_end=transition["from_end"],
                to_start=transition["to_start"],
            ))
        except (KeyError, TypeError):
            continue

    return geometry
