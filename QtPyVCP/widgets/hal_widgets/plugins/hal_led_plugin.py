#!/usr/bin/python2

from PyQt5.QtGui import QIcon
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin

from QtPyVCP.widgets.hal_widgets.hal_led_widget import HalLedWidget

class HalLedPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent=None):
        super(HalLedPlugin, self).__init__(parent)

        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return

        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return HalLedWidget(parent)

    def name(self):
        return "HalLedWidget"

    def group(self):
        return "LinuxCNC - HAL"

    def icon(self):
        return QIcon()

    def toolTip(self):
        return "LED widget used to indicate the state of bool HAL pins."

    def whatsThis(self):
        return "LED widget used to indicate the state of bool HAL pins."

    def isContainer(self):
        return False

    # Returns an XML description of a custom widget instance that describes
    # default values for its properties. Each custom widget created by this
    # plugin will be configured using this description.
    def domXml(self):
        return '''<widget class="HalLedWidget" name="hal_led_2">
         <property name="color">
          <color>
           <red>78</red>
           <green>154</green>
           <blue>6</blue>
          </color>
         </property>
         <property name="state">
          <bool>false</bool>
         </property>
        </widget>'''

    def includeFile(self):
        return "QtPyVCP.widgets.hal_widgets.hal_led_widget"
