"""Per-(WCS, motion-role) path groups for the Qt Quick 3D backplot.

The shared backplot layer produces geometry in *WCS-local* machine coordinates:
a work offset is not baked into the vertex arrays.  Each row of
:class:`PathGroupModel` is one WCS/role pair whose line geometry stays in that
local frame; the work offset (or floating-path anchor) is applied as a scene
transform on the QML ``Model``.  Moving a work offset therefore only emits
``dataChanged`` for the transform roles -- it never re-uploads vertex buffers or
re-parses the program.

Picking is done against the same local arrays: the click ray is transformed into
each row's local frame, so no world-space copy of every segment is kept.
"""

import math
from dataclasses import dataclass, field

import numpy as np
from PySide6.QtCore import QAbstractListModel, QByteArray, Qt
from PySide6.QtGui import QColor, QQuaternion, QVector3D

from .geometry import LineGeometry, map_points_to_quick3d, map_vector_to_quick3d

ROLE_NAMES = ("traverse", "arcfeed", "feed", "dwell", "user")

# Qt Quick 3D is Y-up; a CNC rotation about +Z is a rotation about +Y.
_SCENE_UP = QVector3D(0.0, 1.0, 0.0)


def segment_role_indices(colors, palette):
    """Map each segment RGBA colour to a role index in *palette*.

    Exact palette matches are preferred so a distinct feed/arcfeed colour is
    never confused with a neighbour. Unmatched colours fall back to the nearest
    palette entry using 64-bit math, because ``255 ** 2`` overflows ``int16``
    and silently selects the wrong role.
    """
    colors = np.asarray(colors, dtype=np.int64).reshape(-1, 4)
    palette = np.asarray(palette, dtype=np.int64).reshape(-1, 4)
    if colors.shape[0] == 0 or palette.shape[0] == 0:
        return np.zeros(colors.shape[0], dtype=np.int64)

    exact = (colors[:, None, :] == palette[None, :, :]).all(axis=2)
    indices = exact.argmax(axis=1)
    unmatched = ~exact.any(axis=1)
    if unmatched.any():
        distances = np.square(
            colors[unmatched, None, :] - palette[None, :, :]).sum(axis=2)
        indices[unmatched] = distances.argmin(axis=1)
    return indices


def transform_point(point, x, y, z, rotation_deg):
    """Apply a WCS placement to a CNC-local point."""
    px, py, pz = (float(value) for value in point[:3])
    if rotation_deg:
        radians = math.radians(rotation_deg)
        cosine, sine = math.cos(radians), math.sin(radians)
        px, py = cosine * px - sine * py, sine * px + cosine * py
    return (px + float(x), py + float(y), pz + float(z))


def ray_segment_distances(origin, direction, starts, ends):
    """Return ``(distance, ray_t)`` from a ray to each line segment.

    *origin* and *direction* are in the same frame as *starts*/*ends*;
    *direction* must be a unit vector.  ``ray_t`` is the distance along the ray
    (negative values are clamped to zero) and is used to prefer the segment
    nearest the viewer when several lines sit under the cursor.
    """
    origin = np.asarray(origin, dtype=np.float64).reshape(3)
    direction = np.asarray(direction, dtype=np.float64).reshape(3)
    starts = np.asarray(starts, dtype=np.float64).reshape(-1, 3)
    ends = np.asarray(ends, dtype=np.float64).reshape(-1, 3)
    if starts.shape[0] == 0:
        return np.zeros((0,)), np.zeros((0,))

    ab = ends - starts
    w0 = origin - starts

    # Ray parameter t (a == 1 because direction is unit length).
    b = (ab * direction).sum(axis=1)
    c = np.maximum((ab * ab).sum(axis=1), 1e-12)
    d = (direction * w0).sum(axis=1)
    e = (ab * w0).sum(axis=1)

    denom = c - b * b
    degenerate = np.abs(denom) < 1e-12
    safe = np.where(degenerate, 1.0, denom)
    s = np.clip((e - b * d) / safe, 0.0, 1.0)
    s = np.where(degenerate, 0.0, s)

    t = s * b - d
    behind = t < 0.0
    if behind.any():
        # Closest point on the segment to the ray origin.
        s_behind = np.clip(e / c, 0.0, 1.0)
        s = np.where(behind, s_behind, s)
        t = np.where(behind, 0.0, t)

    closest_segment = starts + s[:, None] * ab
    closest_ray = origin + t[:, None] * direction
    distance = np.linalg.norm(closest_segment - closest_ray, axis=1)
    return distance, t


