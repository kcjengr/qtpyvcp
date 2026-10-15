"""Camera helpers for the Qt3D backplot.

Reproduces the VTK backplot's view presets (isometric ``P``, ``X``/``Y``/``Z``,
lathe ``XZ``/``XZ2``/``Z2``) and provides fit-to-bounds for both orthographic
and perspective projections.
"""

import math

from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtGui import QQuaternion, QVector3D
from shiboken6 import isValid

UP_Z = (0.0, 0.0, 1.0)
NATURAL_VIEW_UP = QVector3D(0.0, 0.0, 1.0)

# camera direction (unit vector from the focus point toward the eye) and up
# vector, keyed by view preset name.
VIEW_DIRECTIONS = {
    'P':   ((1.0, -1.0, 1.0), UP_Z),
    'X':   ((0.0, -1.0, 0.0), UP_Z),
    'Y':   ((1.0, 0.0, 0.0), UP_Z),
    'Z':   ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    'Z2':  ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    'XZ':  ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    'XZ2': ((0.0, -1.0, 0.0), (-1.0, 0.0, 0.0)),
    'M':   ((1.0, -1.0, 1.0), UP_Z),
}


def _components(vec):
    """Return ``(x, y, z)`` for a tuple/list or a ``QVector3D``."""
    if hasattr(vec, 'x'):
        return float(vec.x()), float(vec.y()), float(vec.z())
    return float(vec[0]), float(vec[1]), float(vec[2])


def _normalized(vec):
    x, y, z = _components(vec)
    length = math.sqrt(x * x + y * y + z * z) or 1.0
    return (x / length, y / length, z / length)


