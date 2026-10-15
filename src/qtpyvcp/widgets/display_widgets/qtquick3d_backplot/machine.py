"""Machine-part assembly for the Qt Quick 3D backplot.

Builds a flat list of parts from the same ``MACHINE_PARTS`` YAML the VTK
backplot consumes.  Part geometry is exposed to QML through a list model (one
``Model`` per row via ``Repeater3D``); because QML has no parent/child for the
repeater rows, the nested YAML hierarchy is composed into a world transform per
part in Python.  Rotary joints are re-composed from live joint feedback.
"""

import math
import os
import struct

import numpy as np
from PySide6.QtCore import QAbstractListModel, QByteArray, Qt
from PySide6.QtGui import QColor, QQuaternion, QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry

try:
    from qtpyvcp.utilities import logger
    LOG = logger.getLogger(__name__)
except ImportError:  # standalone import (e.g. unit tests without QtPyVCP init)
    import logging
    LOG = logging.getLogger(__name__)

_AXIS_VECTOR = {
    "A": np.array((1.0, 0.0, 0.0)),
    "B": np.array((0.0, 1.0, 0.0)),
    "C": np.array((0.0, 0.0, 1.0)),
}


def _vec3(value, default=(0.0, 0.0, 0.0)):
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return float(value[0]), float(value[1]), float(value[2])
        except (TypeError, ValueError):
            return default
    return default


def _rgba(value):
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        color = [float(c) for c in value[:3]]
        if max(color) > 1.0:
            color = [c / 255.0 for c in color]
        alpha = float(value[3]) if len(value) > 3 else 1.0
        if alpha > 1.0:
            alpha /= 255.0
        return QColor.fromRgbF(color[0], color[1], color[2], alpha).name()
    return "#e6e6e6"


def _euler_matrix(rx, ry, rz):
    rx, ry, rz = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    mx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    my = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    mz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return mz @ my @ mx


def _axis_matrix(axis, angle_deg):
    axis = _AXIS_VECTOR.get(axis, _AXIS_VECTOR["C"])
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    x, y, z = axis
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) * c + s * cross + (1 - c) * np.outer(axis, axis)


def read_stl_triangles(path):
    """Return ``(N, 3, 3)`` triangle vertices from an STL file, or ``None``."""
    try:
        with open(path, "rb") as handle:
            header = handle.read(84)
            if len(header) < 84:
                return _read_ascii_stl(path)
            count = struct.unpack("<I", header[80:84])[0]
            if os.path.getsize(path) == 84 + count * 50:
                records = np.dtype([("normal", "<3f4"), ("vertices", "<9f"), ("attr", "<u2")])
                data = np.frombuffer(handle.read(count * 50), dtype=records, count=count)
                return data["vertices"].reshape(count, 3, 3).astype(np.float64)
        return _read_ascii_stl(path)
    except OSError:
        LOG.exception("failed reading STL %s", path)
        return None


def _read_ascii_stl(path):
    vertices = []
    with open(path, "r", errors="ignore") as handle:
        for line in handle:
            parts = line.strip().split()
            if parts and parts[0] == "vertex" and len(parts) >= 4:
                vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
    if not vertices or len(vertices) % 3 != 0:
        return None
    return np.asarray(vertices, dtype=np.float64).reshape(-1, 3, 3)


def _stl_geometry(path):
    triangles = read_stl_triangles(path)
    if triangles is None or len(triangles) == 0:
        return None
    vertices = np.ascontiguousarray(
        triangles.reshape(-1, 3).astype(np.float32))
    geometry = QQuick3DGeometry()
    geometry.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)
    geometry.setStride(3 * np.dtype(np.float32).itemsize)
    geometry.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0,
                          QQuick3DGeometry.Attribute.F32Type)
    geometry.setVertexData(vertices.tobytes())
    minimum = vertices.min(axis=0)
    maximum = vertices.max(axis=0)
    geometry.setBounds(QVector3D(*map(float, minimum)), QVector3D(*map(float, maximum)))
    geometry.update()
    return geometry


class _Part:
    __slots__ = (
        "axis",
        "color",
        "euler",
        "geometry",
        "joint",
        "parent",
        "pivot",
        "position",
        "source_url",
        "visible",
        "world",
    )

    def __init__(self):
        self.geometry = None
        self.source_url = ""
        self.color = "#e6e6e6"
        self.position = (0.0, 0.0, 0.0)
        self.euler = (0.0, 0.0, 0.0)
        self.axis = ""
        self.joint = None
        self.pivot = None
        self.parent = None
        self.world = np.eye(4)
        self.visible = True


