from dataclasses import dataclass
import glob
import importlib.util
import os
from time import perf_counter
from typing import Any, Optional

import numpy as np
import vtk
from vtk.util import numpy_support

from qtpyvcp.utilities import logger


LOG = logger.getLogger(__name__)


@dataclass
class CppBackplotResult:
    path_actors: Any
    offset_transitions: Any
    added_segments: int
    draw_ms: float


def _load_native_module():
    try:
        from . import _backplot_cpp  # type: ignore
        return _backplot_cpp
    except Exception:
        pass

    module_dir = os.path.dirname(__file__)
    candidates = sorted(glob.glob(os.path.join(module_dir, "build", "_backplot_cpp*.so")))
    if not candidates:
        return None

    module_path = candidates[-1]
    spec = importlib.util.spec_from_file_location("qtpyvcp.native.backplot_cpp._backplot_cpp", module_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cpp_backplot_available() -> bool:
    return _load_native_module() is not None


def build_backplot_from_canon(canon, datasource, *, file_name: Optional[str] = None) -> Optional[CppBackplotResult]:
    module = _load_native_module()
    if module is None:
        return None

    bridge_start = perf_counter()
    try:
        payload = module.build_from_canon(canon, datasource)
    except NotImplementedError:
        LOG.info("C++ backplot bridge loaded but build_from_canon is not implemented yet")
        return None
    except Exception:
        LOG.exception("C++ backplot build failed; falling back to Python draw path")
        return None

    if not isinstance(payload, dict):
        LOG.warning("C++ backplot payload type unsupported (%s); falling back", type(payload))
        return None

    wcs_payload = payload.get("wcs_payload")
    if not isinstance(wcs_payload, (list, tuple)):
        LOG.warning("C++ backplot payload missing wcs_payload; falling back")
        return None

    path_actors = canon.get_path_actors()
    if not isinstance(path_actors, dict):
        LOG.warning("C++ backplot expected dict path_actors; falling back")
        return None

    for entry in wcs_payload:
        if not isinstance(entry, dict):
            continue

        wcs_index = entry.get("wcs_index")
        segment_count = int(entry.get("segment_count", 0))

        actor = path_actors.get(wcs_index)
        if actor is None:
            LOG.warning("C++ backplot actor missing for wcs=%s; falling back", wcs_index)
            return None

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

    canon.offset_transitions = payload.get("offset_transitions") or []
    canon.added_segments = int(payload.get("added_segments", 0))

    bridge_total_ms = (perf_counter() - bridge_start) * 1000.0

    result = CppBackplotResult(
        path_actors=path_actors,
        offset_transitions=canon.offset_transitions,
        added_segments=canon.added_segments,
        draw_ms=float(bridge_total_ms),
    )

    if result.path_actors is None:
        LOG.warning("C++ backplot returned no path_actors; falling back")
        return None

    if file_name:
        LOG.info(
            "[backplot-cpp] file=%s used_cpp=true geometry_ms=%.2f total_bridge_ms=%.2f",
            file_name,
            float(payload.get("draw_ms", 0.0)),
            result.draw_ms,
        )

    return result
