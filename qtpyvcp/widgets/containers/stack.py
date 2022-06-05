
from qtpy.QtCore import Property
from qtpy.QtWidgets import QStackedWidget

from qtpyvcp import SETTINGS
from qtpyvcp.widgets.base_widgets import VCPWidget


class VCPAbstractStackedWidget(VCPWidget):
    def __init__(self):
        super(VCPAbstractStackedWidget, self).__init__()
        self._setting = None
        self._setting_name = ''

    @Property(str)
    def settingName(self):
        return self._setting_name

    @settingName.setter
    def settingName(self, name):
        self._setting_name = name


class VCPStackedWidget(QStackedWidget, VCPAbstractStackedWidget):
    """VCPStackedWidget

    VCP Stacked Widget

    A widget Stack that can be controlled via rules.
    """
    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractStackedWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'currentIndex': ['setIndexValue', int],
    })

    def __init__(self, parnet):
        super(VCPStackedWidget, self).__init__(parent=parnet)

    def setIndexValue(self, value):
        self.blockSignals(True)
        self.setCurrentIndex(value)
        self.blockSignals(False)
