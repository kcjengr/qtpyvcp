from qtpyvcp.widgets.qtdesigner import _DesignerPlugin

from g5x_offset import G5XOffset
class StatusLabelPlugin(_DesignerPlugin):
    def pluginClass(self):
        return StatusLabel
