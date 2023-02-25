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
    RULE_PROPERTIES = VCPWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'On': ['setState', bool],
        'Flashing': ['setFlashing', bool],
    })

    def __init__(self, parent=None):
        super(StatusLED, self).__init__(parent)

