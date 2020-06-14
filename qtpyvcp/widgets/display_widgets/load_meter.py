# for backward compatibility with older VCPs
from qtpyvcp.lib.decorators import deprecated
from bar_indicator import BarIndicator


@deprecated(reason="new base class implementation", replaced_by="BarIndicator")
class LoadMeter(BarIndicator):
    def __init__(self, parent=None):
        super(LoadMeter, self).__init__(parent=parent)
