from qtpyvcp.widgets.display_widgets.bar_indicator import (BarIndicator)  # noqa: F401
from qtpyvcp.widgets.display_widgets.dro_label import (DROLabel)
from qtpyvcp.widgets.display_widgets.gcode_properties import (GCodeProperties)
from qtpyvcp.widgets.display_widgets.notification_widget import (NotificationWidget)
from qtpyvcp.widgets.display_widgets.status_label import (StatusLabel)
from qtpyvcp.widgets.display_widgets.status_led import (StatusLED)
from qtpyvcp.widgets.display_widgets.vtk_backplot.vtk_backplot import (VTKBackPlot)

from qtpyvcp.widgets.display_widgets.designer_plugins import (StatusLabelPlugin)
from qtpyvcp.widgets.display_widgets.designer_plugins import (DROLabel_Plugin)
from qtpyvcp.widgets.display_widgets.designer_plugins import (BarIndicatorPlugin)
from qtpyvcp.widgets.display_widgets.designer_plugins import (StatusLEDPlugin)
from qtpyvcp.widgets.display_widgets.designer_plugins import (VTKWidgetPlugin)
from qtpyvcp.widgets.display_widgets.designer_plugins import (NotificationPlugin)
from qtpyvcp.widgets.display_widgets.designer_plugins import (GcodeReferenceTable_Plugin)
from qtpyvcp.widgets.display_widgets.designer_plugins import (GCodeProperties_Plugin)

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

if __name__ == '__main__':
    QPyDesignerCustomWidgetCollection.addCustomWidget(StatusLabelPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(DROLabel_Plugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(BarIndicatorPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(StatusLEDPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(VTKWidgetPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(NotificationPlugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(GcodeReferenceTable_Plugin())
    QPyDesignerCustomWidgetCollection.addCustomWidget(GCodeProperties_Plugin())
    