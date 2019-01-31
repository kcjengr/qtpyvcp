from qtpyvcp.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from frame import VCPFrame
class VCPFramePlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPFrame
    def isContainer(self):
        return True

from tab_widget import VCPTabWidget
class VCPTabWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPTabWidget
