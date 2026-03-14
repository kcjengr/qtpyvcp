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
from PySide6.QtCore import Qt, Slot

class VTKBackPlotPlaceholder(QWidget):
    """Placeholder for VTKBackPlot widget in designer mode."""
    def __init__(self, parent=None):
        super().__init__(parent)
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
