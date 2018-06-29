#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import DesignerPlugin
from QtPyVCP.widgets.display_widgets.gcode_backplot import GcodeBackplot

class GcodeBackPlotPlugin(DesignerPlugin):

    def pluginClass(self):
        return GcodeBackplot

    def toolTip(self):
        return "G-code backplot widget"
