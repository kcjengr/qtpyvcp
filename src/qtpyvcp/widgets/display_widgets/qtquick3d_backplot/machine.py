"""Machine-part assembly for the Qt Quick 3D backplot.

Builds a flat list of parts from the ``MACHINE_PARTS`` YAML.  Part geometry is exposed to QML through a list model (one
``Model`` per row via ``Repeater3D``); because QML has no parent/child for the
repeater rows, the nested YAML hierarchy is composed into a world transform per
part in Python.  Rotary joints are re-composed from live joint feedback.
"""

import base64
import json
import math
import os
import struct
from urllib.parse import unquote

import numpy as np
from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt
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

# CNC is Z-up; Qt Quick 3D's scene is Y-up. Paths/tool/grid are mapped with
# ``map_vector_to_quick3d`` (x, y, z) -> (x, z, -y); the machine parts use the
# same change of basis so the arm aligns with them and Z points up.
_CNC_TO_SCENE = np.array([[1.0, 0.0, 0.0],
                          [0.0, 0.0, 1.0],
                          [0.0, -1.0, 0.0]])
_SCENE_FROM_CNC = np.eye(4)
_SCENE_FROM_CNC[:3, :3] = _CNC_TO_SCENE
_CNC_FROM_SCENE = np.eye(4)
_CNC_FROM_SCENE[:3, :3] = _CNC_TO_SCENE.T


def _world_to_scene(world):
    """Change a CNC (Z-up) world matrix to the Y-up scene frame."""
    return _SCENE_FROM_CNC @ world @ _CNC_FROM_SCENE


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


def _geometry_from_arrays(vertices, indices=None, normals=None):
    """Build a triangle ``QQuick3DGeometry`` from vertex/index arrays.

    When *normals* are supplied they are interleaved with the positions so the
    part can be lit (``PrincipledMaterial`` fragment lighting).
    """
    vertices = np.ascontiguousarray(vertices.reshape(-1, 3).astype(np.float32))
    if vertices.size == 0:
        return None
    geometry = QQuick3DGeometry()
    geometry.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)
    if normals is not None and len(normals) == len(vertices):
        normals = np.ascontiguousarray(normals.reshape(-1, 3).astype(np.float32))
        interleaved = np.ascontiguousarray(
            np.concatenate([vertices, normals], axis=1))
        geometry.setStride(6 * np.dtype(np.float32).itemsize)
        geometry.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0,
                              QQuick3DGeometry.Attribute.F32Type)
        geometry.addAttribute(QQuick3DGeometry.Attribute.NormalSemantic, 12,
                              QQuick3DGeometry.Attribute.F32Type)
        geometry.setVertexData(interleaved.tobytes())
    else:
        geometry.setStride(3 * np.dtype(np.float32).itemsize)
        geometry.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0,
                              QQuick3DGeometry.Attribute.F32Type)
        geometry.setVertexData(vertices.tobytes())
    if indices is not None and len(indices):
        index_array = np.ascontiguousarray(indices.reshape(-1).astype(np.uint32))
        geometry.setIndexData(index_array.tobytes())
        geometry.addAttribute(QQuick3DGeometry.Attribute.IndexSemantic, 0,
                              QQuick3DGeometry.Attribute.U32Type)
    minimum = vertices.min(axis=0)
    maximum = vertices.max(axis=0)
    geometry.setBounds(QVector3D(*map(float, minimum)), QVector3D(*map(float, maximum)))
    geometry.update()
    return geometry


def _flat_normals(triangles):
    """Per-face normals repeated for each triangle vertex (STL)."""
    edge1 = triangles[:, 1] - triangles[:, 0]
    edge2 = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(edge1, edge2)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0.0] = 1.0
    return np.repeat(normals / lengths, 3, axis=0)


def _smooth_normals(vertices, indices):
    """Area-weighted vertex normals from an indexed triangle mesh."""
    triangles = np.asarray(indices, dtype=np.int64).reshape(-1, 3)
    p0, p1, p2 = vertices[triangles[:, 0]], vertices[triangles[:, 1]], vertices[triangles[:, 2]]
    face = np.cross(p1 - p0, p2 - p0)
    normals = np.zeros_like(vertices, dtype=np.float64)
    for corner in range(3):
        np.add.at(normals, triangles[:, corner], face)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0.0] = 1.0
    return (normals / lengths).astype(np.float32)


def _stl_geometry(path):
    triangles = read_stl_triangles(path)
    if triangles is None or len(triangles) == 0:
        return None
    return _geometry_from_arrays(triangles.reshape(-1, 3),
                                 normals=_flat_normals(triangles))


# -- glTF / GLB loading ----------------------------------------------------
#
# Qt Quick 3D resolves ``Model.source`` only to ``.mesh`` (or built-ins) at
# runtime, so ``.glb``/``.gltf`` from the Blender addon are parsed here into a
# ``QQuick3DGeometry``.  Positions and indices of the default scene are read;
# node world transforms are baked in and normals are left out (the parts render
# unlit).

