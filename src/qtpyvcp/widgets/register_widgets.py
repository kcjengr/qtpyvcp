# # Action Widgets
# #import pydevd; pydevd.settrace()
#
# from button_widgets.action_button import (ActionButton)  # noqa: F401
# from button_widgets.designer_plugins import (ActionButtonPlugin)  # noqa: F401
#
#
# HAL Widgets

from hal_widgets.hal_bar_indicator import (HalBarIndicator)  # noqa: F401
from hal_widgets.hal_button import (HalButton)  # noqa: F401
from hal_widgets.hal_checkbox import (HalCheckBox)  # noqa: F401
from hal_widgets.hal_double_spinbox import (HalDoubleSpinBox)  # noqa: F401
from hal_widgets.hal_groupbox import (HalGroupBox)  # noqa: F401
from hal_widgets.hal_label import (HalLabel)  # noqa: F401
from hal_widgets.hal_lcd import (HalLCDNumber)  # noqa: F401
from hal_widgets.hal_led import (HalLedIndicator)  # noqa: F401
from hal_widgets.hal_led_button import (HALLEDButton)  # noqa: F401
from hal_widgets.hal_plot import (HalPlot)  # noqa: F401
from hal_widgets.hal_slider import (HalSlider)  # noqa: F401
from hal_widgets.hal_spinbox import (HalQSpinBox)  # noqa: F401
from hal_widgets.designer_plugins import (HalLoadMeterPlugin) # noqa: F401




# Input Widgets
from qtpyvcp.widgets.input_widgets.action_combobox import (ActionComboBox)  # noqa: F401
from qtpyvcp.widgets.input_widgets.action_dial import (ActionDial)  # noqa: F401
from qtpyvcp.widgets.input_widgets.action_slider import (ActionSlider)  # noqa: F401
from qtpyvcp.widgets.input_widgets.dro_line_edit import (DROLineEdit)  # noqa: F401
from qtpyvcp.widgets.input_widgets.file_system import (FileSystemTable, RemovableDeviceComboBox)  # noqa: F401
from qtpyvcp.widgets.input_widgets.gcode_text_edit import (GcodeTextEdit)  # noqa: F401
from qtpyvcp.widgets.input_widgets.jog_increment import (JogIncrementWidget)  # noqa: F401
from qtpyvcp.widgets.input_widgets.line_edit import (VCPLineEdit)  # noqa: F401
from qtpyvcp.widgets.input_widgets.mdientry_widget import (MDIEntry)  # noqa: F401
from qtpyvcp.widgets.input_widgets.mdihistory_widget import (MDIHistory)  # noqa: F401
from qtpyvcp.widgets.input_widgets.offset_table import (OffsetTable)  # noqa: F401
from qtpyvcp.widgets.input_widgets.probesim_widget import (ProbeSim)  # noqa: F401
from qtpyvcp.widgets.input_widgets.recent_file_combobox import (RecentFileComboBox)  # noqa: F401

from qtpyvcp.widgets.input_widgets.setting_slider import (VCPSettingsLineEdit,  # noqa: F401
                                                          VCPSettingsSlider,  # noqa: F401
                                                          VCPSettingsSpinBox,  # noqa: F401
                                                          VCPSettingsDoubleSpinBox,  # noqa: F401
                                                          VCPSettingsCheckBox,  # noqa: F401
                                                          VCPSettingsPushButton,  # noqa: F401
                                                          VCPSettingsComboBox)  # noqa: F401





def main():

    from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

    from hal_widgets.designer_plugins import (HalLoadMeterPlugin,
                                              HalButtonPlugin,
                                              HalCheckBoxPlugin,
                                              HalDoubleSpinBoxPlugin,
                                              HalGroupBoxPlugin,
                                              HalLabelPlugin,
                                              HalLCDNumberPlugin,
                                              HalLedIndicatorPlugin,
                                              HalLedButtonPlugin,
                                              HalPlotPlugin,
                                              HalSliderPlugin,
                                              HalQSpinBoxPlugin)

    from qtpyvcp.widgets.input_widgets.designer_plugins import (ActionComboBoxPlugin,
                                                                ActionDialPlugin,
                                                                ActionSliderPlugin,
                                                                DROLineEditPlugin,
                                                                FileSystemPlugin,
                                                                RemovableDeviceComboBoxPlugin,
                                                                GCodeEditPlugin,
                                                                JogIncrementPlugin,
                                                                VCPLineEditPlugin,
                                                                MDIEntryPlugin,
                                                                MDIHistoryPlugin,
                                                                OffsetTablePlugin,
                                                                ProbeSimPlugin,
                                                                RecentFileComboBoxPlugin,
                                                                VCPSettingsLineEditPlugin,
                                                                VCPSettingsSliderPlugin,
                                                                VCPSettingsSpinBoxPlugin,
                                                                VCPSettingsDoubleSpinBoxPlugin,
                                                                VCPSettingsCheckBoxPlugin,
                                                                VCPSettingsPushButtonPlugin,
                                                                VCPSettingsComboBoxPlugin
                                                                )

# Action Widgets
#     QPyDesignerCustomWidgetCollection.addCustomWidget(ActionButtonPlugin())

    # HAL Widgets
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLoadMeterPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(HalCheckBoxPlugin())  # FixMe !! giver error code -6 in designer
    # QPyDesignerCustomWidgetCollection.addCustomWidget(HalDoubleSpinBoxPlugin())  # FixMe !! giver error code -6 in designer
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalGroupBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLabelPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLCDNumberPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLedIndicatorPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalLedButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalPlotPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalSliderPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(HalQSpinBoxPlugin())

    # Input Widgets
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionComboBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionDialPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionSliderPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(DROLineEditPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(FileSystemPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(RemovableDeviceComboBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(GCodeEditPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(JogIncrementPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPLineEditPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(MDIEntryPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(MDIHistoryPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(OffsetTablePlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(ProbeSimPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(RecentFileComboBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsLineEditPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsSliderPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsSpinBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsDoubleSpinBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsCheckBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsPushButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsComboBoxPlugin())

if __name__ == '__main__':
    main()