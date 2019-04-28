from qtpyvcp.widgets.qtdesigner import _DesignerPlugin

from qtpyvcp.widgets.utility_widgets.g5x_offset.g5x_handler import G5xOffsetHandler
from qtpyvcp.widgets.utility_widgets.g92_offset.g92_handler import G92OffsetHandler
from qtpyvcp.widgets.utility_widgets.mdi_helper.mdi_handler import MdiHelperHandler


class G5xOffsetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return G5xOffsetHandler


class G92OffsetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return G92OffsetHandler


class MdiHelperPlugin(_DesignerPlugin):
    def pluginClass(self):
        return MdiHelperHandler

