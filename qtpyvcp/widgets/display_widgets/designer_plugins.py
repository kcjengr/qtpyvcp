#!/usr/bin/env python

from qtpyvcp.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from status_label import StatusLabel
class StatusLabelPlugin(_DesignerPlugin):
    def pluginClass(self):
        return StatusLabel

from dro_widget import DROWidget
class DROPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DROWidget

from gcode_backplot.gcode_backplot import GcodeBackplot
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

from load_meter import LoadMeter
class LoadMeterPlugin(_DesignerPlugin):
    def pluginClass(self):
        return LoadMeter
