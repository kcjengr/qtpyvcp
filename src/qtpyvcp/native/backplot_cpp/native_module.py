"""Locate and import the compiled ``_backplot_cpp`` extension.

Kept free of any VTK import so renderer-independent callers (e.g. the Qt3D
backplot) can use the native geometry builder without pulling in VTK.
"""

import glob
import importlib
import importlib.util
import os
import sysconfig

from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)


def import_native_module():
    """Import the newest ``_backplot_cpp`` extension module.

    Searches the package directory and its ``build`` output, preferring the
    most recently modified candidate so development rebuilds are picked up
    without copying files around.
    """
    module_dir = os.path.dirname(__file__)
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    candidates = [
        os.path.join(module_dir, f"_backplot_cpp{ext_suffix}"),
        os.path.join(module_dir, "build", f"_backplot_cpp{ext_suffix}"),
    ]
    candidates.extend(sorted(glob.glob(os.path.join(module_dir, "_backplot_cpp*.so")), reverse=True))
    candidates.extend(sorted(glob.glob(os.path.join(module_dir, "build", "_backplot_cpp*.so")), reverse=True))

    existing = sorted({p for p in candidates if os.path.exists(p)},
                      key=lambda p: os.path.getmtime(p), reverse=True)

    import_errors = []
    for module_path in existing:
        try:
            spec = importlib.util.spec_from_file_location(
                "qtpyvcp.native.backplot_cpp._backplot_cpp", module_path)
            if spec is None or spec.loader is None:
                import_errors.append(f"failed to create import spec for {module_path}")
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            LOG.debug("[backplot-cpp] loaded native module: %s", module_path)
            return module
        except Exception as ex:  # noqa: BLE001 - report all, keep searching
            import_errors.append(f"{module_path}: {ex}")

    try:
        module = importlib.import_module("qtpyvcp.native.backplot_cpp._backplot_cpp")
        LOG.debug("[backplot-cpp] loaded native module via importlib: %s",
                  getattr(module, "__file__", "<unknown>"))
        return module
    except Exception as ex:  # noqa: BLE001
        import_errors.append(f"importlib: {ex}")

    hint = "Run `qnative --backplot` (or package install hooks) to build the native module."
    details = f"; import attempts: {' | '.join(import_errors)}" if import_errors else ""
    raise ImportError(f"missing C++ backplot module. {hint}{details}")
