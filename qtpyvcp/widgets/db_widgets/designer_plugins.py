from qtpyvcp.widgets.qtdesigner import _DesignerPlugin
from qtpyvcp.widgets.qtdesigner.designer_plugin import RulesEditorExtension

from qtpyvcp.widgets.db_widgets.tool_model import ToolSTLField

class ToolSTLFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ToolSTLField