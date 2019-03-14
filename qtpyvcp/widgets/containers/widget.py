"""
VCP Widget Container
--------------------

A widget container that can be controlled via rules.
"""

from qtpy.QtWidgets import QWidget
from qtpyvcp.widgets.base_widgets import VCPWidget


class VCPWidget(QWidget, VCPWidget):
    """VCPWidget"""

    DEFAULT_RULE_PROPERTY = 'Enable'

    def __init__(self, parnet):
        super(VCPWidget, self).__init__(parent=parnet)

