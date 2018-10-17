#!/usr/bin/env python

from qtpyvcp.widgets.qtdesigner import _DesignerPlugin

from mdientry_widget import MDIEntry
class MDIEntryPlugin(_DesignerPlugin):
    def pluginClass(self):
        return MDIEntry

    def toolTip(self):
        return "MDI command entry"

from gcode_editor import GcodeEditor
class GcodeEditorPlugin(_DesignerPlugin):
    def pluginClass(self):
        return GcodeEditor

from recent_file_combobox import RecentFileComboBox
class RecentFileComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return RecentFileComboBox

from tool_table import ToolTable
class ToolTablePlugin(_DesignerPlugin):
    def pluginClass(self):
        return ToolTable

from jog_increment import JogIncrementWidget
class JogIncrementPlugin(_DesignerPlugin):
    def pluginClass(self):
        return JogIncrementWidget

from file_system import FileSystemTable
class FileSystemPlugin(_DesignerPlugin):
    def pluginClass(self):
        return FileSystemTable

from file_system import RemovableDeviceComboBox
class RemovableDeviceComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return RemovableDeviceComboBox

from action_slider import ActionSlider
class ActionSliderPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionSlider

from action_combobox import ActionComboBox
class ActionComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionComboBox
