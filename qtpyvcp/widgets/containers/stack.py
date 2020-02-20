
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


class VCPStackedWidget(QStackedWidget, VCPWidget):
    """VCPStackedWidget

    VCP Stacked Widget

    A widget Stack that can be controlled via rules.
    """
    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractStackedWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'currentIndex': ['setValue', int],
    })

    def __init__(self, parnet):
        super(VCPStackedWidget, self).__init__(parent=parnet)

    def setIndexValue(self, value):
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:
            if self._setting.max_value is not None:
                self.setMaximum(self._setting.max_value)
            if self._setting.min_value is not None:
                self.setMinimum(self._setting.min_value)

            self.setIndexValue(self._setting.getValue())
            self._setting.notify(self.setIndexValue)
            self.valueChanged.connect(self._setting.setValue)
