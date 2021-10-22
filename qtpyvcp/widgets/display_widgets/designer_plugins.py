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

from .camera.camera import Camera
class CameraPlugin(_DesignerPlugin):
    def pluginClass(self):
        return Camera
    def toolTip(self):
        return "Camera widget"
    def isContainer(self):
        return True

from .bar_indicator import BarIndicator
class BarIndicatorPlugin(_DesignerPlugin):
    def pluginClass(self):
        return BarIndicator

from .status_led import StatusLED
class StatusLEDPlugin(_DesignerPlugin):
    def pluginClass(self):
        return StatusLED

from .vtk_backplot.vtk_backplot import VTKBackPlot
class VTKWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VTKBackPlot
    def isContainer(self):
        return True

from .notification_widget import NotificationWidget
class NotificationPlugin(_DesignerPlugin):
    def pluginClass(self):
        return NotificationWidget

from .active_gcodes_table import ActiveGcodesTable
class GcodeReferenceTable_Plugin(_DesignerPlugin):
    def pluginClass(self):
        return ActiveGcodesTable
