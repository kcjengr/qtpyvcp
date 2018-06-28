#!/usr/bin/env python

from PyQt5 import QtCore, QtGui
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from QtPyVCP.widgets.status_widgets.gcode_backplot import GcodeBackplot

class  GcodeBackPlotPlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent = None):
        super(GcodeBackPlotPlugin, self).__init__(parent)
        self.initialized = False

    def initialize(self, formEditor):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return GcodeBackplot(parent)

    def name(self):
        return "GcodeBackplot"

    def group(self):
        return "LinuxCNC - Status"

    def icon(self):
        return QtGui.QIcon() #QtGui.QIcon(QtGui.QPixmap(ICON.get_path('gcodegraphics')))

    def toolTip(self):
        return "G-code backplot widget"

    def whatsThis(self):
        return ""

    def isContainer(self):
        return True

    def domXml(self):
        return '<widget class="GcodeBackplot" name="gcode_backplot" />\n'

    def includeFile(self):
        return "QtPyVCP.widgets.status_widgets.gcode_backplot"
