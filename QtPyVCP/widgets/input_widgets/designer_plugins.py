#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import _DesignerPlugin

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


from override_slider import OverrideSlider


class OverrideSliderPlugin(_DesignerPlugin):
    def pluginClass(self):
        return OverrideSlider


from tool_table import ToolTable


class ToolTablePlugin(_DesignerPlugin):
    def pluginClass(self):
        return ToolTable

from jog_increment import JogIncrementWidget
class JogIncrementPlugin(_DesignerPlugin):
    def pluginClass(self):
        return JogIncrementWidget

from console_widget.wrapper import Wrapper

class PythonInterpreterPlugin(_DesignerPlugin):
    def pluginClass(self):
        return Wrapper