class MachinePartsModel(QAbstractListModel):
    """Flat list model of machine parts for a QML ``Repeater3D``."""

    GeometryRole = Qt.ItemDataRole.UserRole + 1
    SourceUrlRole = Qt.ItemDataRole.UserRole + 2
    PosRole = Qt.ItemDataRole.UserRole + 3
    RotRole = Qt.ItemDataRole.UserRole + 4
    ColorRole = Qt.ItemDataRole.UserRole + 5
    VisibleRole = Qt.ItemDataRole.UserRole + 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parts = []
        self._joint_values = None
        self._enabled = True

    # -- model interface ---------------------------------------------------

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return len(self._parts)

    def roleNames(self):
        return {
            self.GeometryRole: QByteArray(b"geometry"),
            self.SourceUrlRole: QByteArray(b"sourceUrl"),
            self.PosRole: QByteArray(b"pos"),
            self.RotRole: QByteArray(b"rot"),
            self.ColorRole: QByteArray(b"col"),
            self.VisibleRole: QByteArray(b"vis"),
        }

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self._parts)):
            return None
        part = self._parts[index.row()]
        if role == self.GeometryRole:
            return part.geometry
        if role == self.SourceUrlRole:
            return part.source_url
        if role == self.PosRole:
            return QVector3D(*map(float, part.world[:3, 3]))
        if role == self.RotRole:
            return self._world_quaternion(part.world)
        if role == self.ColorRole:
            return part.color
        if role == self.VisibleRole:
            return bool(part.visible and self._enabled)
        return None

    @staticmethod
    def _world_quaternion(matrix):
        m = matrix[:3, :3]
        trace = m[0, 0] + m[1, 1] + m[2, 2]
        if trace > 0.0:
            s = math.sqrt(trace + 1.0) * 2.0
            w = 0.25 * s
            x = (m[2, 1] - m[1, 2]) / s
            y = (m[0, 2] - m[2, 0]) / s
            z = (m[1, 0] - m[0, 1]) / s
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
            w = (m[2, 1] - m[1, 2]) / s
            x = 0.25 * s
            y = (m[0, 1] + m[1, 0]) / s
            z = (m[0, 2] + m[2, 0]) / s
        elif m[1, 1] > m[2, 2]:
            s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
            w = (m[0, 2] - m[2, 0]) / s
            x = (m[0, 1] + m[1, 0]) / s
            y = 0.25 * s
            z = (m[1, 2] + m[2, 1]) / s
        else:
            s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
            w = (m[1, 0] - m[0, 1]) / s
            x = (m[0, 2] + m[2, 0]) / s
            y = (m[1, 2] + m[2, 1]) / s
            z = 0.25 * s
        return QQuaternion(float(w), float(x), float(y), float(z)).normalized()

    # -- loading -----------------------------------------------------------

    def load(self, data, config_dir=None):
        """(Re)build the parts from ``MACHINE_PARTS`` *data* (a parsed mapping)."""
        self.beginResetModel()
        self._parts = []
        if isinstance(data, dict):
            self._walk(data, None, config_dir)
        self._recompute()
        self.endResetModel()
        LOG.debug("Quick 3D machine assembly built with %d parts", len(self._parts))

    def _walk(self, node, parent, config_dir):
        for value in node.values():
            if not isinstance(value, dict):
                continue
            part = self._make_part(value, parent, config_dir)
            self._parts.append(part)
            self._walk(value, part, config_dir)

    def _make_part(self, data, parent, config_dir):
        part = _Part()
        part.parent = parent
        position = data.get("position")
        if isinstance(position, (list, tuple)):
            part.position = _vec3(position)
            if len(position) >= 6:
                part.euler = (float(position[3]), float(position[4]), float(position[5]))
        part.color = _rgba(data.get("color"))
        part.axis = str(data.get("axis") or "").upper()
        part.joint = data.get("joint")
        origin = data.get("origin")
        if isinstance(origin, (list, tuple)) and len(origin) >= 3:
            part.pivot = _vec3(origin)

        model_path = data.get("model")
        if model_path:
            resolved = self._resolve(model_path, config_dir)
            lower = str(model_path).lower()
            if lower.endswith(".stl"):
                part.geometry = _stl_geometry(resolved)
                if part.geometry is None:
                    LOG.warning("Quick 3D machine STL unavailable: %s", resolved)
            else:
                # glTF/GLB: let Qt Quick 3D load the asset URL (best effort).
                from PySide6.QtCore import QUrl
                part.source_url = QUrl.fromLocalFile(resolved).toString()
        return part

    @staticmethod
    def _resolve(path, config_dir):
        text = str(path)
        if os.path.isabs(text) or not config_dir:
            return text
        return os.path.normpath(os.path.join(config_dir, text))

    # -- animation / visibility -------------------------------------------

    def apply_joint_values(self, joint_values):
        if not joint_values:
            return
        self._joint_values = joint_values
        if not self._parts:
            return
        self._recompute()
        top = self.index(0, 0)
        bottom = self.index(len(self._parts) - 1, 0)
        self.dataChanged.emit(top, bottom)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        if not self._parts:
            return
        top = self.index(0, 0)
        bottom = self.index(len(self._parts) - 1, 0)
        self.dataChanged.emit(top, bottom)

    def _recompute(self):
        for part in self._parts:
            angle = None
            if part.axis in _AXIS_VECTOR and part.joint is not None:
                try:
                    angle = float(self._joint_values[int(part.joint)])
                except (IndexError, TypeError, ValueError):
                    angle = None
            local = self._local_matrix(part, angle)
            parent = part.parent.world if part.parent is not None else np.eye(4)
            part.world = parent @ local

    @staticmethod
    def _local_matrix(part, joint_angle):
        matrix = np.eye(4)
        matrix[:3, :3] = _euler_matrix(*part.euler)
        matrix[:3, 3] = part.position
        if joint_angle is not None and part.pivot is not None:
            pivot = np.asarray(part.pivot, dtype=float)
            rotate = np.eye(4)
            rotate[:3, :3] = _axis_matrix(part.axis, joint_angle)
            pre = np.eye(4)
            pre[:3, 3] = pivot
            post = np.eye(4)
            post[:3, 3] = -pivot
            matrix = pre @ rotate @ post @ matrix
        return matrix
