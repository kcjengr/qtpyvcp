"""
LED Indicator
-------------
"""

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.widgets.base_widgets.led_widget import LEDWidget


class StatusLED(LEDWidget, VCPWidget):
    """General purpose LED style indicator.

    Args:
        parent (QWidget) : The parent widget, or None.
    """

    DEFAULT_RULE_PROPERTY = 'On'
    RULE_PROPERTIES = {
        'On': ['setState', bool],
        'Flashing': ['setFlashing', bool],
        'Visible': ['setVisible', bool],
        'Opacity': ['setOpacity', float],
    }

    def __init__(self, parent=None):
        super(StatusLED, self).__init__(parent)

