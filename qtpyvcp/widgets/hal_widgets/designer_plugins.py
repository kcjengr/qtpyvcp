from qtpyvcp.widgets.qtdesigner import _DesignerPlugin

from hal_checkbox import HalCheckBox
class HalCheckBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalCheckBox

from hal_spinbox import HalQSpinBox
class HalQSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalQSpinBox

from hal_double_spinbox import HalDoubleSpinBox
class HalDoubleSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalDoubleSpinBox

from qtpyvcp.widgets.hal_widgets.hal_led import HalLedIndicator
class HalLedIndicatorPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalLedIndicator

from qtpyvcp.widgets.hal_widgets.hal_label import HalLabel
class HalLabelPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalLabel

from qtpyvcp.widgets.hal_widgets.hal_slider import HalSlider
class HalSliderPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalSlider

from qtpyvcp.widgets.hal_widgets.hal_button import HalButton
class HalButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalButton

from qtpyvcp.widgets.hal_widgets.hal_lcd import HalLCDNumber
class HalLCDNumberPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalLCDNumber

from qtpyvcp.widgets.hal_widgets.hal_groupbox import HalGroupBox
class HalGroupBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalGroupBox
    def isContainer(self):
        return True

from qtpyvcp.widgets.hal_widgets.hal_plot import HalPlot
class HalPlotPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalPlot