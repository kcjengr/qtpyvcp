#!/usr/bin/env python
#!/usr/bin/env python

from PyQt5.QtGui import QIcon
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin

from QtPyVCP.widgets.status_widgets.dro_widget import DROWidget

class DROPlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super(DROPlugin, self).__init__(parent)
        self.initialized = False

    def initialize(self, formEditor):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return DROWidget(parent)

    def name(self):
        # Must match widget ClassName
        return "DROWidget"

    def group(self):
        # Group used in QtDesigner widget chooser
        return "LinuxCNC - Status"

    def icon(self):
        # Icon used in QtDesinger widget chooser
        return QIcon()

    def toolTip(self):
        return "Join/Axis Position Readout"

    def whatsThis(self):
        return ""

    def isContainer(self):
        return False

    def domXml(self):
        return '<widget class="DROWidget" name="dro_widget" />\n'

    def includeFile(self):
        return "QtPyVCP.widgets.status_widgets.dro_widget"
