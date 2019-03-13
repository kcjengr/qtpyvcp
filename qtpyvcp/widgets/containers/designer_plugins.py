from qtpyvcp.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from frame import VCPFrame
class VCPFramePlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPFrame
    def isContainer(self):
        return True

from widget import VCPWidget
class VCPWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPWidget
    def isContainer(self):
        return True
