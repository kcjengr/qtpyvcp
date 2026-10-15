"""Qt3D geometry smoke tests (no render window or LinuxCNC session required)."""

import gc
import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
Qt3DCore = pytest.importorskip("PySide6.Qt3DCore").Qt3DCore
Qt3DRender = pytest.importorskip("PySide6.Qt3DRender").Qt3DRender
QColor = pytest.importorskip("PySide6.QtGui").QColor

from qtpyvcp.widgets.display_widgets.qt3d_backplot.scene import (
    build_gradient_background,
    build_indexed_triangle_geometry,
    build_line_entity,
)


@pytest.fixture(scope="module")
def qt_app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _renderer(entity):
    return next(component for component in entity.components()
                if isinstance(component, Qt3DRender.QGeometryRenderer))


def test_uncoloured_lines_have_a_visible_colour_attribute(qt_app):
    root = Qt3DCore.QEntity()
    points = np.asarray(((0, 0, 0), (1, 2, 3)), dtype=np.float32)
    entity = build_line_entity(root, points, name="bounds")
    gc.collect()

    renderer = _renderer(entity)
    attributes = {attribute.name(): attribute
                  for attribute in renderer.geometry().attributes()}
    assert attributes[Qt3DCore.QAttribute.defaultPositionAttributeName()].count() == 2
    assert attributes[Qt3DCore.QAttribute.defaultColorAttributeName()].count() == 2
    assert len(entity.components()) == 2


def test_per_segment_colours_expand_to_both_line_vertices(qt_app):
    root = Qt3DCore.QEntity()
    points = np.asarray(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)),
                        dtype=np.float32)
    colors = np.asarray(((255, 0, 0, 255), (0, 255, 0, 255)), dtype=np.uint8)
    entity = build_line_entity(root, points, colors, name="program")

    attributes = {attribute.name(): attribute
                  for attribute in _renderer(entity).geometry().attributes()}
    assert attributes[Qt3DCore.QAttribute.defaultColorAttributeName()].count() == 4


def test_gradient_background_contains_position_and_color_attributes(qt_app):
    root = Qt3DCore.QEntity()
    entity = build_gradient_background(root, QColor("#101020"), QColor("#304060"))
    gc.collect()

    renderer = _renderer(entity)
    attributes = {attribute.name(): attribute
                  for attribute in renderer.geometry().attributes()}
    assert attributes[Qt3DCore.QAttribute.defaultPositionAttributeName()].count() == 4
    assert attributes[Qt3DCore.QAttribute.defaultColorAttributeName()].count() == 4


def test_triangle_geometry_keeps_position_normal_and_index_attributes(qt_app):
    vertices = np.asarray(((0, 0, 0), (1, 0, 0), (0, 1, 0)), dtype=np.float32)
    normals = np.asarray(((0, 0, 1),) * 3, dtype=np.float32)
    geometry = build_indexed_triangle_geometry(vertices, (0, 1, 2), normals)
    gc.collect()

    attributes = {attribute.name(): attribute for attribute in geometry.attributes()}
    assert Qt3DCore.QAttribute.defaultPositionAttributeName() in attributes
    assert Qt3DCore.QAttribute.defaultNormalAttributeName() in attributes
    assert any(attribute.attributeType() == Qt3DCore.QAttribute.IndexAttribute
               for attribute in attributes.values())


def test_qt3d_backplot_exposes_vtk_color_properties(qt_app):
    from qtpyvcp.widgets.display_widgets.designer_plugins import Qt3D0Placeholder
    from qtpyvcp.widgets.display_widgets.qt3d_backplot.qt3d_backplot import Qt3D0

    names = (
        "backgroundColor", "backgroundColor2", "traverseColor", "arcfeedColor",
        "feedColor", "dwellColor", "userColor", "enableProgramTicks",
        "navHelperXAxisColor", "navHelperYAxisColor", "navHelperZAxisColor",
    )
    for name in names:
        assert Qt3D0.staticMetaObject.indexOfProperty(name) >= 0
        assert Qt3D0Placeholder.staticMetaObject.indexOfProperty(name) >= 0

    placeholder = Qt3D0Placeholder()
    placeholder.traverseColor = QColor(1, 2, 3)
    assert placeholder.traverseColor == QColor(1, 2, 3)
    prop = placeholder.metaObject().property(
        placeholder.metaObject().indexOfProperty("traverseColor"))
    assert prop.reset(placeholder)
    assert placeholder.traverseColor == QColor(200, 35, 35)
