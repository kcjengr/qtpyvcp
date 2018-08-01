#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import _DesignerPlugin

from gcode_editor import GcodeEditor
class GcodeEditorPlugin(_DesignerPlugin):
    def pluginClass(self):
        return GcodeEditor

from recent_file_combobox import RecentFileComboBox
class RecentFileComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return RecentFileComboBox
