import os
from PySide6.QtCore import Property
from PySide6.QtWidgets import QLineEdit, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QPushButton
from PySide6.QtGui import QIntValidator, QDoubleValidator

from qtpyvcp import SETTINGS
from qtpyvcp.widgets import VCPWidget

from qtpyvcp.utilities import logger

IN_DESIGNER = os.getenv('DESIGNER', False)
LOG = logger.getLogger(__name__)

class VCPAbstractSettingsWidget(VCPWidget):
    def __init__(self,parent=None):
        super(VCPAbstractSettingsWidget, self).__init__()
        self._setting = None
        self._setting_name = ''

    @Property(str)
    def settingName(self):
        return self._setting_name

    @settingName.setter
    def settingName(self, name):
        self._setting_name = name


class VCPSettingsLineEdit(QLineEdit, VCPAbstractSettingsWidget):
    """Settings LineEdit"""

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractSettingsWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Text': ['setText', str],
        'Value': ['setValue', float],
    })

    def __init__(self, parent):
        super(VCPSettingsLineEdit, self).__init__(parent=parent)
        self._setting_name = ''
        self._text_format = ''
        self._tmp_value = None

        self.returnPressed.connect(self.onReturnPressed)

    def formatValue(self, value):
        if self._setting.value_type in (int, float):
            return self._text_format.format(value)

        if isinstance(value, str):
            return value

        else:
            return str(value)

    def setValue(self, text):
        if self._setting is not None:
            value = self._setting.normalizeValue(text)
            self.setDisplayValue(value)
            self._setting.setValue(value)
        else:
            self._tmp_value = text

    def onReturnPressed(self):
        self.clearFocus()

    def setDisplayValue(self, value):
        self.blockSignals(True)
        self.setText(self.formatValue(value))
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:

            val = self._setting.getValue()

            validator = None
            if type(val) == int:
                validator = QIntValidator()
            elif type(val) == float:
                validator = QDoubleValidator()

            self.setValidator(validator)

            if self._tmp_value:
                self.setDisplayValue(self._tmp_value)
                self._setting.setValue(self._tmp_value)
            else:
                self.setDisplayValue(self._setting.getValue())

            self._setting.notify(self.setDisplayValue)

            self.editingFinished.connect(self.onEditingFinished)

    def onEditingFinished(self):
        value = self._setting.normalizeValue(self.text())
        self.setDisplayValue(value)
        self._setting.setValue(value)

    @Property(str)
    def textFormat(self):
        return self._text_format

    @textFormat.setter
    def textFormat(self, text_fmt):
        if self._setting_name != "":
            setting = SETTINGS.get(self._setting_name)
            if setting:
                try:
                    str = text_fmt.format(setting.getValue())
                except Exception as e:
                    LOG.warning(e)
            else:
                return

        self._text_format = text_fmt


class VCPSettingsSlider(QSlider, VCPAbstractSettingsWidget):
    """Settings Slider

       Set action options like::

           machine.jog.linear-speed

    """

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractSettingsWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Value': ['setValue', int],
    })

    def __init__(self, parent):
        super(VCPSettingsSlider, self).__init__(parent=parent)
        self._setting_name = ''

    def setDisplayValue(self, value):
        self.blockSignals(True)
        self.setValue(int(value))
        self.blockSignals(False)

    def mouseDoubleClickEvent(self, event):
        self.setValue(100)


    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:
            if self._setting.max_value is not None:
                self.setMaximum(int(self._setting.max_value))
            if self._setting.min_value is not None:
                self.setMinimum(int(self._setting.min_value))

            self.setDisplayValue(self._setting.getValue())
            self._setting.notify(self.setDisplayValue)
            self.valueChanged.connect(self._setting.setValue)


class VCPSettingsSpinBox(QSpinBox, VCPAbstractSettingsWidget):
    """Settings SpinBox"""

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractSettingsWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Value': ['setValue', int],
    })

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
                self.setMaximum(int(self._setting.max_value))
            if self._setting.min_value is not None:
                self.setMinimum(int(self._setting.min_value))

            self.setDisplayValue(self._setting.getValue())
            self._setting.notify(self.setDisplayValue)
            self.valueChanged.connect(self._setting.setValue)


class VCPSettingsDoubleSpinBox(QDoubleSpinBox, VCPAbstractSettingsWidget):
    """Settings DoubleSpinBox"""

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractSettingsWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Value': ['setValue', float],
    })

    def __init__(self, parent):
        super(VCPSettingsDoubleSpinBox, self).__init__(parent=parent)

    def setDisplayValue(self, value):
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)

    def editingEnded(self):
        self._setting.setValue(self.value())

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:
            if self._setting.max_value is not None:
                self.setMaximum(self._setting.max_value)
            if self._setting.min_value is not None:
                self.setMinimum(self._setting.min_value)

            self.setDisplayValue(self._setting.getValue())
            self._setting.notify(self.setDisplayValue)
            #self.valueChanged.connect(self._setting.setValue)
            self.editingFinished.connect(self.editingEnded)


class VCPSettingsCheckBox(QCheckBox, VCPAbstractSettingsWidget):
    """Settings CheckBox"""

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractSettingsWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Checked': ['setChecked', bool],
    })

    def __init__(self, parent):
        super(VCPSettingsCheckBox, self).__init__(parent=parent)

    def setDisplayChecked(self, checked):
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:

            value = self._setting.getValue()

            self.setDisplayChecked(value)
            self.toggled.emit(value)

            self._setting.notify(self.setDisplayChecked)
            self.toggled.connect(self._setting.setValue)


class VCPSettingsPushButton(QPushButton, VCPAbstractSettingsWidget):
    """Settings PushButton"""

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = VCPAbstractSettingsWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Text': ['setText', str],
        'Checked': ['setChecked', bool],
    })

    def __init__(self, parent):
        super(VCPSettingsPushButton, self).__init__(parent=parent)
        self.setCheckable(True)
        self.setEnabled(False)

    def setDisplayChecked(self, checked):
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:
            self.setEnabled(True)

            value = self._setting.getValue()

            self.setDisplayChecked(value)
            self.toggled.emit(value)

            self._setting.notify(self.setDisplayChecked)
            self.toggled.connect(self._setting.setValue)


class VCPSettingsComboBox(QComboBox, VCPAbstractSettingsWidget):
    """Settings ComboBox"""

    DEFAULT_RULE_PROPERTY = 'Enable'

    def __init__(self, parent):
        super(VCPSettingsComboBox, self).__init__(parent=parent)

    def setDisplayIndex(self, index):
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:

            value = self._setting.getValue()

            options = self._setting.enum_options
            if isinstance(options, list):
                for option in options:
                    self.addItem(option)

            self.setDisplayIndex(value)
            self.currentIndexChanged.emit(value)

            self._setting.notify(self.setDisplayIndex)
            self.currentIndexChanged.connect(self._setting.setValue)
