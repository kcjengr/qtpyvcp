from dataclasses import dataclass
import glob
import importlib
import importlib.util
import os
import shutil
import sysconfig
from time import perf_counter
from typing import Any, Optional

import gcode
import numpy as np
import vtk
from vtk.util import numpy_support

from qtpyvcp.utilities import logger


LOG = logger.getLogger(__name__)


def _import_native_module():
    module_dir = os.path.dirname(__file__)
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    candidates = [
        os.path.join(module_dir, f"_backplot_cpp{ext_suffix}"),
        os.path.join(module_dir, "build", f"_backplot_cpp{ext_suffix}"),
    ]

    # Accept extension variations (e.g. abi-tagged .so names) from both locations.
    candidates.extend(sorted(glob.glob(os.path.join(module_dir, "_backplot_cpp*.so")), reverse=True))
    candidates.extend(sorted(glob.glob(os.path.join(module_dir, "build", "_backplot_cpp*.so")), reverse=True))

    # Prefer newest build output so development rebuilds are picked up
    # without needing a manual copy into package root.
    existing_candidates = [p for p in candidates if os.path.exists(p)]
    existing_candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    seen = set()
    import_errors = []
    for module_path in existing_candidates:
        if module_path in seen:
            continue
        seen.add(module_path)

        try:
            spec = importlib.util.spec_from_file_location("qtpyvcp.native.backplot_cpp._backplot_cpp", module_path)
            if spec is None or spec.loader is None:
                import_errors.append(f"failed to create import spec for {module_path}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            LOG.debug("[backplot-cpp] loaded native module: %s", module_path)
            return module
        except Exception as ex:
            import_errors.append(f"{module_path}: {ex}")

    # Fall back to standard import as a last resort.
    try:
        module = importlib.import_module("qtpyvcp.native.backplot_cpp._backplot_cpp")
        LOG.debug("[backplot-cpp] loaded native module via importlib: %s", getattr(module, "__file__", "<unknown>"))
        return module
    except Exception as ex:
        import_errors.append(f"importlib: {ex}")

    searched = [
        os.path.join(module_dir, "_backplot_cpp*.so"),
        os.path.join(module_dir, "build", "_backplot_cpp*.so"),
    ]
    hint = "Run `qnative --backplot` (or package install hooks) to build the native module."
    details = f"; import attempts: {' | '.join(import_errors)}" if import_errors else ""
    raise ImportError(f"missing C++ backplot module; searched: {searched}. {hint}{details}")


_backplot_cpp = _import_native_module()


@dataclass
class CppBackplotResult:
    path_actors: Any
    offset_transitions: Any
    added_segments: int
    draw_ms: float
    parse_ms: float = 0.0


def _payload_to_result(payload: Any, datasource, *, file_name: Optional[str], path_actors: Optional[dict] = None, parse_ms: float = 0.0) -> Optional[CppBackplotResult]:
    if not isinstance(payload, dict):
        LOG.warning("C++ backplot payload type unsupported (%s); falling back", type(payload))
        return None

    wcs_payload = payload.get("wcs_payload")
    if not isinstance(wcs_payload, (list, tuple)):
        LOG.warning("C++ backplot payload missing wcs_payload; falling back")
        return None

    if path_actors is None:
        path_actors = {}

    from qtpyvcp.widgets.display_widgets.vtk_backplot.path_actor import PathActor

    for entry in wcs_payload:
        if not isinstance(entry, dict):
            continue

        wcs_index = entry.get("wcs_index")
        segment_count = int(entry.get("segment_count", 0))

        actor = path_actors.get(wcs_index)
        if actor is None:
            actor = PathActor(datasource)
            path_actors[wcs_index] = actor

        points_np = np.asarray(entry.get("points"), dtype=np.float64)
        colors_np = np.asarray(entry.get("colors"), dtype=np.uint8)

        if points_np.ndim != 2 or points_np.shape[1] != 3:
            LOG.warning("C++ backplot points payload shape invalid for wcs=%s; falling back", wcs_index)
            return None
        if colors_np.ndim != 2 or colors_np.shape[1] != 4:
            LOG.warning("C++ backplot colors payload shape invalid for wcs=%s; falling back", wcs_index)
            return None

        vtk_points_data = numpy_support.numpy_to_vtk(points_np, deep=True)
        actor.points = vtk.vtkPoints()
        actor.points.SetData(vtk_points_data)

        connectivity = np.empty((segment_count, 3), dtype=np.int64)
        if segment_count > 0:
            connectivity[:, 0] = 2
            start_indices = np.arange(0, segment_count * 2, 2, dtype=np.int64)
            connectivity[:, 1] = start_indices
            connectivity[:, 2] = start_indices + 1

        vtk_ids = numpy_support.numpy_to_vtkIdTypeArray(connectivity.ravel(), deep=True)
        actor.lines = vtk.vtkCellArray()
        actor.lines.SetCells(segment_count, vtk_ids)

        vtk_colors = numpy_support.numpy_to_vtk(
            num_array=colors_np,
            deep=True,
            array_type=vtk.VTK_UNSIGNED_CHAR,
        )
        vtk_colors.SetNumberOfComponents(4)
        actor.colors = vtk_colors

        actor.poly_data.SetPoints(actor.points)
        actor.poly_data.SetLines(actor.lines)
        actor.poly_data.GetCellData().SetScalars(actor.colors)
        actor.data_mapper.SetInputData(actor.poly_data)
        actor.data_mapper.Update()
        actor.SetMapper(actor.data_mapper)

    result = CppBackplotResult(
        path_actors=path_actors,
        offset_transitions=payload.get("offset_transitions") or [],
        added_segments=int(payload.get("added_segments", 0)),
        draw_ms=float(payload.get("draw_ms", 0.0) or 0.0),
        parse_ms=float(parse_ms),
    )

    if result.path_actors is None:
        LOG.warning("C++ backplot returned no path_actors; falling back")
        return None

    if file_name:
        LOG.debug(
            "[backplot-cpp] file=%s used_cpp=true geometry_ms=%.2f total_bridge_ms=%.2f",
            file_name,
            float(payload.get("draw_ms", 0.0)),
            result.draw_ms,
        )

    return result


def build_backplot_from_file(
    filename: str,
    datasource,
    *,
    path_colors,
    unitcode: str,
    initcode: str,
    parameter_file: str,
    temp_parameter_file: str,
) -> Optional[CppBackplotResult]:
    canon = _backplot_cpp.NativeCanon(path_colors)
    try:
        machine_is_metric = bool(datasource.isMachineMetric())
        external_length_units = 1.0 if machine_is_metric else (1.0 / 25.4)
        canon.set_external_length_units(external_length_units)
        LOG.debug(
            "[backplot-cpp] canon external units: machine_is_metric=%s external_length_units=%.12f",
            machine_is_metric,
            external_length_units,
        )
    except Exception:
        LOG.exception("Failed to configure native canon external length units")

    try:
        axis_mask = int(datasource.getAxisMask())
        if axis_mask <= 0:
            axis_mask = 0x1FF
    except Exception:
        axis_mask = 0x1FF
    try:
        canon.set_axis_mask(axis_mask)
    except Exception:
        pass

    parse_start = perf_counter()
    try:
        if os.path.exists(parameter_file):
            shutil.copy(parameter_file, temp_parameter_file)

        canon.parameter_file = temp_parameter_file
        result, seq = gcode.parse(filename, canon, unitcode, initcode)
        if result > gcode.MIN_ERROR:
            msg = gcode.strerror(result)
            LOG.warning("C++ native canon parse error in %s line %s: %s", filename, seq - 1, msg)
            return None

        # Keep parse_ms scoped to parser execution only.
        parse_ms = (perf_counter() - parse_start) * 1000.0

        payload = _backplot_cpp.build_from_canon(canon, datasource)
        cpp_result = _payload_to_result(payload, datasource, file_name=filename, parse_ms=parse_ms)
        return cpp_result
    except Exception:
        LOG.exception("C++ native canon parse/build failed")
        return None
    finally:
        try:
            os.unlink(temp_parameter_file)
        except Exception:
            pass
        try:
            os.unlink(temp_parameter_file + '.bak')
        except Exception:
            pass
