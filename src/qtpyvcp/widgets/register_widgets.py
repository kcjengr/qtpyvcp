#import pydevd; pydevd.settrace()

# Button Widgets

from qtpyvcp.widgets.button_widgets.action_button import (ActionButton)  # noqa: F401
from qtpyvcp.widgets.button_widgets.action_checkbox import (ActionCheckBox)  # noqa: F401
from qtpyvcp.widgets.button_widgets.action_spinbox import (ActionSpinBox)  # noqa: F401
from qtpyvcp.widgets.button_widgets.subcall_button import (SubCallButton)  # noqa: F401
from qtpyvcp.widgets.button_widgets.led_button import (LEDButton)  # noqa: F401
from qtpyvcp.widgets.button_widgets.mdi_button import (MDIButton)  # noqa: F401
from qtpyvcp.widgets.button_widgets.dialog_button import (DialogButton)  # noqa: F401


# Tool Database fields
from qtpyvcp.widgets.db_widgets.tool_model import (ToolSTLField)  # noqa: F401

# Display Widgets

from qtpyvcp.widgets.display_widgets.bar_indicator import (BarIndicator)  # noqa: F401
from qtpyvcp.widgets.display_widgets.dro_label import (DROLabel)  # noqa: F401
from qtpyvcp.widgets.display_widgets.gcode_properties import (GCodeProperties)  # noqa: F401
from qtpyvcp.widgets.display_widgets.notification_widget import (NotificationWidget)  # noqa: F401
from qtpyvcp.widgets.display_widgets.status_label import (StatusLabel)  # noqa: F401
from qtpyvcp.widgets.display_widgets.status_led import (StatusLED)  # noqa: F401
from qtpyvcp.widgets.display_widgets.vtk_backplot.vtk_backplot import (VTKBackPlot)  # noqa: F401

# HAL Widgets

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

# Settings Widgets
from qtpyvcp.widgets.input_widgets.setting_slider import (VCPSettingsLineEdit,  # noqa: F401
                                                          VCPSettingsSlider,  # noqa: F401
                                                          VCPSettingsSpinBox,  # noqa: F401
                                                          VCPSettingsDoubleSpinBox,  # noqa: F401
                                                          VCPSettingsCheckBox,  # noqa: F401
                                                          VCPSettingsPushButton,  # noqa: F401
                                                          VCPSettingsComboBox)  # noqa: F401





def main():

    from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
    
    print("DEBUG: register_widgets.main() called", flush=True)

    # Action Buttons
    from qtpyvcp.widgets.button_widgets.designer_plugins import (ActionButtonPlugin,
                                                 ActionCheckBoxPlugin,
                                                 ActionSpinBoxPlugin,
                                                 MacroButtonPlugin,
                                                 LedButtonPlugin,
                                                 MDIButtonPlugin,
                                                 DialogButtonPlugin)
    # Tool Database Widgets
    from qtpyvcp.widgets.db_widgets.designer_plugins import (ToolSTLFieldPlugin)

    # Display Widgets
    from qtpyvcp.widgets.display_widgets.designer_plugins import (StatusLabelPlugin,
                                                                  DROLabel_Plugin,
                                                                  BarIndicatorPlugin,
                                                                  StatusLEDPlugin,
                                                                  VTKWidgetPlugin,
                                                                  NotificationPlugin,
                                                                  GcodeReferenceTablePlugin,
                                                                  GCodePropertiesPlugin)
    # HAL Widgets
    from qtpyvcp.widgets.hal_widgets.designer_plugins import (HalLoadMeterPlugin,
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
    
    # Input Widgets
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

    # Button Widgets
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionCheckBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionSpinBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(MacroButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(LedButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(MDIButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(DialogButtonPlugin())

    # Tool database Widgets
    QPyDesignerCustomWidgetCollection.addCustomWidget(ToolSTLFieldPlugin())

    # Display Widgets

    QPyDesignerCustomWidgetCollection.addCustomWidget(StatusLabelPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(DROLabel_Plugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(BarIndicatorPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(StatusLEDPlugin())
    
    # VTK Widget - may have metaclass conflicts in designer, so skip on error
    try:
        QPyDesignerCustomWidgetCollection.addCustomWidget(VTKWidgetPlugin())
    except Exception as e:
        print(f"Warning: Could not load VTK widget plugin: {e}")
        print("VTK widget will not be available in designer")
    
    QPyDesignerCustomWidgetCollection.addCustomWidget(NotificationPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(GcodeReferenceTablePlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(GCodePropertiesPlugin())

    
    # HAL Widgets
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
    
    # Settings Widgets
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsLineEditPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsSliderPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsSpinBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsDoubleSpinBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsCheckBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsPushButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VCPSettingsComboBoxPlugin())
    
    print("DEBUG: All QtPyVCP custom widgets registered successfully", flush=True)

if __name__ == '__main__':
    main()