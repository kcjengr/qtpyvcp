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

from stack import VCPStackedWidget
class VCPStackedWidgetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPStackedWidget
    def isContainer(self):
        return True
    def domXml(self):
        return """
    <widget class="VCPStackedWidget" name="stackedWidget">
    <property name="geometry">
     <rect>
      <x>120</x>
      <y>420</y>
      <width>371</width>
      <height>221</height>
     </rect>
    </property>
    <widget class="QWidget" name="page_1"/>
    <widget class="QWidget" name="page_2"/>
   </widget>"""