@dataclass
class PathRow:
    """One WCS/role group: local segment endpoints plus a scene transform."""

    wcs_index: int
    role: str
    geometry: LineGeometry
    starts: np.ndarray
    ends: np.ndarray
    line_numbers: np.ndarray
    color: str
    local_low: np.ndarray = field(default_factory=lambda: np.zeros(3))
    local_high: np.ndarray = field(default_factory=lambda: np.zeros(3))
    position: QVector3D = field(default_factory=QVector3D)
    rotation: QQuaternion = field(default_factory=QQuaternion)
    _tx: float = 0.0
    _ty: float = 0.0
    _tz: float = 0.0
    _theta: float = 0.0

    def apply_transform(self, x, y, z, rotation_deg):
        """Set the WCS placement; returns True when anything changed."""
        x, y, z = float(x), float(y), float(z)
        rotation_deg = float(rotation_deg)
        if (x == self._tx and y == self._ty and z == self._tz
                and rotation_deg == self._theta):
            return False
        self._tx, self._ty, self._tz = x, y, z
        self._theta = rotation_deg
        self.position = map_vector_to_quick3d((x, y, z))
        self.rotation = QQuaternion.fromAxisAndAngle(_SCENE_UP, rotation_deg)
        return True

    # -- coordinate conversion --------------------------------------------

    def world_point(self, point):
        """CNC-local point -> CNC world point."""
        return transform_point(point, self._tx, self._ty, self._tz, self._theta)

    def local_point(self, point):
        """CNC world point -> CNC-local point (inverse of :meth:`world_point`)."""
        dx = float(point[0]) - self._tx
        dy = float(point[1]) - self._ty
        if self._theta:
            radians = math.radians(self._theta)
            cosine, sine = math.cos(radians), math.sin(radians)
            dx, dy = cosine * dx + sine * dy, -sine * dx + cosine * dy
        return (dx, dy, float(point[2]) - self._tz)

    def world_points(self, points):
        """Transform an ``(N, 3)`` array of CNC-local points to world space."""
        points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
        if points.shape[0] == 0:
            return points
        if self._theta:
            radians = math.radians(self._theta)
            cosine, sine = math.cos(radians), math.sin(radians)
            x = cosine * points[:, 0] - sine * points[:, 1]
            y = sine * points[:, 0] + cosine * points[:, 1]
            points = np.column_stack((x, y, points[:, 2]))
        offset = np.asarray((self._tx, self._ty, self._tz), dtype=np.float64)
        return points + offset

    def world_segments(self):
        """Return ``(starts, ends)`` in CNC world coordinates."""
        return self.world_points(self.starts), self.world_points(self.ends)

    def world_bounds(self):
        """Axis-aligned world bounds of this row, or ``None``."""
        low, high = self.local_low, self.local_high
        corners = np.asarray([
            (x, y, z)
            for x in (low[0], high[0])
            for y in (low[1], high[1])
            for z in (low[2], high[2])
        ], dtype=np.float64)
        if self._theta:
            radians = math.radians(self._theta)
            cosine, sine = math.cos(radians), math.sin(radians)
            x = cosine * corners[:, 0] - sine * corners[:, 1]
            y = sine * corners[:, 0] + cosine * corners[:, 1]
            corners = np.column_stack((x, y, corners[:, 2]))
        corners = corners + np.asarray((self._tx, self._ty, self._tz))
        return corners.min(axis=0), corners.max(axis=0)


class PathGroupModel(QAbstractListModel):
    """QML list model with one line ``Model`` per WCS/role group."""

    GeometryRole = Qt.ItemDataRole.UserRole + 1
    ColorRole = Qt.ItemDataRole.UserRole + 2
    PosRole = Qt.ItemDataRole.UserRole + 3
    RotRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []

    # -- model interface ---------------------------------------------------

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return len(self._rows)

    def roleNames(self):
        return {
            self.GeometryRole: QByteArray(b"geometry"),
            self.ColorRole: QByteArray(b"col"),
            self.PosRole: QByteArray(b"pos"),
            self.RotRole: QByteArray(b"rot"),
        }

    def data(self, index, role):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        if role == self.GeometryRole:
            return row.geometry
        if role == self.ColorRole:
            return row.color
        if role == self.PosRole:
            return row.position
        if role == self.RotRole:
            return row.rotation
        return None

    # -- construction ------------------------------------------------------

    def clear(self):
        self.beginResetModel()
        self._rows = []
        self.endResetModel()

    def build(self, geometry, role_colors, transform_for_wcs):
        """Rebuild the rows from *geometry*.

        *role_colors* maps role -> CSS colour string; *transform_for_wcs* maps a
        WCS index to ``(x, y, z, rotation_degrees)`` in machine units.
        """
        rows = []
        transforms = {}

        def transform(wcs_index):
            if wcs_index not in transforms:
                transforms[wcs_index] = transform_for_wcs(wcs_index)
            return transforms[wcs_index]

        if geometry is not None:
            palette = np.asarray(
                [QColor(role_colors[role]).getRgb() for role in ROLE_NAMES],
                dtype=np.int64)
            for wcs_index, path in geometry.paths.items():
                if path.is_empty:
                    continue
                segment_points = np.asarray(
                    path.points, dtype=np.float32).reshape(-1, 2, 3)
                segment_count = segment_points.shape[0]
                if segment_count == 0:
                    continue

                colors = np.asarray(path.colors, dtype=np.int64).reshape(-1, 4)
                if colors.shape[0] != segment_count:
                    colors = np.tile(palette[2], (segment_count, 1))
                role_indices = segment_role_indices(colors, palette)

                line_numbers = np.asarray(path.line_numbers, dtype=np.int64)
                if line_numbers.shape[0] != segment_count:
                    line_numbers = np.full(segment_count, -1, dtype=np.int64)

                for role_index, role in enumerate(ROLE_NAMES):
                    mask = role_indices == role_index
                    if not mask.any():
                        continue
                    selected = segment_points[mask]
                    endpoints = selected.reshape(-1, 3)
                    line_geometry = LineGeometry()
                    line_geometry.replace(map_points_to_quick3d(endpoints))
                    starts = np.ascontiguousarray(selected[:, 0, :])
                    ends = np.ascontiguousarray(selected[:, 1, :])
                    low = np.minimum(starts.min(axis=0), ends.min(axis=0))
                    high = np.maximum(starts.max(axis=0), ends.max(axis=0))
                    row = PathRow(
                        wcs_index=int(wcs_index),
                        role=role,
                        geometry=line_geometry,
                        starts=starts,
                        ends=ends,
                        line_numbers=line_numbers[mask],
                        color=role_colors[role],
                        local_low=low.astype(np.float64),
                        local_high=high.astype(np.float64),
                    )
                    row.apply_transform(*transform(wcs_index))
                    rows.append(row)

        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    # -- updates -----------------------------------------------------------

    def update_transforms(self, transform_for_wcs):
        """Re-apply WCS placement; returns True when a row moved."""
        changed = False
        transforms = {}
        for row in self._rows:
            transform = transforms.get(row.wcs_index)
            if transform is None:
                transform = transform_for_wcs(row.wcs_index)
                transforms[row.wcs_index] = transform
            if row.apply_transform(*transform):
                changed = True
        if changed and self._rows:
            self.dataChanged.emit(self.index(0, 0),
                                  self.index(len(self._rows) - 1, 0),
                                  [self.PosRole, self.RotRole])
        return changed

    def set_colors(self, role_colors):
        """Update the per-role material colours without touching geometry."""
        changed = False
        for row in self._rows:
            color = role_colors.get(row.role)
            if color is not None and color != row.color:
                row.color = color
                changed = True
        if changed and self._rows:
            self.dataChanged.emit(self.index(0, 0),
                                  self.index(len(self._rows) - 1, 0),
                                  [self.ColorRole])

    def refresh(self):
        """Notify views that row transforms/colours changed in place."""
        if self._rows:
            self.dataChanged.emit(
                self.index(0, 0), self.index(len(self._rows) - 1, 0))

    # -- queries -----------------------------------------------------------

    def rows(self):
        return tuple(self._rows)

    def world_bounds(self):
        low = high = None
        for row in self._rows:
            bounds = row.world_bounds()
            if bounds is None:
                continue
            row_low, row_high = bounds
            low = row_low if low is None else np.minimum(low, row_low)
            high = row_high if high is None else np.maximum(high, row_high)
        if low is None:
            return None
        return (
            float(low[0]), float(high[0]),
            float(low[1]), float(high[1]),
            float(low[2]), float(high[2]),
        )

    def segments_for_lines(self, lines):
        """Return ``(starts, ends)`` in world coordinates for *lines*."""
        wanted = np.asarray([int(value) for value in lines if int(value) >= 0],
                            dtype=np.int64)
        if wanted.size == 0:
            return np.zeros((0, 3)), np.zeros((0, 3))
        starts, ends = [], []
        for row in self._rows:
            if row.line_numbers.size == 0:
                continue
            indices = np.nonzero(np.isin(row.line_numbers, wanted))[0]
            if indices.size == 0:
                continue
            starts.append(row.world_points(row.starts[indices]))
            ends.append(row.world_points(row.ends[indices]))
        if not starts:
            return np.zeros((0, 3)), np.zeros((0, 3))
        return np.concatenate(starts, axis=0), np.concatenate(ends, axis=0)
