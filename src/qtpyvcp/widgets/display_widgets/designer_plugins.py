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

# VTK Widget - Cannot be instantiated in designer due to VTK dependencies
# Create a placeholder class for designer mode only
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Slot, Property, QSize
from PySide6.QtGui import QColor


class VTKBackPlotPlaceholder(QWidget):
    """Placeholder for VTKBackPlot widget in designer mode."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # nav-helper camera-gizmo qproperties; copied to the real backplot at
        # runtime by VCPMainWindow._replace_vtk_placeholders_runtime
        self._nav_helper_props = {}
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("VTK Backplot\n(3D visualization)")
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

    # nav-helper camera-gizmo qproperties (mirror VTKBackPlot; copied to the
    # real widget at runtime, see VCPMainWindow._replace_vtk_placeholders_runtime)
    @staticmethod
    def _nav_prop(qt_type, key):
        def _get(self):
            return self._nav_helper_props.get(key)

        def _set(self, value):
            self._nav_helper_props[key] = value

        return Property(qt_type, _get, _set)

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


# Give Designer a class whose runtime name matches the requested class
# to prevent custom widget factory class-name mismatch warnings.
class VTKBackPlot(VTKBackPlotPlaceholder):
    pass

class VTKWidgetPlugin(_DesignerPlugin):
    def objectName(self):
        # Keep Probe Basic compatibility: many .ui signal receivers target
        # object name "vtk". If Designer inserts "vtkbackplot" by default,
        # those connections silently break when users replace the widget.
        return "vtk"

    def name(self):
        # Expose the runtime class name in Designer while still using a
        # placeholder implementation when DESIGNER is set.
        return "VTKBackPlot"

    def pluginClass(self):
        # Return the placeholder for designer mode, real widget for runtime
        if IN_DESIGNER:
            return VTKBackPlot
        else:
            # Import the real VTK widget at runtime
            try:
                from .vtk_backplot.vtk_backplot import VTKBackPlot as RuntimeVTKBackPlot
                return RuntimeVTKBackPlot
            except ImportError:
                return VTKBackPlot
    
    def toolTip(self):
        return "VTK 3D Backplot Widget (runtime only)"
    
    def whatsThis(self):
        return "3D visualization of tool paths using VTK. Only functional at runtime."
    
    def isContainer(self):
        return True

# Export a VTKBackPlot symbol so compiled UIs that import from this module
# succeed. In runtime mode, prefer the real widget and only fall back if import
# actually fails.
if IN_DESIGNER:
    _VTKBackPlot = VTKBackPlot
else:
    try:
        from .vtk_backplot.vtk_backplot import VTKBackPlot as _VTKBackPlot
    except Exception:
        _VTKBackPlot = VTKBackPlot

VTKBackPlot = _VTKBackPlot

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
