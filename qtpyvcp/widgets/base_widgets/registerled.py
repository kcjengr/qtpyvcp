from qtpyvcp.widgets.base_widgets.led_widget import LEDWidget
from qtpyvcp.widgets.base_widgets.ledplugin import LEDWidgetPlugin

from PySide2.QtDesigner import QPyDesignerCustomWidgetCollection

# Set PYSIDE_DESIGNER_PLUGINS to point to this directory and load the plugin


if __name__ == '__main__':
    QPyDesignerCustomWidgetCollection.addCustomWidget(LEDWidgetPlugin())