_COMPONENT_DTYPE = {5120: "i1", 5121: "u1", 5122: "i2", 5123: "u2",
                    5125: "u4", 5126: "f4"}
_TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _read_gltf_document(path):
    """Return ``(document, {buffer_index: bytes})`` for a .glb or .gltf file."""
    with open(path, "rb") as handle:
        data = handle.read()

    if data[:4] == b"glTF":
        length = struct.unpack("<I", data[8:12])[0]
        offset, document, buffers = 12, None, {}
        while offset < length:
            chunk_len, chunk_type = struct.unpack("<II", data[offset:offset + 8])
            chunk = data[offset + 8:offset + 8 + chunk_len]
            if chunk_type == 0x4E4F534A:      # 'JSON'
                document = json.loads(chunk)
            elif chunk_type == 0x004E4942:    # 'BIN'
                buffers[0] = chunk
            offset += 8 + chunk_len
        return document, buffers

    document = json.loads(data)
    base_dir = os.path.dirname(path)
    buffers = {}
    for index, buffer in enumerate(document.get("buffers", [])):
        uri = buffer.get("uri")
        if not uri:
            buffers[index] = b""
        elif uri.startswith("data:"):
            buffers[index] = base64.b64decode(uri.split(",", 1)[1])
        else:
            with open(os.path.join(base_dir, unquote(uri)), "rb") as handle:
                buffers[index] = handle.read()
    return document, buffers


def _read_accessor(document, buffers, index):
    accessor = document["accessors"][index]
    count = accessor["count"]
    components = _TYPE_COUNT[accessor["type"]]
    dtype = np.dtype(_COMPONENT_DTYPE[accessor["componentType"]])
    view = document["bufferViews"][accessor["bufferView"]]
    raw = buffers[view.get("buffer", 0)]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    item_size = dtype.itemsize * components
    stride = view.get("byteStride") or item_size
    if stride == item_size:
        flat = np.frombuffer(raw, dtype=dtype, count=count * components, offset=start)
        return flat.reshape(count, components)
    end = start + (count - 1) * stride + item_size
    block = np.frombuffer(raw, dtype=np.uint8)[start:end].reshape(count, stride)
    return block[:, :item_size].copy().view(dtype).reshape(count, components)


def _node_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T
    matrix = np.eye(4)
    translation = node.get("translation", (0.0, 0.0, 0.0))
    rotation = node.get("rotation", (0.0, 0.0, 0.0, 1.0))  # x, y, z, w
    scale = node.get("scale", (1.0, 1.0, 1.0))
    x, y, z, w = rotation
    rot = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    matrix[:3, :3] = rot * np.asarray(scale, dtype=float)
    matrix[:3, 3] = translation
    return matrix


def _iter_mesh_nodes(document):
    nodes = document.get("nodes", [])
    if not nodes:
        return
    scene_index = document.get("scene", 0)
    scenes = document.get("scenes", [])
    roots = scenes[scene_index].get("nodes") if scene_index < len(scenes) else None
    if not roots:
        roots = list(range(len(nodes)))

    stack = [(root, np.eye(4)) for root in roots]
    while stack:
        index, parent = stack.pop()
        node = nodes[index]
        world = parent @ _node_matrix(node)
        if "mesh" in node:
            yield world, node["mesh"]
        for child in node.get("children", []):
            stack.append((child, world))


def _gltf_geometry(path):
    document, buffers = _read_gltf_document(path)
    if not document:
        return None

    positions, indices, base = [], [], 0
    for world, mesh_index in _iter_mesh_nodes(document):
        for primitive in document["meshes"][mesh_index].get("primitives", []):
            if primitive.get("mode", 4) != 4 or "POSITION" not in primitive.get("attributes", {}):
                continue
            vertices = _read_accessor(
                document, buffers, primitive["attributes"]["POSITION"]).astype(np.float32)
            if world is not None:
                vertices = (world[:3, :3] @ vertices.T).T + world[:3, 3]
            if "indices" in primitive:
                prim_indices = _read_accessor(
                    document, buffers, primitive["indices"]).reshape(-1).astype(np.uint32)
            else:
                prim_indices = np.arange(vertices.shape[0], dtype=np.uint32)
            positions.append(vertices.astype(np.float32))
            indices.append(prim_indices + base)
            base += vertices.shape[0]

    if not positions:
        return None
    vertices = np.concatenate(positions)
    combined = np.concatenate(indices)
    normals = _smooth_normals(vertices.astype(np.float64), combined)
    return _geometry_from_arrays(vertices, combined, normals=normals)


