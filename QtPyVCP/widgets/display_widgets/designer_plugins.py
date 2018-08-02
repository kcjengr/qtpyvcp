#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import _DesignerPlugin

from dro_widget import DROWidget
class DROPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DROWidget

from gcode_backplot import GcodeBackplot
class GcodeBackPlotPlugin(_DesignerPlugin):
    def pluginClass(self):
        return GcodeBackplot
    def toolTip(self):
        return "G-code backplot widget"
    def isContainer(self):
        return True

from camera.camera import Camera
class CameraPlugin(_DesignerPlugin):
    def pluginClass(self):
        return Camera
    def toolTip(self):
        return "Camera widget"
    def isContainer(self):
        return True
