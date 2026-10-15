"""Display widgets package.

3D renderer modules are imported lazily so shared geometry and data helpers
remain available without loading renderer-specific Qt modules.
"""

import os as _os

__all__ = ["VTKBackPlot", "Qt3D0"]


def __getattr__(name):
    if name == "VTKBackPlot" and not _os.getenv('DESIGNER'):
        from .vtk_backplot.vtk_backplot import VTKBackPlot
        return VTKBackPlot
    if name == "Qt3D0":
        if _os.getenv('DESIGNER'):
            from .designer_plugins import Qt3D0
            return Qt3D0
        from .qtquick3d_backplot.qtquick3d_backplot import Qt3D0
        return Qt3D0
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + __all__)
