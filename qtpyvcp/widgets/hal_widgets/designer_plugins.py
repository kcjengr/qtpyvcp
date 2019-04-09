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

from qtpyvcp.widgets.hal_widgets.hal_led_widget import HalLedWidget
class HalLedPlugin(_DesignerPlugin):
    def pluginClass(self):
        return HalLedWidget
    def toolTip(self):
        return "LED widget used to indicate the state of bool HAL pins."
    def domXml(self):
        return '''<widget class="HalLedWidget" name="hal_led">
                   <property name="color">
                    <color>
                     <red>78</red>
                     <green>154</green>
                     <blue>6</blue>
                    </color>
                   </property>
                   <property name="state">
                    <bool>false</bool>
                   </property>
                  </widget>'''