class CameraRig:
    """Wraps a ``Qt3DRender.QCamera`` with backplot-aware helpers."""

    def __init__(self, camera):
        self.camera = camera
        self._orthographic = False
        self._fov = 30.0
        if camera is not None:
            camera.setFieldOfView(self._fov)
            camera.setUpVector(QVector3D(*UP_Z))
            camera.setViewCenter(QVector3D(0.0, 0.0, 0.0))
            camera.setPosition(QVector3D(100.0, -100.0, 100.0))
        self.set_perspective()

    def _alive(self):
        """True while the wrapped QCamera C++ object still exists."""
        return self.camera is not None and isValid(self.camera)

    # -- projection ---------------------------------------------------------

    def set_perspective(self):
        self._orthographic = False
        if self._alive():
            self.camera.setProjectionType(Qt3DRender.QCameraLens.PerspectiveProjection)

    def set_orthographic(self):
        self._orthographic = True
        if self._alive():
            self.camera.setProjectionType(Qt3DRender.QCameraLens.OrthographicProjection)

    @property
    def is_orthographic(self):
        return self._orthographic

    # -- poses --------------------------------------------------------------

    def look_at(self, center, direction, up=None, distance=None):
        """Point the camera at *center* from *direction* (unit-ish vector)."""
        if not self._alive():
            return
        d = _normalized(direction)
        center = QVector3D(float(center[0]), float(center[1]), float(center[2]))

        if distance is None:
            distance = max(1.0, self._current_distance())

        position = QVector3D(
            center.x() + d[0] * distance,
            center.y() + d[1] * distance,
            center.z() + d[2] * distance,
        )
        self.camera.setViewCenter(center)
        self.camera.setPosition(position)
        if up is not None:
            self.camera.setUpVector(QVector3D(float(up[0]), float(up[1]), float(up[2])))

    def _current_distance(self):
        if not self._alive():
            return 100.0
        try:
            return (self.camera.position() - self.camera.viewCenter()).length()
        except (AttributeError, RuntimeError):
            return 100.0

    def set_view(self, name, center, distance=None):
        key = str(name or 'P').upper()
        direction, up = VIEW_DIRECTIONS.get(key, VIEW_DIRECTIONS['P'])
        self.look_at(center, direction, up, distance)

    # -- fitting ------------------------------------------------------------

    def fit_bounds(self, bounds, aspect=1.0, padding=1.1, distance=None):
        """Frame *bounds* ``(xmin,xmax,ymin,ymax,zmin,zmax)``."""
        if bounds is None or not self._alive():
            return
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        center = ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0, (zmin + zmax) / 2.0)
        diagonal = math.sqrt((xmax - xmin) ** 2 + (ymax - ymin) ** 2 + (zmax - zmin) ** 2)

        if self._orthographic:
            half = max(xmax - xmin, ymax - ymin, zmax - zmin) * 0.5 * padding
            half = max(half, 1.0)
            self.camera.setProjectionType(Qt3DRender.QCameraLens.OrthographicProjection)
            self.camera.setTop(half)
            self.camera.setBottom(-half)
            self.camera.setLeft(-half * max(aspect, 1e-6))
            self.camera.setRight(half * max(aspect, 1e-6))
            if distance is None:
                distance = diagonal * 2.0 or 100.0
        else:
            if distance is None:
                half_fov = math.radians(self._fov) * 0.5
                distance = (diagonal * 0.5) / max(math.sin(half_fov), 1e-6) * padding
                distance = max(distance, 1.0)

        direction = _normalized(self.camera.position() - self.camera.viewCenter()) \
            if self._current_distance() > 1e-6 else (1.0, -1.0, 1.0)
        self.look_at(center, direction, distance=distance)
        self.camera.setNearPlane(max(0.01, distance - diagonal))
        self.camera.setFarPlane(distance + diagonal * 4.0 + 100.0)

    def zoom(self, factor):
        """Scale the eye distance by *factor* (values > 1 zoom out)."""
        if not self._alive():
            return
        center = self.camera.viewCenter()
        offset = self.camera.position() - center
        self.camera.setPosition(center + offset * float(factor))
        self._refresh_clip_planes()

    # -- interaction (mirrors the VTK backplot's style) ---------------------

    def orbit(self, azimuth_deg, elevation_deg):
        """Azimuth around world Z, then elevation around the camera right axis.

        The up vector is re-orthogonalized against the view direction after
        each step (VTK's ``OrthogonalizeViewUp``); without it the horizon
        slowly rolls and the view stops behaving like the VTK backplot.
        """
        if not self._alive():
            return
        center = self.camera.viewCenter()
        position = self.camera.position()
        up = self.camera.upVector()

        offset = position - center
        if offset.lengthSquared() < 1e-12:
            return

        if abs(azimuth_deg) > 1e-9:
            quat = QQuaternion.fromAxisAndAngle(NATURAL_VIEW_UP, float(azimuth_deg))
            offset = quat.rotatedVector(offset)
            up = quat.rotatedVector(up)

        forward = (-offset).normalized()
        up = self._orthogonalize(up, forward)

        if abs(elevation_deg) > 1e-9:
            right = QVector3D.crossProduct(forward, up)
            if right.lengthSquared() > 1e-12:
                quat = QQuaternion.fromAxisAndAngle(right.normalized(),
                                                    float(elevation_deg))
                offset = quat.rotatedVector(offset)
                up = quat.rotatedVector(up)
                forward = (-offset).normalized()
                up = self._orthogonalize(up, forward)

        self.camera.setPosition(center + offset)
        self.camera.setUpVector(up.normalized())
        self.camera.setViewCenter(center)
        self._refresh_clip_planes()

    @staticmethod
    def _orthogonalize(up, forward):
        """Project *up* perpendicular to *forward*, keeping a stable fallback."""
        projected = up - forward * QVector3D.dotProduct(up, forward)
        if projected.lengthSquared() < 1e-10:
            projected = QVector3D(0.0, 0.0, 1.0) \
                - forward * QVector3D.dotProduct(QVector3D(0.0, 0.0, 1.0), forward)
        if projected.lengthSquared() < 1e-10:
            return up
        return projected.normalized()

    def pan(self, dx_pixels, dy_pixels, viewport_width, viewport_height):
        """Translate position and view center so the scene follows the cursor."""
        if not self._alive():
            return
        # Pixels are assumed square, so the horizontal and vertical world
        # scales are the same; only the viewport height is needed.
        height = max(float(viewport_height), 1.0)

        center = self.camera.viewCenter()
        position = self.camera.position()
        forward = (center - position)
        distance = forward.length()
        if distance < 1e-9:
            return
        forward = forward / distance

        up = self.camera.upVector()
        right = QVector3D.crossProduct(forward, up)
        if right.lengthSquared() < 1e-12:
            right = QVector3D(1.0, 0.0, 0.0)
        right = right.normalized()
        true_up = QVector3D.crossProduct(right, forward).normalized()

        if self._orthographic:
            world_height = abs(self.camera.top() - self.camera.bottom())
        else:
            world_height = 2.0 * distance * math.tan(math.radians(self._fov) * 0.5)

        units_per_pixel_y = world_height / height
        units_per_pixel_x = units_per_pixel_y

        delta = right * (-float(dx_pixels) * units_per_pixel_x) \
            + true_up * (float(dy_pixels) * units_per_pixel_y)
        self.camera.setPosition(position + delta)
        self.camera.setViewCenter(center + delta)

    def dolly(self, factor):
        """VTK-compatible dolly: ``factor > 1`` zooms in."""
        factor = float(factor)
        if factor <= 0.0 or not self._alive():
            return
        if self._orthographic:
            self.camera.setTop(self.camera.top() / factor)
            self.camera.setBottom(self.camera.bottom() / factor)
            self.camera.setLeft(self.camera.left() / factor)
            self.camera.setRight(self.camera.right() / factor)
        else:
            center = self.camera.viewCenter()
            offset = self.camera.position() - center
            self.camera.setPosition(center + offset / factor)
        self._refresh_clip_planes()

    def _refresh_clip_planes(self):
        if not self._alive():
            return
        distance = self._current_distance()
        if distance <= 0.0:
            return
        self.camera.setNearPlane(max(0.01, distance * 0.001))
        self.camera.setFarPlane(max(1000.0, distance * 100.0))
