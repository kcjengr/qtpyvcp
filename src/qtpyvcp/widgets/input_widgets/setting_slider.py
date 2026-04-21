import os
from PySide6.QtCore import Property, QLocale
from PySide6.QtWidgets import QLineEdit, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QPushButton
from PySide6.QtGui import QIntValidator, QDoubleValidator

from qtpyvcp import SETTINGS
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities.qt_safety import safe_qt_callback
from qtpyvcp.utilities.misc import cnc_float

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
        self._setting_type_mode = 'auto'
        self._tmp_value = None
        self._high_precision_storage = False
        self._internal_value = None
        self._display_decimals = 4

        self.returnPressed.connect(self.onReturnPressed)

    def _normalize_setting_type_mode(self, mode):
        mode = (mode or 'auto').strip().lower()
        if mode in ('auto', 'float', 'int', 'text'):
            return mode
        LOG.warning("Invalid settingTypeMode '%s'; using 'auto'", mode)
        return 'auto'

    def _mode_value_type(self):
        if self._setting_type_mode == 'float':
            return float
        if self._setting_type_mode == 'int':
            return int
        if self._setting_type_mode == 'text':
            return str
        return None

    def _effective_value_type(self):
        mode_type = self._mode_value_type()

        setting_type = None
        if self._setting is not None:
            setting_type = self._setting.value_type
            if setting_type not in (int, float, str):
                setting_type = str

        # When a setting is bound, prefer its declared type for safety.
        if setting_type is not None:
            if mode_type is not None and mode_type is not setting_type:
                LOG.warning(
                    "settingTypeMode '%s' conflicts with setting '%s' type '%s'; using setting type",
                    self._setting_type_mode,
                    self._setting_name,
                    setting_type.__name__,
                )
            return setting_type

        if mode_type is not None:
            return mode_type

        # In auto mode without a bound setting, treat 0 decimals as integer mode.
        return int if self._display_decimals == 0 else float

    @Property(str)
    def settingTypeMode(self):
        """Type hint for Designer/runtime behavior: auto, float, int, or text."""
        return self._setting_type_mode

    @settingTypeMode.setter
    def settingTypeMode(self, mode):
        self._setting_type_mode = self._normalize_setting_type_mode(mode)
        if self._setting is not None:
            self.setDisplayValue(self._setting.getValue())

    def _format_numeric_value(self, numeric):
        """Format numeric values from displayDecimals only (single source of truth)."""
        return f"{numeric:.{self._display_decimals}f}"

    @Property(bool)
    def highPrecisionStorage(self):
        """Keep full float precision internally while formatting display text."""
        return self._high_precision_storage

    @highPrecisionStorage.setter
    def highPrecisionStorage(self, enabled):
        self._high_precision_storage = bool(enabled)

    @Property(int)
    def displayDecimals(self):
        """Number of decimals shown for float settings."""
        return self._display_decimals

    @displayDecimals.setter
    def displayDecimals(self, decimals):
        self._display_decimals = max(0, int(decimals))
        if self._setting is not None:
            self.setDisplayValue(self._setting.getValue())

    def value(self):
        """Return the current value normalized to the setting type."""
        if self._setting is not None:
            if self._setting.value_type in (int, float):
                if self._high_precision_storage and self._internal_value is not None:
                    return self._internal_value

                try:
                    return self._setting.normalizeValue(cnc_float(self.text()))
                except (TypeError, ValueError):
                    return self._setting.getValue()

            return self.text()

        # Fallback when setting not yet bound (e.g., before initialize)
        try:
            return int(self.text())
        except ValueError:
            try:
                return float(self.text())
            except ValueError:
                return self.text()

    def formatValue(self, value):
        value_type = self._effective_value_type()

        if value_type is int:
            return str(int(cnc_float(value)))

        if value_type is float:
            return self._format_numeric_value(cnc_float(value))

        if isinstance(value, str):
            return value

        else:
            return str(value)

    def setValue(self, text):
        if self._setting is not None:
            value_type = self._effective_value_type()

            if value_type in (int, float):
                numeric = cnc_float(text)
                value = self._setting.normalizeValue(numeric)

                if value_type is float and self._high_precision_storage:
                    self._internal_value = float(numeric)
                    self._setting.setValue(self._setting.normalizeValue(self._internal_value))
                    self.setDisplayValue(self._internal_value)
                else:
                    self._setting.setValue(value)
                    self.setDisplayValue(value)
            else:
                value = str(text)
                self.setDisplayValue(value)
                self._setting.setValue(value)
        else:
            self._tmp_value = text

    def onReturnPressed(self):
        self.clearFocus()

    def setDisplayValue(self, value):
        self.blockSignals(True)
        try:
            self.setText(self.formatValue(value))
        except Exception as e:
            # Keep widget usable if a user enters an invalid format string.
            LOG.warning("VCPSettingsLineEdit setDisplayValue fallback due to format error: %s", e)
            self.setText(str(value) if value is not None else "")
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:

            value_type = self._effective_value_type()

            validator = None
            if value_type is int:
                validator = QIntValidator()
            elif value_type is float:
                validator = QDoubleValidator()
                # CNC parsing should always use decimal point regardless of OS locale.
                validator.setLocale(QLocale.c())
                validator.setDecimals(6)

            self.setValidator(validator)

            if self._tmp_value:
                self.setValue(self._tmp_value)
            else:
                self.setDisplayValue(self._setting.getValue())

            self._setting.notify(safe_qt_callback(self, self.setDisplayValue))

            self.editingFinished.connect(self.onEditingFinished)

    def onEditingFinished(self):
        if self._setting is None:
            return

        value_type = self._effective_value_type()

        if value_type in (int, float):
            try:
                numeric = cnc_float(self.text())
            except (TypeError, ValueError):
                self.setDisplayValue(self._setting.getValue())
                return

            value = self._setting.normalizeValue(numeric)

            if value_type is float and self._high_precision_storage:
                self._internal_value = float(numeric)
                self._setting.setValue(self._setting.normalizeValue(self._internal_value))
                self.setDisplayValue(self._internal_value)
            else:
                self._setting.setValue(value)
                self.setDisplayValue(value)
        else:
            value = self.text()
            self.setDisplayValue(value)
            self._setting.setValue(value)

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
            self._setting.notify(safe_qt_callback(self, self.setDisplayValue))
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
            self._setting.notify(safe_qt_callback(self, self.setDisplayValue))
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
            self._setting.notify(safe_qt_callback(self, self.setDisplayValue))
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

            self._setting.notify(safe_qt_callback(self, self.setDisplayChecked))
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
            self._setting.notify(safe_qt_callback(self, lambda v: self.setDisplayChecked(bool(v))))
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

            # Backward compatibility: accept stored text and map to index
            if isinstance(value, str):
                idx = self.findText(value)
                if idx != -1:
                    value = idx

            options = self._setting.enum_options
            # Only inject options if the UI has not already provided them
            if self.count() == 0 and isinstance(options, list):
                for option in options:
                    self.addItem(str(option))

            self.setDisplayIndex(value)
            self.currentIndexChanged.emit(value)

            self._setting.notify(safe_qt_callback(self, self.setDisplayIndex))
            self.currentIndexChanged.connect(self._setting.setValue)
