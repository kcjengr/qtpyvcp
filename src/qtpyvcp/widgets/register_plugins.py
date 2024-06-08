#
# from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow  # noqa: F401
# from qtpyvcp.widgets.form_widgets.probe_widget.probe import SubCaller  # noqa: F401
#
# from qtpyvcp.widgets.button_widgets.action_button import ActionButton  # noqa: F401
# from qtpyvcp.widgets.button_widgets.action_checkbox import ActionCheckBox  # noqa: F401
# from qtpyvcp.widgets.button_widgets.action_spinbox import ActionSpinBox  # noqa: F401
# from qtpyvcp.widgets.button_widgets.dialog_button import DialogButton  # noqa: F401
# from qtpyvcp.widgets.button_widgets.led_button import LEDButton  # noqa: F401
# from qtpyvcp.widgets.button_widgets.mdi_button import MDIButton  # noqa: F401
# from qtpyvcp.widgets.button_widgets.subcall_button import SubCallButton  # noqa: F401
#
# from qtpyvcp.widgets.input_widgets.tool_table import ToolTable  # noqa: F401

from qtpyvcp.widgets.form_widgets.designer_plugins import (MainWindowPlugin,
                                                           ProbePlugin)

from qtpyvcp.widgets.button_widgets.designer_plugins import (ActionButtonPlugin,
                                                             ActionCheckBoxPlugin,
                                                             ActionSpinBoxPlugin,
                                                             DialogButtonPlugin,
                                                             LedButtonPlugin,
                                                             MacroButtonPlugin,
                                                             MDIButtonPlugin)


# from qtpyvcp.widgets.display_widgets.designer_plugins import *
from qtpyvcp.widgets.input_widgets.designer_plugins import (ToolTablePlugin)
# from qtpyvcp.widgets.hal_widgets.designer_plugins import *
# from qtpyvcp.widgets.containers.designer_plugins import *
# from qtpyvcp.widgets.db_widgets.designer_plugins import *
#
# from qtpyvcp.widgets.external_widgets import *
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection


if __name__ == '__main__':

    print("Register Plugins")
    QPyDesignerCustomWidgetCollection.addCustomWidget(MainWindowPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ProbePlugin())
    #
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ActionButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ActionCheckBoxPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ActionSpinBoxPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(DialogButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(LedButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(MacroButtonPlugin())
    # QPyDesignerCustomWidgetCollection.addCustomWidget(MDIButtonPlugin())
    #
    # QPyDesignerCustomWidgetCollection.addCustomWidget(ToolTablePlugin())
