"""
Bar Indicator
-------------
"""

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.widgets.base_widgets.bar_indicator import BarIndicatorBase

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)


class BarIndicator(BarIndicatorBase, VCPWidget):
    """General purpose bars style indicator.

    Args:
        parent (QWidget) : The parent widget, or None.
    """

    DEFAULT_RULE_PROPERTY = 'Value'
    RULE_PROPERTIES = VCPWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Value': ['setValue', int],
    })

    def __init__(self, parent=None):
        super(BarIndicator, self).__init__(parent)
