"""Renderer-independent backplot data layer.

This package turns a G-code program plus LinuxCNC machine state into plain
geometry (NumPy arrays and small dataclasses) with no rendering dependency.
The Qt Quick 3D backplot consumes this layer, so coordinate handling,
work-offset math, and rotary/kinematics shaping live in exactly one place.
"""

from .canon import DEFAULT_ROLE_COLORS, BackplotCanon
from .geometry import BackplotGeometry, OffsetTransition, PathGeometry

__all__ = [
    "DEFAULT_ROLE_COLORS",
    "BackplotCanon",
    "BackplotGeometry",
    "OffsetTransition",
    "PathGeometry",
    "load_geometry",
]


def load_geometry(*args, **kwargs):
    """Lazy re-export so importing the package does not pull in ``gcode``."""
    from .loader import load_geometry as _load_geometry

    return _load_geometry(*args, **kwargs)
