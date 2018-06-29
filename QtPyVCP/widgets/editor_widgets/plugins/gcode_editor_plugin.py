#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import DesignerPlugin
from QtPyVCP.widgets.editor_widgets.gcode_editor import GcodeEditor

class GcodeEditorPlugin(DesignerPlugin):

    def pluginClass(self):
        return GcodeEditor