class _Part:
    __slots__ = (
        "axis",
        "color",
        "euler",
        "geometry",
        "joint",
        "mount",
        "parent",
        "pivot",
        "position",
        "source_url",
        "type",
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
        self.type = ""
        self.mount = None


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
        self._dh_params = {}
        self._skip_ids = ()
        self._spindle = None
        self._spindle_position = None

    @staticmethod
    def _collect_dh(parts):
        """Recover modified-DH (alpha, a, d) per joint from ``mount`` fields.

        Robot-arm parts are authored on their DH home frame and describe the
        link pose with ``mount = [a, -sin(alpha)*d, cos(alpha)*d, alpha_deg, 0, 0]``,
        so alpha/a/d can be recovered directly. World-axis machines (no
        ``mount``) yield an empty dict and use the generic transform path.
        """
        params = {}
        for part in parts:
            if (part.type != "angular" or part.joint is None
                    or part.mount is None):
                continue
            try:
                joint = int(part.joint)
            except (TypeError, ValueError):
                continue
            alpha = math.radians(float(part.mount[3]))
            a = float(part.mount[0])
            cos_a, sin_a = math.cos(alpha), math.sin(alpha)
            if abs(cos_a) > 1e-9:
                d = float(part.mount[2]) / cos_a
            elif abs(sin_a) > 1e-9:
                d = -float(part.mount[1]) / sin_a
            else:
                d = 0.0
            params[joint] = (alpha, a, d)
        return params

    @staticmethod
    def _dh_link_matrix(alpha, a, d, theta):
        """4x4 modified-DH link matrix (matches genserkins)."""
        sin_t, cos_t = math.sin(theta), math.cos(theta)
        sin_a, cos_a = math.sin(alpha), math.cos(alpha)
        return np.array([
            [cos_t, -sin_t, 0.0, a],
            [sin_t * cos_a, cos_t * cos_a, -sin_a, -sin_a * d],
            [sin_t * sin_a, cos_t * sin_a, cos_a, cos_a * d],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def _dh_frames(self, joint_reader):
        count = max(6, (max(self._dh_params) + 1) if self._dh_params else 6)
        frame = np.eye(4)
        frames = []
        for joint in range(count):
            params = self._dh_params.get(joint)
            if params is not None:
                alpha, a, d = params
                theta = math.radians(float(joint_reader(joint)))
                frame = frame @ self._dh_link_matrix(alpha, a, d, theta)
            frames.append(frame.copy())
        frames.append(frame.copy())  # tool frame
        return frames

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
            scene = _world_to_scene(part.world)
            return QVector3D(*map(float, scene[:3, 3]))
        if role == self.RotRole:
            return self._world_quaternion(_world_to_scene(part.world))
        if role == self.ColorRole:
            return part.color
        if role == self.VisibleRole:
            has_mesh = part.geometry is not None or bool(part.source_url)
            return bool(part.visible and self._enabled and has_mesh)
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

    def load(self, data, config_dir=None, skip_ids=()):
        """(Re)build the parts from ``MACHINE_PARTS`` *data* (a parsed mapping).

        *skip_ids* are case-insensitive id/model substrings to omit (e.g. the
        spindle when it is drawn from the ``[VTK] SPINDLE`` bit instead).
        """
        self._skip_ids = tuple(str(s).lower() for s in skip_ids)
        self._spindle = None
        self.beginResetModel()
        self._parts = []
        if isinstance(data, dict):
            self._walk(data, None, config_dir)
        self._dh_params = self._collect_dh(self._parts)
        self._recompute()
        self.endResetModel()
        if self._dh_params:
            LOG.info("Quick 3D machine: DH animation for joints %s",
                     sorted(self._dh_params))
        LOG.debug("Quick 3D machine assembly built with %d parts", len(self._parts))

    def _walk(self, node, parent, config_dir):
        for value in node.values():
            if not isinstance(value, dict):
                continue
            part = self._make_part(value, parent, config_dir)
            if part is None:
                # Skipped (e.g. spindle drawn from the INI instead); keep
                # walking so its children are still visited.
                self._walk(value, parent, config_dir)
                continue
            self._parts.append(part)
            self._walk(value, part, config_dir)

    def _make_part(self, data, parent, config_dir):
        if self._skip_ids:
            ident = str(data.get("id") or "").lower()
            model = str(data.get("model") or "").lower()
            if any(token in ident or token in model for token in self._skip_ids):
                return None
        part = _Part()
        part.parent = parent
        position = data.get("position")
        if isinstance(position, (list, tuple)):
            part.position = _vec3(position)
            if len(position) >= 6:
                part.euler = (float(position[3]), float(position[4]), float(position[5]))
        part.color = _rgba(data.get("color"))
        part.type = str(data.get("type") or "").lower()
        part.axis = str(data.get("axis") or "").upper()
        part.joint = data.get("joint")
        mount = data.get("mount")
        if isinstance(mount, (list, tuple)) and len(mount) >= 6:
            part.mount = tuple(float(value) for value in mount[:6])
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
            elif lower.endswith((".glb", ".gltf")):
                try:
                    part.geometry = _gltf_geometry(resolved)
                except (OSError, ValueError, KeyError, IndexError,
                        struct.error, json.JSONDecodeError):
                    LOG.exception("Quick 3D machine glTF read failed: %s", resolved)
                if part.geometry is None:
                    LOG.warning("Quick 3D machine glTF unavailable: %s", resolved)
            else:
                # Unknown format: let Qt Quick 3D try the asset URL.
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
        values = tuple(float(value) for value in joint_values)
        if values == self._joint_values:
            return
        self._joint_values = values
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

    def set_spindle(self, geometry, color="#b0c4de"):
        """Attach the ``[VTK] SPINDLE`` model, following the tool/6th-link frame."""
        part = _Part()
        part.geometry = geometry
        part.color = color
        part.type = "spindle"
        self._spindle = part
        row = len(self._parts)
        self.beginInsertRows(QModelIndex(), row, row)
        self._parts.append(part)
        self.endInsertRows()
        self._recompute()

    def set_spindle_visible(self, visible):
        if self._spindle is None:
            return
        self._spindle.visible = bool(visible)
        row = self._parts.index(self._spindle)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)

    def set_spindle_position(self, position):
        """Place the spindle model at the live machine position.

        The spindle is the head, not the cutter; the tool bit is a separate
        entity at the tool tip. Robot/DH assemblies position the spindle from
        their tool frame instead, so this is a no-op for them.
        """
        if self._spindle is None or self._dh_params:
            return
        try:
            position = tuple(float(value) for value in position[:3])
        except (TypeError, ValueError, IndexError):
            return
        if position == self._spindle_position:
            return
        self._spindle_position = position
        self._apply_spindle_position()
        row = self._parts.index(self._spindle)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)

    def _apply_spindle_position(self):
        if self._spindle is None:
            return
        world = np.eye(4)
        if self._spindle_position is not None and not self._dh_params:
            world[:3, 3] = self._spindle_position
        self._spindle.world = world

    def world_bounds(self):
        """Axis-aligned bounds of all part meshes in world space, or ``None``.

        Used to size the camera clip range so the arm (which can reach beyond
        the Cartesian machine limits) is never clipped front or back.
        """
        low = None
        high = None
        for part in self._parts:
            geometry = part.geometry
            if geometry is None:
                continue
            bmin, bmax = geometry.boundsMin(), geometry.boundsMax()
            corners = np.array([[x, y, z]
                                for x in (bmin.x(), bmax.x())
                                for y in (bmin.y(), bmax.y())
                                for z in (bmin.z(), bmax.z())], dtype=float)
            world = part.world
            points = corners @ world[:3, :3].T + world[:3, 3]
            pmin, pmax = points.min(axis=0), points.max(axis=0)
            low = pmin if low is None else np.minimum(low, pmin)
            high = pmax if high is None else np.maximum(high, pmax)
        if low is None:
            return None
        return low, high

    def _recompute(self):
        if self._dh_params:
            self._recompute_dh()
            return
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
        self._apply_spindle_position()

    def _recompute_dh(self):
        """Place robot-arm parts on their DH frames.

        Each angular part's world transform is ``current @ inv(home)`` for its
        joint (home = theta 0), so the STLs authored in the DH home pose move
        exactly as the kinematics do. Non-angular parts stay on their own
        transform (the static table/base).
        """
        joint_values = self._joint_values or ()

        def reader(joint):
            try:
                return float(joint_values[int(joint)])
            except (IndexError, TypeError, ValueError):
                return 0.0

        current = self._dh_frames(reader)
        home = self._dh_frames(lambda _joint: 0.0)
        tool_world = None
        tool_joint = -1
        for part in self._parts:
            if (part.type == "angular" and part.joint is not None
                    and self._as_joint(part.joint) in self._dh_params):
                joint = self._as_joint(part.joint)
                target = current[joint] @ np.linalg.inv(home[joint])
                position = np.asarray(part.position, dtype=float)
                # Cancel the part's own position (no-op for robot yamls).
                target[:3, 3] = target[:3, 3] - target[:3, :3] @ position
                part.world = target
                if joint > tool_joint:
                    tool_joint, tool_world = joint, part.world
            else:
                local = np.eye(4)
                local[:3, :3] = _euler_matrix(*part.euler)
                local[:3, 3] = part.position
                part.world = local
        # The INI spindle rides the deepest joint (the tool / 6th link), exactly
        # where the yaml spindle used to sit.
        if self._spindle is not None and tool_world is not None:
            self._spindle.world = tool_world.copy()

    @staticmethod
    def _as_joint(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

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
