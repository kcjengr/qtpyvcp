from qtpyvcp.widgets.hal_widgets.hal_bar_indicator import (HalBarIndicator)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_button import (HalButton)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_checkbox import (HalCheckBox)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_double_spinbox import (HalDoubleSpinBox)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_groupbox import (HalGroupBox)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_label import (HalLabel)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_lcd import (HalLCDNumber)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_led import (HalLedIndicator)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_led_button import (HALLEDButton)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_plot import (HalPlot)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_slider import (HalSlider)  # noqa: F401
from qtpyvcp.widgets.hal_widgets.hal_spinbox import (HalQSpinBox)  # noqa: F401


from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLoadMeterPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalButtonPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalCheckBoxPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalDoubleSpinBoxPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalGroupBoxPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLabelPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLCDNumberPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLedIndicatorPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLedButtonPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalPlotPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalSliderPlugin) # noqa: F401
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalQSpinBoxPlugin) # noqa: F401

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection



if __name__ == '__main__':

    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLoadMeterPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalCheckBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalDoubleSpinBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalGroupBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLabelPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLCDNumberPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLedIndicatorPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLedButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalPlotPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalSliderPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalQSpinBoxPlugin())

