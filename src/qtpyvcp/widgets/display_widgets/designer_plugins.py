import os
IN_DESIGNER = os.getenv('DESIGNER', False)

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
from PySide6.QtCore import Qt

class VTKBackPlotPlaceholder(QWidget):
    """Placeholder for VTKBackPlot widget in designer mode."""
    def __init__(self, parent=None):
        print("DEBUG: VTKBackPlot placeholder __init__ START", flush=True)
        super().__init__(parent)
        print("DEBUG: VTKBackPlot super().__init__ done", flush=True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("VTK Backplot\n(3D visualization)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #2a2a2a; color: #cccccc;")
        print("DEBUG: VTKBackPlot placeholder __init__ DONE", flush=True)

    # Dummy methods for UI connections
    def setViewY(self): pass
    def setViewX(self): pass
    def setViewZ(self): pass
    def setViewPath(self): pass
    def setViewP(self): pass
    def setViewOrtho(self): pass
    def setViewPersp(self): pass
    def setViewProgram(self): pass
    def setViewMachine(self): pass
    def clearLivePlot(self): pass
    def zoomIn(self): pass
    def zoomOut(self): pass
    def enable_panning(self, enabled): pass

class VTKWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        # Return the placeholder for designer mode, real widget for runtime
        if IN_DESIGNER:
            return VTKBackPlotPlaceholder
        else:
            # Import the real VTK widget at runtime
            try:
                from .vtk_backplot.vtk_backplot import VTKBackPlot
                return VTKBackPlot
            except ImportError:
                return VTKBackPlotPlaceholder
    
    def toolTip(self):
        return "VTK 3D Backplot Widget (runtime only)"
    
    def whatsThis(self):
        return "3D visualization of tool paths using VTK. Only functional at runtime."
    
    def isContainer(self):
        return True

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
