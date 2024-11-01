from qtpyvcp.widgets.qtdesigner import _DesignerPlugin
from qtpyvcp.widgets.qtdesigner.designer_plugin import RulesEditorExtension


from qtpyvcp.widgets.db_widgets.tool_fields import DBToolSTLField

class DBToolSTLFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DBToolSTLField
    
    
from qtpyvcp.widgets.db_widgets.tool_fields import DBTextField

class DBTextFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DBTextField
    
    
from qtpyvcp.widgets.db_widgets.tool_fields import DBCheckBoxField

class DBCheckBoxFieldPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DBCheckBoxField