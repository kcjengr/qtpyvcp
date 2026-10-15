"""Display widgets package.

The VTK backplot pulls in VTK and a live render window.  It is imported
lazily so renderer-independent submodules (e.g. ``backplot_common``) can be
imported without constructing a VTK context.
"""

import os as _os

__all__ = ["VTKBackPlot"]


def __getattr__(name):
    if name == "VTKBackPlot" and not _os.getenv('DESIGNER'):
        from .vtk_backplot.vtk_backplot import VTKBackPlot
        return VTKBackPlot
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + __all__)
