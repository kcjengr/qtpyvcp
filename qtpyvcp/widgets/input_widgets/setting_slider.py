from qtpy.QtCore import Property
from qtpy.QtWidgets import QSlider, QSpinBox, QDoubleSpinBox, QCheckBox

from qtpyvcp import SETTINGS
from qtpyvcp.widgets import VCPWidget


class VCPAbstractSettingsWidget(VCPWidget):
    def __init__(self):
        super(VCPAbstractSettingsWidget, self).__init__()
        self._setting = None
        self._setting_name = ''

    @Property(str)
    def settingName(self):
        return self._setting_name

    @settingName.setter
    def settingName(self, name):
        self._setting_name = name


class VCPSettingsSlider(QSlider, VCPAbstractSettingsWidget):
    """Settings Slider"""
    def __init__(self, parent):
        super(VCPSettingsSlider, self).__init__(parent=parent)
        self._setting_name = ''

    def setDisplayValue(self, value):
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

            self.setDisplayValue(self._setting.getValue())
            self._setting.notify(self.setDisplayValue)
            self.valueChanged.connect(self._setting.setValue)


class VCPSettingsSpinBox(QSpinBox, VCPAbstractSettingsWidget):
    """Settings SpinBox"""
    def __init__(self, parent):
        super(VCPSettingsSpinBox, self).__init__(parent=parent)

    def setDisplayValue(self, value):
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

            self.setDisplayValue(self._setting.getValue())
            self._setting.notify(self.setDisplayValue)
            self.valueChanged.connect(self._setting.setValue)


class VCPSettingsDoubleSpinBox(QDoubleSpinBox, VCPAbstractSettingsWidget):
    """Settings DoubleSpinBox"""
    def __init__(self, parent):
        super(VCPSettingsDoubleSpinBox, self).__init__(parent=parent)

    def setDisplayValue(self, value):
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

            self.setDisplayValue(self._setting.getValue())
            self._setting.notify(self.setDisplayValue)
            self.valueChanged.connect(self._setting.setValue)


class VCPSettingsCheckBox(QCheckBox, VCPAbstractSettingsWidget):
    """Settings CheckBox"""
    def __init__(self, parent):
        super(VCPSettingsCheckBox, self).__init__(parent=parent)

    def setDisplayChecked(self, checked):
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:
            self.setDisplayChecked(self._setting.getValue())

            self._setting.notify(self.setDisplayChecked)
            self.toggled.connect(self._setting.setValue)
