"""Qt Quick 3D implementation of the LinuxCNC backplot."""

__all__ = ["Qt3D0"]


def __getattr__(name):
    if name == "Qt3D0":
        from .qtquick3d_backplot import Qt3D0
        return Qt3D0
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
