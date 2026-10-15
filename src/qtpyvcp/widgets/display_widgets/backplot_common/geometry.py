"""Plain-data geometry containers shared by the VTK and Qt3D backplots.

Segment endpoints are stored the same way the native C++ builder and the
``VTKCanon`` already emit them: a flat ``(N, 3)`` float32 point array where
each *segment* occupies two consecutive rows (start, end).  ``colors`` is
``(N / 2, 4)`` uint8 with one RGBA entry per *segment* (matching the native
payload and VTK's per-cell scalars); renderers expand it per-vertex as needed.
``line_numbers`` carries one G-code sequence number per segment.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

EMPTY_POINTS = np.zeros((0, 3), dtype=np.float32)
EMPTY_COLORS = np.zeros((0, 4), dtype=np.uint8)
EMPTY_LINES = np.zeros((0,), dtype=np.int32)


@dataclass
class PathGeometry:
    """Geometry for the program path in one work coordinate system (WCS)."""

    wcs_index: int
    points: np.ndarray = field(default_factory=lambda: EMPTY_POINTS.copy())
    colors: np.ndarray = field(default_factory=lambda: EMPTY_COLORS.copy())
    line_numbers: np.ndarray = field(default_factory=lambda: EMPTY_LINES.copy())

    @property
    def segment_count(self) -> int:
        return int(self.points.shape[0]) // 2

    @property
    def is_empty(self) -> bool:
        return self.points.size == 0

    def bounds(self) -> tuple[float, float, float, float, float, float] | None:
        """Return ``(xmin, xmax, ymin, ymax, zmin, zmax)`` or ``None``."""
        if self.is_empty:
            return None
        pts = self.points
        return (
            float(pts[:, 0].min()), float(pts[:, 0].max()),
            float(pts[:, 1].min()), float(pts[:, 1].max()),
            float(pts[:, 2].min()), float(pts[:, 2].max()),
        )

    def segment(self, index: int) -> tuple[np.ndarray, np.ndarray] | None:
        """Return the ``(start, end)`` rows for segment *index*, or ``None``."""
        if index < 0 or index >= self.segment_count:
            return None
        base = index * 2
        return self.points[base], self.points[base + 1]


@dataclass
class OffsetTransition:
    """A link drawn between the end of one WCS path and the next."""

    from_wcs: int
    to_wcs: int
    from_end: Sequence[float]
    to_start: Sequence[float]


@dataclass
class BackplotGeometry:
    """All geometry produced by loading a single program."""

    paths: dict[int, PathGeometry] = field(default_factory=dict)
    offset_transitions: list[OffsetTransition] = field(default_factory=list)
    added_segments: int = 0
    # WCS indices whose path never established an absolute position (G91-only).
    floating_wcs: set[int] = field(default_factory=set)
    # Foam/jet vertical offsets ``(z, w)`` when the machine reports them.
    foam: tuple[float, float] = (0.0, 0.0)

    def bounds(self) -> tuple[float, float, float, float, float, float] | None:
        """Combined bounds across every WCS path, or ``None`` when empty."""
        boxes = [p.bounds() for p in self.paths.values() if not p.is_empty]
        boxes = [b for b in boxes if b is not None]
        if not boxes:
            return None
        arr = np.asarray(boxes, dtype=np.float64)
        return (
            float(arr[:, 0].min()), float(arr[:, 1].max()),
            float(arr[:, 2].min()), float(arr[:, 3].max()),
            float(arr[:, 4].min()), float(arr[:, 5].max()),
        )

    @property
    def has_paths(self) -> bool:
        return any(not p.is_empty for p in self.paths.values())
