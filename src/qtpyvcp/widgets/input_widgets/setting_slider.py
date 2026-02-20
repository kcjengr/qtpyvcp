from qtpy.QtCore import Property
from qtpy.QtWidgets import QLineEdit, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QPushButton
from qtpy.QtGui import QIntValidator, QDoubleValidator

from qtpyvcp import SETTINGS
from qtpyvcp.widgets import VCPWidget

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

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
            if isinstance(val, int):
                validator = QIntValidator()
            elif isinstance(val, float):
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
        # Always save the format first
        self._text_format = text_fmt
        
        # Validate the format if setting is already available
        if self._setting_name != "":
            setting = SETTINGS.get(self._setting_name)
            if setting:
                try:
                    _ = text_fmt.format(setting.getValue())  # Validate format
                except Exception as e:
                    LOG.warning(f"Invalid textFormat '{text_fmt}' for setting '{self._setting_name}': {e}")


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
    """Settings PushButton with configurable output type and fail-fast validation"""

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
        # Property to control output type
        self._output_as_int = False

    @Property(bool)
    def outputAsInt(self):
        """If True, value() returns 0/1 integers. If False (default), returns True/False booleans."""
        return self._output_as_int

    @outputAsInt.setter
    def outputAsInt(self, use_int):
        self._output_as_int = bool(use_int)

    def setDisplayChecked(self, checked):
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)

    # Provide value() method with configurable output type
    def value(self):
        """Return the current checked state as boolean or integer based on outputAsInt property"""
        checked_state = self.isChecked()
        if self._output_as_int:
            return 1 if checked_state else 0  # Return integer 0/1
        else:
            return checked_state  # Return boolean True/False

    # Provide setValue() method that handles both int and bool inputs
    def setValue(self, value):
        """Set the checked state from a boolean, integer, or compatible value with fail-fast validation"""
        if isinstance(value, bool):
            self.setChecked(value)
        elif isinstance(value, (int, float)):
            # Handle both 0/1 integers and boolean conversion
            self.setChecked(bool(value))
        elif isinstance(value, str):
            # Handle string representations of both boolean and integer values
            value_lower = value.lower()
            if value_lower in ['true', '1', 'yes', 'on']:
                self.setChecked(True)
            elif value_lower in ['false', '0', 'no', 'off']:
                self.setChecked(False)
            else:
                # Fail fast: string must be convertible to integer
                int_value = int(value)  # Let this raise ValueError if invalid
                self.setChecked(bool(int_value))
        else:
            self.setChecked(bool(value))

    # Override text() to return numeric value as string when outputAsInt is enabled
    def text(self):
        """Return string representation of value for parameter collection"""
        if self._output_as_int:
            return str(self.value())  # Returns "0" or "1"
        else:
            # Return the actual button text for normal buttons
            return super(VCPSettingsPushButton, self).text()

    # Settings persistence with proper type handling
    def getSettingsValue(self):
        """Get value for settings persistence using configured output type"""
        return self.value()  # Uses the configurable output type

    def setSettingsValue(self, value):
        """Set value from settings persistence"""
        # Use the setValue method which handles all input types
        self.setValue(value)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:
            self.setEnabled(True)

            value = self._setting.getValue()

            # Convert value to bool for setDisplayChecked
            self.setDisplayChecked(bool(value))
            # Emit the value in the configured output type
            self.toggled.emit(self.value())

            # Use wrapper for settings notification to handle type conversion
            self._setting.notify(lambda v: self.setDisplayChecked(bool(v)))
            # Connect to a wrapper that uses the configured output type
            self.toggled.connect(self._onToggled)

    # Wrapper method to emit the correct value type to settings
    def _onToggled(self, checked):
        """Internal method to emit the correct value type based on outputAsInt property"""
        if self._setting is not None:
            value_to_store = self.value()  # Uses the configurable output type
            self._setting.setValue(value_to_store)


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
