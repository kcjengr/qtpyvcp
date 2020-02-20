

from qtpy.QtWidgets import QStackedWidget
from qtpyvcp.widgets.base_widgets import VCPWidget


class VCPStackedWidget(QStackedWidget, VCPWidget):
    """VCPStackedWidget

    VCP Stacked Widget

    A widget Stack that can be controlled via rules.
    """
    DEFAULT_RULE_PROPERTY = 'Enable'

    def __init__(self, parnet):
        super(VCPStackedWidget, self).__init__(parent=parnet)

