from qtpyvcp.widgets.qtdesigner import _DesignerPlugin
from qtpyvcp.widgets.qtdesigner.designer_plugin import RulesEditorExtension


from qtpyvcp.widgets.db_widgets.tool_fields import DBFileField
from qtpyvcp.widgets.db_widgets.tool_fields import DBTextField
from qtpyvcp.widgets.db_widgets.tool_fields import DBCheckBoxField
from qtpyvcp.widgets.db_widgets.tool_fields import DBIntField
from qtpyvcp.widgets.db_widgets.tool_fields import DBFloatField


class DBFileFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DBFileField
    

class DBTextFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DBTextField


class DBCheckBoxFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DBCheckBoxField


class DBFloatFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DBFloatField