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


from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLoadMeterPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalButtonPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalCheckBoxPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalDoubleSpinBoxPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalGroupBoxPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLabelPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLCDNumberPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLedIndicatorPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLedButtonPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalPlotPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalSliderPlugin)
from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalQSpinBoxPlugin)

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

