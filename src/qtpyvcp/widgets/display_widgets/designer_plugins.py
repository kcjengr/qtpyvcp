import os


def _env_flag(name):
    value = os.getenv(name)
    if value is None:
        return False
    value = str(value).strip().lower()
    if value in ('', '0', 'false', 'no', 'off'):
        return False
    return True


IN_DESIGNER = _env_flag('DESIGNER')

from qtpyvcp.widgets.qtdesigner import _DesignerPlugin
from qtpyvcp.widgets.qtdesigner.designer_plugin import RulesEditorExtension

from .status_label import StatusLabel
class StatusLabelPlugin(_DesignerPlugin):
    def pluginClass(self):
        return StatusLabel

from .dro_label import DROLabel
from qtpyvcp.widgets.qtdesigner.dro_editor import DroEditorExtension
class DROLabel_Plugin(_DesignerPlugin):
    def pluginClass(self):
        return DROLabel
    def designerExtensions(self):
        return [DroEditorExtension, RulesEditorExtension]

#
# Remove camera until refactored to not need qtpy
#
# from .camera.camera import Camera
# class CameraPlugin(_DesignerPlugin):
#     def pluginClass(self):
#         return Camera
#     def toolTip(self):
#         return "Camera widget"
#     def isContainer(self):
#         return True

from .bar_indicator import BarIndicator
class BarIndicatorPlugin(_DesignerPlugin):
    def pluginClass(self):
        return BarIndicator

from .status_led import StatusLED
class StatusLEDPlugin(_DesignerPlugin):
    def pluginClass(self):
        return StatusLED

# Backplot placeholders. The real widgets need a live render surface and
# LinuxCNC, so Designer gets a placeholder that is swapped at runtime.
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Slot, Property, QSize
from PySide6.QtGui import QColor


