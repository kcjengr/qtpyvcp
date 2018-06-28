#!/usr/bin/python

from PyQt5.QtGui import QIcon
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin

from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

class MainWindowPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent=None):
        super(MainWindowPlugin, self).__init__(parent)
        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return VCPMainWindow(parent)

    def name(self):
        return "VCPMainWindow"

    def group(self):
        return "LinuxCNC - HAL"

    def icon(self):
        return QIcon()

    def toolTip(self):
        return "LED widget used to indicate the state of bool HAL pins."

    def whatsThis(self):
        return "LED widget used to indicate the state of bool HAL pins."

    def isContainer(self):
        return True

    def domXml(self):
        return '''
<widget class="VCPMainWindow" name="VCP Main Window">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>500</width>
    <height>300</height>
   </rect>
  </property>
  <widget class="QWidget" name="centralwidget"/>
</widget>
'''

    def includeFile(self):
        return "QtPyVCP.widgets.form_widgets.main_window"
