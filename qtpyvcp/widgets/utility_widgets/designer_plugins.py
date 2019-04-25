from qtpyvcp.widgets.qtdesigner import _DesignerPlugin

from g5x_offset.g5x_handler import G5xOffsetHandler
from g92_offset.g92_handler import G92OffsetHandler


class G5xOffsetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return G5xOffsetHandler


class G92OffsetPlugin(_DesignerPlugin):
    def pluginClass(self):
        return G92OffsetHandler
