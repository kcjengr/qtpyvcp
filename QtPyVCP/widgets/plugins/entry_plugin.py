#!/usr/bin/env python

from PyQt5.QtGui import QIcon
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin

from QtPyVCP.widgets.entry_widget import EntryWidget

class EntryPlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super(EntryPlugin, self).__init__(parent)
        self.initialized = False

    def initialize(self, formEditor):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return EntryWidget(parent)

    def name(self):
        return "EntryWidget"

    def group(self):
        return "LinuxCNC - Controller"

    def icon(self):
        return QIcon()

    def toolTip(self):
        return "MDI edit line Widget"

    def whatsThis(self):
        return ""

    def isContainer(self):
        return True

    def domXml(self):
        return '<widget class="EntryWidget" name="lcnc_mdiline" />\n'

    def includeFile(self):
        return "QtPyVCP.widgets.entry_widget"
