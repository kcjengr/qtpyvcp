#import pydevd; pydevd.settrace()

from qtpyvcp.widgets.button_widgets.action_button import (ActionButton)  # noqa: F401
from qtpyvcp.widgets.button_widgets.action_checkbox import (ActionCheckBox)
from qtpyvcp.widgets.button_widgets.action_spinbox import (ActionSpinBox)
from qtpyvcp.widgets.button_widgets.dialog_button import (DialogButton)
from qtpyvcp.widgets.button_widgets.led_button import (LEDButton)
from qtpyvcp.widgets.button_widgets.mdi_button import (MDIButton)
from qtpyvcp.widgets.button_widgets.subcall_button import (SubCallButton)

from qtpyvcp.widgets.button_widgets.designer_plugins import (ActionButtonPlugin)
from qtpyvcp.widgets.button_widgets.designer_plugins import (ActionCheckBoxPlugin)
from qtpyvcp.widgets.button_widgets.designer_plugins import (ActionSpinBoxPlugin)
from qtpyvcp.widgets.button_widgets.designer_plugins import (MacroButtonPlugin)
from qtpyvcp.widgets.button_widgets.designer_plugins import (LedButtonPlugin)
from qtpyvcp.widgets.button_widgets.designer_plugins import (MDIButtonPlugin)
from qtpyvcp.widgets.button_widgets.designer_plugins import (DialogButtonPlugin)

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

if __name__ == '__main__':
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionCheckBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(ActionSpinBoxPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(MacroButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(LedButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(MDIButtonPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(DialogButtonPlugin())