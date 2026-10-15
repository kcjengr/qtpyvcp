"""VTK backplot widget package.

The public widget (``VTKBackPlot``) pulls in VTK and a live render window, which
is heavy and unavailable in a plain headless/test context.  Submodules such as
``linuxcnc_datasource`` are renderer-independent and are imported directly by
the shared backplot layer, so the VTK widget is imported lazily via PEP 562
module ``__getattr__`` rather than eagerly here.
"""

__all__ = ["VTKBackPlot"]


def __getattr__(name):
    if name == "VTKBackPlot":
        from .vtk_backplot import VTKBackPlot
        return VTKBackPlot
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + __all__)
