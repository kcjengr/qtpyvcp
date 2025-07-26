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
        
        # High-precision storage properties
        self._high_precision_storage = False
        self._internal_value = None
        self._display_decimals = 4
        self._user_just_edited = False

        self.returnPressed.connect(self.onReturnPressed)

    @Property(bool)
    def highPrecisionStorage(self):
        """If True, store full precision internally but display with limited decimals"""
        return self._high_precision_storage

    @highPrecisionStorage.setter
    def highPrecisionStorage(self, enabled):
        self._high_precision_storage = enabled

    @Property(int)
    def displayDecimals(self):
        """Number of decimal places to show in display (when highPrecisionStorage is True)"""
        return self._display_decimals

    @displayDecimals.setter
    def displayDecimals(self, decimals):
        self._display_decimals = max(0, decimals)

    def formatValue(self, value):
        if self._high_precision_storage and isinstance(value, (int, float)):
            # Use display decimals for formatting instead of textFormat
            return f"{value:.{self._display_decimals}f}"
        elif self._setting and self._setting.value_type in (int, float):
            return self._text_format.format(value)
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    def setValue(self, value):
        if self._setting is not None:
            if self._high_precision_storage:
                # Store full precision internally
                self._internal_value = float(value)
                # Display with limited precision
                self.setDisplayValue(self._internal_value)
                # Store full precision in settings
                self._setting.setValue(value)
            else:
                # Normal behavior
                normalized_value = self._setting.normalizeValue(value)
                self.setDisplayValue(normalized_value)
                self._setting.setValue(normalized_value)
        else:
            self._tmp_value = value

    def value(self):
        """Return the stored value - high precision if enabled, otherwise current text value"""
        if self._high_precision_storage and self._internal_value is not None:
            return self._internal_value
        elif self._setting:
            return self._setting.normalizeValue(self.text())
        else:
            return float(self.text())

    def onReturnPressed(self):
        self.clearFocus()

    def setDisplayValue(self, value):
        if self._high_precision_storage:
            pass
            # print(f"DEBUG: setDisplayValue called with {value}, internal_value: {self._internal_value}")
            # print(f"DEBUG: setDisplayValue - user_just_edited: {self._user_just_edited}")
        
        # Skip settings notifications if user just edited to prevent overriding the formatted display
        if self._high_precision_storage and self._user_just_edited:
            # print(f"DEBUG: setDisplayValue - skipping because user just edited")
            return
        
        self.blockSignals(True)
        
        if self._high_precision_storage:
            try:
                float_value = float(value)
                # Always format for display, but store full precision internally
                self._internal_value = float_value
                display_text = self.formatValue(float_value)
                # print(f"DEBUG: setDisplayValue - storing {float_value} internally, displaying: '{display_text}'")
            except (ValueError, TypeError):
                display_text = str(value)
                # print(f"DEBUG: setDisplayValue - invalid value, displaying as string: '{display_text}'")
        else:
            # Normal behavior
            display_text = self.formatValue(value)
        
        # print(f"DEBUG: setDisplayValue - final text being set: '{display_text}'")
        self.setText(display_text)
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
                if self._high_precision_storage:
                    self._internal_value = float(self._tmp_value)
                self.setDisplayValue(self._tmp_value)
                self._setting.setValue(self._tmp_value)
            else:
                if self._high_precision_storage:
                    self._internal_value = float(self._setting.getValue())
                self.setDisplayValue(self._setting.getValue())

            self._setting.notify(self.setDisplayValue)
            self.editingFinished.connect(self.onEditingFinished)

    def onEditingFinished(self):
        # When user edits, parse their input and store appropriately
        try:
            user_text = self.text()
            user_value = float(user_text)
            # print(f"DEBUG: onEditingFinished - user entered: {user_value}")
            # print(f"DEBUG: onEditingFinished - current text: '{user_text}'")
            # print(f"DEBUG: onEditingFinished - high_precision_storage: {self._high_precision_storage}")
            
            if self._high_precision_storage:
                # print(f"DEBUG: onEditingFinished - storing {user_value} internally")
                # Store full precision internally
                self._internal_value = user_value
                # Set flag to prevent settings notification from overriding
                self._user_just_edited = True
                # print(f"DEBUG: onEditingFinished - calling setValue({user_value}) on settings")
                # Store full precision in settings
                self._setting.setValue(user_value)
                # Format the display but keep full precision stored
                formatted_text = self.formatValue(user_value)
                # print(f"DEBUG: onEditingFinished - formatting display to: '{formatted_text}'")
                self.blockSignals(True)
                self.setText(formatted_text)
                self.blockSignals(False)
                self._user_just_edited = False
                # print(f"DEBUG: onEditingFinished - after formatting, text is now: '{self.text()}'")
            else:
                # Normal behavior - normalize and store
                normalized_value = self._setting.normalizeValue(user_value)
                self.setDisplayValue(normalized_value)
                self._setting.setValue(normalized_value)
                
        except ValueError:
            # Revert to previous value if invalid input
            if self._high_precision_storage and self._internal_value is not None:
                self.setDisplayValue(self._internal_value)
            else:
                self.setDisplayValue(self._setting.getValue())

    @Property(str)
    def textFormat(self):
        return self._text_format

    @textFormat.setter
    def textFormat(self, text_fmt):
        # Only use textFormat if not using high precision storage
        if not self._high_precision_storage:
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
    """Settings ComboBox

    By default, stores the current index as the setting value.
    If 'storeIndex' is set to False, stores the currentText value instead.
    """

    DEFAULT_RULE_PROPERTY = 'Enable'

    def __init__(self, parent):
        super(VCPSettingsComboBox, self).__init__(parent=parent)
        self._store_index = True  # Default: store index, not value

    @Property(bool)
    def storeIndex(self):
        """If True (default), store the index. If False, store the value (currentText)."""
        return self._store_index

    @storeIndex.setter
    def storeIndex(self, val):
        self._store_index = val

    def setDisplayValue(self, value):
        """Set the combo box to the index matching the value or index."""
        if self._store_index:
            # Value is index
            try:
                idx = int(value)
            except Exception:
                idx = -1
        else:
            # Value is item text
            value_str = str(value)
            idx = self.findText(value_str)
        if idx >= 0:
            self.blockSignals(True)
            self.setCurrentIndex(idx)
            self.blockSignals(False)

    def onIndexChanged(self, idx):
        """Store the actual index or value in the setting."""
        if self._setting is not None:
            if self._store_index:
                self._setting.setValue(idx)
            else:
                value = self.itemText(idx)
                # Try to convert to int or float if possible
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                self._setting.setValue(value)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:
            # Populate items
            options = self._setting.enum_options
            if isinstance(options, list):
                self.clear()
                for option in options:
                    self.addItem(str(option))
            elif self._setting.min_value is not None and self._setting.max_value is not None:
                self.clear()
                for v in range(int(self._setting.min_value), int(self._setting.max_value) + 1):
                    self.addItem(str(v))

            # Set display to current value
            self.setDisplayValue(self._setting.getValue())
            self._setting.notify(self.setDisplayValue)
            self.currentIndexChanged.connect(self.onIndexChanged)
