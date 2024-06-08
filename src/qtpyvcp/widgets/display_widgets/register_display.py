from qtpyvcp.widgets.display_widgets.bar_indicator import (BarIndicator)  # noqa: F401
from qtpyvcp.widgets.display_widgets.designer_plugins import (BarIndicatorPlugin)

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

if __name__ == '__main__':
    QPyDesignerCustomWidgetCollection.addCustomWidget(BarIndicatorPlugin())
