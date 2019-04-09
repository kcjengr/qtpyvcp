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

from qtpyvcp.widgets.hal_widgets.hal_s32_dro import Hals32Dro
class Hals32DroPlugin(_DesignerPlugin):
    def pluginClass(self):
        return Hals32Dro

from qtpyvcp.widgets.hal_widgets.hal_u32_dro import Halu32Dro
class Halu32DroPlugin(_DesignerPlugin):
    def pluginClass(self):
        return Halu32Dro

from qtpyvcp.widgets.hal_widgets.hal_float_dro import HalFloatDro
class HalFloatDroPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalFloatDro