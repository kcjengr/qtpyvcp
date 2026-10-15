"""Machine-part assembly for the Qt3D backplot.

Builds a hierarchy of entities from the same ``MACHINE_PARTS`` YAML the VTK
backplot consumes.  Each node becomes an entity with a transform; nested nodes
become children, so a joint rotation on a parent moves everything below it.
"""

import os

from PySide6.Qt3DCore import Qt3DCore
from PySide6.QtGui import QVector3D

from qtpyvcp.utilities import logger

from . import models

LOG = logger.getLogger(__name__)


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
        return (color[0], color[1], color[2], alpha)
    return (0.9, 0.9, 0.9, 1.0)


class MachineAssembly:
    """Joint-aware entity hierarchy built from ``MACHINE_PARTS`` data."""

    def __init__(self, parent_entity, data, config_dir=None):
        self.root = Qt3DCore.QEntity(parent_entity)
        self.root.setObjectName("machine_parts")
        self.config_dir = config_dir
        self._parts = []
        if isinstance(data, dict):
            self._walk(data, self.root)
        LOG.debug("Qt3D machine assembly built with %d parts", len(self._parts))

    # -- construction ------------------------------------------------------

    def _walk(self, node, parent_entity):
        for value in node.values():
            if not isinstance(value, dict):
                continue
            entity = self._add_part(value, parent_entity)
            self._walk(value, entity)

    def _add_part(self, data, parent_entity):
        entity = Qt3DCore.QEntity(parent_entity)
        entity.setObjectName(str(data.get('id') or data.get('name') or 'part'))

        transform = Qt3DCore.QTransform()
        position = data.get('position') or (0.0,) * 6
        tx, ty, tz = _vec3(position)
        transform.setTranslation(QVector3D(tx, ty, tz))
        if len(position) >= 6:
            transform.setRotationX(float(position[3]))
            transform.setRotationY(float(position[4]))
            transform.setRotationZ(float(position[5]))
        entity.addComponent(transform)

        model_path = data.get('model')
        if model_path:
            resolved = self._resolve_model(model_path)
            model_entity = models.load_model_entity(
                entity, resolved, color=_rgba(data.get('color')),
                name=os.path.basename(str(model_path)))
            if model_entity is None:
                LOG.debug("machine part model unavailable: %s", model_path)

        self._parts.append({
            'entity': entity,
            'transform': transform,
            'axis': str(data.get('axis') or '').upper(),
            'type': str(data.get('type') or '').lower(),
            'joint': data.get('joint'),
            'origin': data.get('origin'),
            'base_position': list(position) if isinstance(position, (list, tuple)) else [0.0] * 6,
        })
        return entity

    def _resolve_model(self, path):
        text = str(path)
        if os.path.isabs(text) or not self.config_dir:
            return text
        return os.path.normpath(os.path.join(self.config_dir, text))

    # -- animation ---------------------------------------------------------

    def apply_joint_values(self, joint_values):
        """Rotate rotary-tagged parts from live joint feedback.

        *joint_values* is the LinuxCNC joint position tuple.  Linear parts are
        left at their configured position; rotary joints are applied about the
        part origin when one is supplied.
        """
        if not joint_values:
            return
        for part in self._parts:
            joint = part['joint']
            axis = part['axis']
            if joint is None or axis not in ('A', 'B', 'C'):
                continue
            try:
                angle = float(joint_values[int(joint)])
            except (IndexError, TypeError, ValueError):
                continue

            origin = _vec3(part['origin']) if part['origin'] else (0.0, 0.0, 0.0)
            transform = part['transform']
            transform.setRotation(Qt3DCore.QTransform.fromAxisAndAngle(
                QVector3D(*origin), _axis_vector(axis), angle))

    def set_enabled(self, enabled):
        self.root.setEnabled(bool(enabled))


def _axis_vector(axis):
    return {
        'A': QVector3D(1.0, 0.0, 0.0),
        'B': QVector3D(0.0, 1.0, 0.0),
        'C': QVector3D(0.0, 0.0, 1.0),
    }.get(axis, QVector3D(0.0, 0.0, 1.0))
