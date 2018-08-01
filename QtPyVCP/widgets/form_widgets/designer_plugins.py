#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import _DesignerPlugin

from main_window import VCPMainWindow
class MainWindowPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPMainWindow
    def isContainer(self):
        return True
    def group(self):
        return "Use ONLY as a Toplevel!!!"
    def domXml(self):
        return '''<widget class="VCPMainWindow" name="VCP Main Window">
                   <property name="geometry">
                    <rect>
                     <x>0</x>
                     <y>0</y>
                     <width>500</width>
                     <height>300</height>
                    </rect>
                   </property>
                   <widget class="QWidget" name="centralwidget"/>
                  </widget>'''
