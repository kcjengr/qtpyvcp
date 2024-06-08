from qtpyvcp.widgets.button_widgets.action_button import (ActionButton)  # noqa: F401
from qtpyvcp.widgets.button_widgets.designer_plugins import (ActionButtonPlugin)

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

if __name__ == '__main__':
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionButtonPlugin())