class BackplotPlaceholder(QWidget):
    """Base placeholder for backplot widgets in designer mode."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # nav-helper camera-gizmo qproperties; copied to the real backplot at
        # runtime by VCPMainWindow when a Designer placeholder is replaced.
        self._nav_helper_props = {}
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Backplot\n(3D visualization)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #2a2a2a; color: #cccccc;")

    # Dummy slot methods for UI connections in Designer.
    @Slot()
    def reload_program(self):
        pass

    @Slot(bool)
    @Slot(object)
    def viewPerspective(self, _persp):
        pass

    @Slot(bool)
    @Slot(object)
    def showSpindle(self, _show):
        pass

    @Slot()
    def setViewY(self):
        pass

    @Slot()
    def setViewX(self):
        pass

    @Slot()
    def setViewZ(self):
        pass

    @Slot()
    def setViewXZ(self):
        pass

    @Slot()
    def setViewXZ2(self):
        pass

    @Slot()
    def setViewZ2(self):
        pass

    @Slot()
    def setViewPath(self):
        pass

    @Slot()
    def setViewP(self):
        pass

    @Slot()
    def setViewOrtho(self):
        pass

    @Slot()
    def setViewPersp(self):
        pass

    @Slot()
    def setViewProgram(self):
        pass

    @Slot()
    def setViewMachine(self):
        pass

    @Slot(int)
    def setView(self, _index):
        pass

    @Slot()
    def clearLivePlot(self):
        pass

    @Slot()
    def printView(self):
        pass

    @Slot()
    def zoomIn(self):
        pass

    @Slot()
    def zoomOut(self):
        pass

    @Slot(bool)
    def enableBreadcrumbs(self, _enabled):
        pass

    @Slot(bool)
    def enableMultiTouch(self, _enabled):
        pass

    @Slot(bool)
    def setProgramViewWhenLoadingProgram(self, _enabled):
        pass

    @Slot(bool)
    def alphaBlend(self, _alpha):
        pass

    @Slot(bool)
    @Slot(object)
    def showSurface(self, _show):
        pass

    @Slot(bool)
    @Slot(object)
    def showGrid(self, _show):
        pass

    @Slot(bool)
    @Slot(object)
    def showProgramBounds(self, _show):
        pass

    @Slot()
    def toggleProgramBounds(self):
        pass

    @Slot(bool)
    @Slot(object)
    def showMachineBounds(self, _show):
        pass

    @Slot()
    def toggleMachineBounds(self):
        pass

    @Slot(bool)
    @Slot(object)
    def showMachineTicks(self, _show):
        pass

    @Slot()
    def toggleMachineTicks(self):
        pass

    @Slot(bool)
    @Slot(object)
    def showMachineLabels(self, _show):
        pass

    @Slot()
    def toggleMachineLabels(self):
        pass

    @Slot(bool)
    @Slot(object)
    def showMultiColorPath(self, _show):
        pass

    @Slot()
    def toggleMultiColorPath(self):
        pass

    @Slot(bool)
    @Slot(object)
    def showMachine(self, _show):
        pass

    @Slot(bool)
    def enable_panning(self, _enabled):
        pass

    # nav-helper camera-gizmo qproperties (mirrored by the real widget when a
    # Designer placeholder is replaced).
    @staticmethod
    def _nav_prop(qt_type, key):
        def _get(self):
            return self._nav_helper_props.get(key)

        def _set(self, value):
            self._nav_helper_props[key] = value

        def _reset(self):
            # Back to "not set", the fresh state, which the gizmo config
            # fills with its own default. See reset_to() in base_widget for
            # why every Property needs a reset function.
            self._nav_helper_props.pop(key, None)

        return Property(qt_type, _get, _set, freset=_reset)

    navHelperEnabled = _nav_prop(bool, "enabled")
    navHelperAnimate = _nav_prop(bool, "animate")
    navHelperShouldResetCamera = _nav_prop(bool, "should_reset_camera")
    navHelperKeyActivation = _nav_prop(str, "key_activation")
    navHelperAnchor = _nav_prop(str, "anchor")
    navHelperPadding = _nav_prop(QSize, "padding")
    navHelperSize = _nav_prop(QSize, "size")
    navHelperTotalLength = _nav_prop(float, "total_length")
    navHelperHandleSize = _nav_prop(float, "handle_size")
    navHelperNormalizedHandleDia = _nav_prop(float, "normalized_handle_dia")
    navHelperContainerVisibility = _nav_prop(bool, "container_visibility")
    navHelperDragable = _nav_prop(bool, "dragable")
    navHelperPickable = _nav_prop(bool, "pickable")
    navHelperShaftResolution = _nav_prop(int, "shaft_resolution")
    navHelperHandleResolution = _nav_prop(int, "handle_resolution")
    navHelperXAxisColor = _nav_prop(QColor, "x_axis_color")
    navHelperYAxisColor = _nav_prop(QColor, "y_axis_color")
    navHelperZAxisColor = _nav_prop(QColor, "z_axis_color")
    # show/hide + extra behavior knobs
    navHelperHandleVisibility = _nav_prop(bool, "handle_visibility")
    navHelperLabelsVisible = _nav_prop(bool, "labels_visible")
    navHelperLabels = _nav_prop("QStringList", "labels")
    navHelperAxisColor = _nav_prop(QColor, "axis_color")
    navHelperContainerCircumferentialResolution = _nav_prop(
        int, "container_circumferential_resolution")
    navHelperContainerRadialResolution = _nav_prop(
        int, "container_radial_resolution")
    navHelperAnimatorTotalFrames = _nav_prop(int, "animator_total_frames")
    navHelperProcessEvents = _nav_prop(bool, "process_events")
    navHelperManagesCursor = _nav_prop(bool, "manages_cursor")
    navHelperPriority = _nav_prop(float, "priority")


from .notification_widget import NotificationWidget
class NotificationPlugin(_DesignerPlugin):
    def pluginClass(self):
        return NotificationWidget

from .active_gcodes_table import ActiveGcodesTable
class GcodeReferenceTablePlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActiveGcodesTable

from .gcode_properties import GCodeProperties
class GCodePropertiesPlugin(_DesignerPlugin):
    def pluginClass(self):
        return GCodeProperties


# ---------------------------------------------------------------------------
# Qt3D0 backplot.  Like every renderer it cannot be instantiated in Designer
# (it needs a live Qt Quick 3D surface + LinuxCNC), so Designer gets a
# placeholder and the real widget is swapped in at runtime (see VCPMainWindow).
# The widget name is historical; the runtime renderer is Qt Quick 3D.
# ---------------------------------------------------------------------------

class Qt3D0Placeholder(BackplotPlaceholder):
    """Placeholder for Qt3D0 in designer mode."""

    @staticmethod
    def _color_property(name, default):
        def get(self):
            value = self._qt3d_property_values.get(name)
            return QColor(value) if value is not None else QColor(*default)

        def set_(self, value):
            self._qt3d_property_values[name] = QColor(value)

        def reset(self):
            self._qt3d_property_values.pop(name, None)

        return Property(QColor, get, set_, freset=reset)

    @staticmethod
    def _bool_property(name, default):
        def get(self):
            return bool(self._qt3d_property_values.get(name, default))

        def set_(self, value):
            self._qt3d_property_values[name] = bool(value)

        def reset(self):
            self._qt3d_property_values.pop(name, None)

        return Property(bool, get, set_, freset=reset)

    backgroundColor = _color_property.__func__("backgroundColor", (0, 0, 0, 255))
    backgroundColor2 = _color_property.__func__("backgroundColor2", (0, 0, 0, 255))
    traverseColor = _color_property.__func__("traverseColor", (200, 35, 35, 255))
    arcfeedColor = _color_property.__func__("arcfeedColor", (110, 110, 255, 255))
    feedColor = _color_property.__func__("feedColor", (210, 210, 255, 255))
    dwellColor = _color_property.__func__("dwellColor", (0, 0, 255, 255))
    userColor = _color_property.__func__("userColor", (0, 100, 255, 255))
    gridVisible = _bool_property.__func__("gridVisible", False)
    machineBoundsVisible = _bool_property.__func__("machineBoundsVisible", True)
    wcsOriginsVisible = _bool_property.__func__("wcsOriginsVisible", True)
    programBoundsVisible = _bool_property.__func__("programBoundsVisible", False)

    @Property(bool, freset=lambda self: setattr(self, "enableProgramTicks", True))
    def enableProgramTicks(self):
        return getattr(self, "_enable_program_ticks", True)

    @enableProgramTicks.setter
    def enableProgramTicks(self, value):
        self._enable_program_ticks = bool(value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._qt3d_property_values = {}
        label = self.findChild(QLabel)
        if label is not None:
            label.setText("Qt3D0 Backplot\n(Qt Quick 3D visualization)")


class Qt3D0(Qt3D0Placeholder):
    pass


class Qt3D0Plugin(_DesignerPlugin):
    def objectName(self):
        return "qt3d0"

    def name(self):
        return "Qt3D0"

    def pluginClass(self):
        if IN_DESIGNER:
            return Qt3D0
        try:
            # Preserve the historical .ui class name while using the actively
            # maintained Qt Quick 3D renderer at runtime.
            from .qtquick3d_backplot.qtquick3d_backplot import Qt3D0 as RuntimeQt3D0
            return RuntimeQt3D0
        except Exception:
            return Qt3D0

    def toolTip(self):
        return "Qt Quick 3D backplot widget (Qt3D0)"

    def whatsThis(self):
        return "3D visualization of tool paths using Qt Quick 3D. Only functional at runtime."

    def isContainer(self):
        return True


if IN_DESIGNER:
    _Qt3D0 = Qt3D0
else:
    try:
        from .qtquick3d_backplot.qtquick3d_backplot import Qt3D0 as _Qt3D0
    except Exception:
        _Qt3D0 = Qt3D0

Qt3D0 = _Qt3D0
