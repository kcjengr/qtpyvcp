#!/usr/bin/python2

from PyQt5.QtGui import QIcon
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin

from QtPyVCP.widgets.led_widget import LEDWidget

class LedPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent=None):
        super(LedPlugin, self).__init__(parent)

        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return

        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return LEDWidget(parent)

    def name(self):
        return "LEDWidget"

    def group(self):
        return "LinuxCNC - Status"

    def icon(self):
        return QIcon()

    def toolTip(self):
        return ""

    def whatsThis(self):
        return ""

    def isContainer(self):
        return False

    # Returns an XML description of a custom widget instance that describes
    # default values for its properties. Each custom widget created by this
    # plugin will be configured using this description.
    def domXml(self):
        return '<widget class="LEDWidget" name="ledWidget">\n' \
               ' <property name="toolTip">\n' \
               '  <string>The current time</string>\n' \
               ' </property>\n' \
               ' <property name="whatsThis">\n' \
               '  <string>The analog clock widget displays the current ' \
               'time.</string>\n' \
               ' </property>\n' \
               '</widget>\n'

    def includeFile(self):
        return "QtPyVCP.widgets.led_widget"
