"""Mechanical model loading for the Qt3D backplot.

Supports the two mesh formats the VTK backplot handles for machine parts:
STL (parsed here; Qt3D has no built-in STL reader) and glTF/GLB (loaded
through ``Qt3DRender.QSceneLoader``).  Everything produces a ready-to-parent
``QEntity`` with a solid material.
"""

import os
import struct

import numpy as np
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import QUrl

from qtpyvcp.utilities import logger

from . import scene

LOG = logger.getLogger(__name__)


def load_model_entity(parent, path, color=(0.9, 0.9, 0.9, 1.0), name=None):
    """Return a ``QEntity`` for *path*, or ``None`` when unsupported/missing."""
    if not path or not os.path.isfile(path):
        LOG.warning("Qt3D model not found: %s", path)
        return None

    lower = str(path).lower()
    if lower.endswith(('.glb', '.gltf')):
        return _load_gltf_entity(parent, path, name=name)
    if lower.endswith('.stl'):
        return load_stl_entity(parent, path, color=color, name=name)

    LOG.warning("Unsupported model format for Qt3D backplot: %s", path)
    return None


def load_stl_entity(parent, path, color=(0.9, 0.9, 0.9, 1.0), name=None):
    """Load an STL mesh and return a shaded entity."""
    triangles = read_stl_triangles(path)
    if triangles is None or len(triangles) == 0:
        return None

    vertices = triangles.reshape(-1, 3).astype(np.float32)
    normals = _facet_normals(triangles)
    indices = np.arange(vertices.shape[0], dtype=np.uint32)

    entity = Qt3DCore.QEntity(parent)
    entity.setObjectName(name or os.path.basename(path))

    geometry = scene.build_indexed_triangle_geometry(vertices, indices, normals)
    renderer = Qt3DRender.QGeometryRenderer(entity)
    renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Triangles)
    renderer.setGeometry(geometry)

    material = scene.solid_material(color, entity)

    entity.addComponent(renderer)
    entity.addComponent(material)
    entity._qt3d_refs = (geometry, renderer, material)
    return entity


def _load_gltf_entity(parent, path, name=None):
    entity = Qt3DCore.QEntity(parent)
    entity.setObjectName(name or os.path.basename(path))

    loader = Qt3DRender.QSceneLoader(entity)
    loader.setSource(QUrl.fromLocalFile(path))
    entity.addComponent(loader)
    entity._qt3d_refs = (loader,)
    return entity


# -- STL parsing -----------------------------------------------------------

def read_stl_triangles(path):
    """Return an ``(N, 3, 3)`` float64 array of triangle vertices, or ``None``."""
    try:
        with open(path, 'rb') as handle:
            header = handle.read(84)
            if len(header) < 84:
                return _read_ascii_stl(path)

            # Binary STL: 80-byte header, uint32 count, then 50-byte facets.
            count = struct.unpack('<I', header[80:84])[0]
            expected = 84 + count * 50
            if os.path.getsize(path) == expected:
                return _read_binary_stl(handle, count)

        # Size mismatch: treat as ASCII.
        return _read_ascii_stl(path)
    except OSError:
        LOG.exception("failed reading STL %s", path)
        return None


def _read_binary_stl(handle, count):
    records = np.dtype([('normal', '<3f4'), ('vertices', '<9f'), ('attr', '<u2')])
    data = np.frombuffer(handle.read(count * 50), dtype=records, count=count)
    return data['vertices'].reshape(count, 3, 3).astype(np.float64)


def _read_ascii_stl(path):
    vertices = []
    with open(path, 'r', errors='ignore') as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith('vertex'):
                parts = stripped.split()
                if len(parts) >= 4:
                    vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
    if len(vertices) % 3 != 0 or not vertices:
        return None
    return np.asarray(vertices, dtype=np.float64).reshape(-1, 3, 3)


def _facet_normals(triangles):
    edges1 = triangles[:, 1] - triangles[:, 0]
    edges2 = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(edges1, edges2)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1.0
    normals = normals / lengths
    return np.repeat(normals, 3, axis=0).astype(np.float32)
