"""Smoke tests for the Qt Quick 3D geometry boundary (no LinuxCNC required)."""

import importlib.util
import os
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QtQuickWidgets = pytest.importorskip("PySide6.QtQuickWidgets")
QtCore = pytest.importorskip("PySide6.QtCore")
QtGui = pytest.importorskip("PySide6.QtGui")
pytest.importorskip("PySide6.QtQuick3D")

ROOT = Path(__file__).resolve().parents[2]
GEOMETRY_PATH = ROOT / "src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/geometry.py"
QML_PATH = GEOMETRY_PATH.with_name("scene.qml")
spec = importlib.util.spec_from_file_location("qtquick3d_backplot_geometry", GEOMETRY_PATH)
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)


@pytest.fixture(scope="module")
def qt_app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_line_geometry_replaces_vertex_buffer_and_updates_bounds():
    line = geometry.LineGeometry()
    points = np.asarray(((1, 2, 3), (-4, 5, 6)), dtype=np.float32)
    line.replace(points)

    assert line.vertexData() == points.tobytes()
    assert line.stride() == 12
    assert line.attributeCount() == 1
    assert line.boundsMin() == QtGui.QVector3D(-4, 2, 3)
    assert line.boundsMax() == QtGui.QVector3D(1, 5, 6)

    line.replace(np.zeros((0, 3), dtype=np.float32))
    assert len(line.vertexData()) == 0


def test_cnc_z_up_points_are_mapped_to_quick3d_y_up():
    points = geometry.map_points_to_quick3d(((1, 2, 3), (4, 5, 6)))
    assert points.tolist() == [[1.0, 3.0, -2.0], [4.0, 6.0, -5.0]]
    assert geometry.map_vector_to_quick3d((0, 0, 1)) == QtGui.QVector3D(0, 1, 0)


def test_qml_scene_loads_with_python_geometry_and_live_camera(qt_app):
    machine_spec = importlib.util.spec_from_file_location(
        "qtquick3d_machine", GEOMETRY_PATH.with_name("machine.py"))
    machine = importlib.util.module_from_spec(machine_spec)
    machine_spec.loader.exec_module(machine)

    widget = QtQuickWidgets.QQuickWidget()
    plot_data = geometry.Quick3DPlotData()
    widget.rootContext().setContextProperty("plotData", plot_data)
    widget.rootContext().setContextProperty("machineParts", machine.MachinePartsModel())
    widget.setSource(QtCore.QUrl.fromLocalFile(str(QML_PATH)))

    assert widget.status() == QtQuickWidgets.QQuickWidget.Status.Ready, [
        error.toString() for error in widget.errors()
    ]
    root = widget.rootObject()
    camera = root.findChild(QtCore.QObject, "perspectiveCamera")
    assert camera is not None
    assert camera.setProperty("position", QtGui.QVector3D(10, 20, 30))
    plot_data.feedColor = "#123456"
    assert plot_data.feedColor == "#123456"
    assert camera.property("position") == QtGui.QVector3D(10, 20, 30)
    widget.close()


def test_touch_surface_avoids_pinch_area():
    """Qt 6.12 warns from the QML loader thread for QQuickPinchArea.

    That warning reaches QtPyVCP's Python Qt message handler, which then
    deadlocks on the GIL while QQuickWidget.setSource() is still running.
    MultiPointTouchArea provides the same gestures without the warning.
    """
    text = QML_PATH.read_text(encoding="utf-8")
    assert "PinchArea {" not in text
    assert "MultiPointTouchArea {" in text
