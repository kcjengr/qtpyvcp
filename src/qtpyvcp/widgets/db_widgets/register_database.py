from qtpyvcp.widgets.db_widgets.tool_model import (ToolSTLField)  # noqa: F401

from qtpyvcp.widgets.button_widgets.designer_plugins import (ToolSTLFieldPlugin)

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

if __name__ == '__main__':
    QPyDesignerCustomWidgetCollection.addCustomWidget(ToolSTLFieldPlugin())
