from qtpyvcp.widgets.conversational.hole_circle import *
from qtpyvcp.widgets.qtdesigner import _DesignerPlugin


class HoleCircleWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HoleCircleWidget

