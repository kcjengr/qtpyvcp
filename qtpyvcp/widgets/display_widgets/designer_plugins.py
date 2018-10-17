#!/usr/bin/env python

from qtpyvcp.widgets.qtdesigner import _DesignerPlugin, _PluginExtension

from status_label import StatusLabel
class StatusLabelPlugin(_DesignerPlugin):
    def pluginClass(self):
        return StatusLabel
    def extensions(self):
        return [StatusLablePluginExtension,]

from qtpyvcp.widgets.qtdesigner.widget_rules_editor import RulesEditor
class StatusLablePluginExtension(_PluginExtension):
    def __init__(self, widget):
        super(StatusLablePluginExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Edit Widget Rules...", self.editAction)

    def editAction(self, state):
        RulesEditor(self.widget, parent=None).exec_()

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

from load_meter import LoadMeter
class LoadMeterPlugin(_DesignerPlugin):
    def pluginClass(self):
        return LoadMeter
