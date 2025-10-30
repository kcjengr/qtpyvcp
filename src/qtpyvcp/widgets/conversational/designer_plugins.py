from qtpyvcp.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from .facing import FacingWidget
from .xy_coord import XYCoordWidget
from .hole_circle import HoleCircleWidget
from .int_line_edit import IntLineEdit
from .float_line_edit import FloatLineEdit

class FloatLineEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return FloatLineEdit


class IntLineEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return IntLineEdit


class HoleCircleWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HoleCircleWidget


class XYCoordWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return XYCoordWidget


class FacingWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return FacingWidget
