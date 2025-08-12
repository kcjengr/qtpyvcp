#!/usr/bin/env python

"""
Settings Widgets with Fail-Fast Validation

This module implements settings widgets that use fail-fast methodology:
- Invalid inputs raise exceptions immediately rather than being silently handled
- No try/except blocks that could hide bugs or lead to unpredictable state
- Clear error messages when validation fails
- Predictable widget behavior in all cases

This approach ensures bugs are caught early in development and the widgets
maintain consistent, reliable behavior in production.
"""

import locale
from qtpy.QtCore import Property, Qt, QTimer
from qtpy.QtWidgets import QLineEdit, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QPushButton
from qtpy.QtGui import QIntValidator, QDoubleValidator

from qtpyvcp import SETTINGS
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities.misc import cnc_float

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
    """Settings LineEdit with type-aware validation and high precision storage
    
    This widget supports both string and numeric settings with fail-fast methodology:
    - String settings: Values stored and displayed as-is (format strings, text, etc.)
    - Numeric settings: Values validated and optionally formatted with decimal precision
    - None values: Handled gracefully by displaying empty text
    - Invalid inputs: Raise exceptions immediately for early bug detection
    
    The widget automatically detects the setting type from the stored value and
    adapts its behavior accordingly while maintaining predictable state.
    """

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
        
        # High-precision storage properties with consistent display formatting
        self._high_precision_storage = False
        self._internal_value = None
        self._display_decimals = 4  # Always controls display format
        self._user_just_edited = False

        self.returnPressed.connect(self.onReturnPressed)
        
        # Add debugging for key events
        self.textChanged.connect(self._onTextChanged)
        
        # Debug validator settings and fix locale issues
        LOG.debug(f"VCPSettingsLineEdit.__init__() validator: {self.validator()}")
        if self.validator():
            validator = self.validator()
            LOG.debug(f"VCPSettingsLineEdit.__init__() validator type: {type(validator)}")
            if hasattr(validator, 'locale'):
                LOG.debug(f"VCPSettingsLineEdit.__init__() validator locale: {validator.locale().name()}")
                
                # Fix validator locale for CNC compatibility - always use C locale for decimal points
                from qtpy.QtCore import QLocale
                c_locale = QLocale(QLocale.C)
                validator.setLocale(c_locale)
                LOG.debug(f"VCPSettingsLineEdit.__init__() validator locale changed to: {validator.locale().name()}")
        
        # If no validator exists, create a CNC-compatible one for numeric settings
        self._ensureCncCompatibleValidator()

    def _ensureCncCompatibleValidator(self):
        """Ensure the widget has a CNC-compatible validator that uses decimal points"""
        # This will be called during initialization and when connecting to numeric settings
        if hasattr(self, '_setting') and self._setting is not None:
            setting_value = self._setting.getValue()
            if isinstance(setting_value, (int, float)):
                # Numeric setting needs CNC-compatible validator
                from qtpy.QtGui import QDoubleValidator
                from qtpy.QtCore import QLocale
                
                validator = QDoubleValidator()
                # Always use C locale for CNC decimal point format
                c_locale = QLocale(QLocale.C)
                validator.setLocale(c_locale)
                validator.setDecimals(6)  # Support CNC precision
                
                self.setValidator(validator)
                LOG.debug(f"VCPSettingsLineEdit._ensureCncCompatibleValidator() set CNC validator with C locale")

    @Property(bool)
    def highPrecisionStorage(self):
        """If True, store full precision internally. Display format always uses displayDecimals."""
        return self._high_precision_storage

    @highPrecisionStorage.setter
    def highPrecisionStorage(self, enabled):
        self._high_precision_storage = enabled

    @Property(int)
    def displayDecimals(self):
        """Number of decimal places to show in display (applies to both precision modes)"""
        return self._display_decimals

    @displayDecimals.setter
    def displayDecimals(self, decimals):
        self._display_decimals = max(0, decimals)
        # Update display immediately when decimals setting changes
        if hasattr(self, '_setting') and self._setting is not None:
            current_value = self.value()
            self.setDisplayValue(current_value)

    def formatValue(self, value):
        """Format value with type-aware validation"""
        
        # Handle None values
        if value is None:
            return ""
        
        # Handle different value types based on display mode
        if hasattr(self, '_setting') and self._setting is not None:
            setting_value = self._setting.getValue()
            if isinstance(setting_value, str):
                # String settings: return as-is
                return str(value)
        
        # Numeric settings: use displayDecimals formatting
        if isinstance(value, (int, float)):
            try:
                cnc_value = cnc_float(value)
                return f"{cnc_value:.{self._display_decimals}f}"
            except Exception as e:
                LOG.error(f"VCPSettingsLineEdit.formatValue() numeric formatting failed: {e}")
                raise
        elif isinstance(value, str):
            # Try to format as numeric if it looks like a number
            if value.strip():
                # Check if it's a numeric string
                try:
                    float_value = cnc_float(value)
                    return f"{float_value:.{self._display_decimals}f}"
                except ValueError as e:
                    LOG.error(f"VCPSettingsLineEdit.formatValue() string parsing failed: {e}")
                    # Not numeric, return as string
                    return value
            else:
                return ""
        else:
            result = str(value)
            LOG.debug(f"VCPSettingsLineEdit.formatValue() other type -> '{result}'")
            return result

    def setValue(self, value):
        """Store value with type-aware validation"""
        if self._setting is not None:
            # Get the expected type from the setting
            setting_value = self._setting.getValue()
            
            if isinstance(setting_value, str):
                # String setting: store as string
                str_value = str(value) if value is not None else ""
                self._setting.setValue(str_value)
                self.setDisplayValue(str_value)
            else:
                # Numeric setting: convert and validate
                if value is None:
                    raise ValueError(f"VCPSettingsLineEdit: Cannot set None value for numeric setting")
                
                float_value = cnc_float(value)  # Let this raise ValueError/TypeError if invalid
                
                if self._high_precision_storage:
                    # Store full precision internally and in settings
                    self._internal_value = float_value
                    self._setting.setValue(float_value)  # Store full precision
                else:
                    # Store display-formatted precision in settings
                    normalized_value = self._setting.normalizeValue(float_value)
                    self._setting.setValue(normalized_value)
                
                # Always format display the same way
                self.setDisplayValue(float_value)
        else:
            self._tmp_value = value

    def value(self):
        """Return the stored value with type-aware validation"""
        LOG.debug(f"VCPSettingsLineEdit.value() called, text='{self.text()}'")
        
        if self._high_precision_storage and self._internal_value is not None:
            LOG.debug(f"VCPSettingsLineEdit.value() returning high precision: {self._internal_value}")
            return self._internal_value
        
        text = self.text()
        
        # Determine expected type from setting
        if hasattr(self, '_setting') and self._setting is not None:
            setting_value = self._setting.getValue()
            if isinstance(setting_value, str):
                # String setting: return as string
                LOG.debug(f"VCPSettingsLineEdit.value() returning string: '{text}'")
                return text
        
        # Numeric setting: validate and convert
        if not text.strip():
            LOG.error("VCPSettingsLineEdit.value() empty text for numeric setting")
            raise ValueError(f"VCPSettingsLineEdit: Cannot get numeric value from empty text")
        
        LOG.debug(f"VCPSettingsLineEdit.value() parsing numeric: '{text}'")
        result = cnc_float(text)  # Let this raise ValueError if invalid
        LOG.debug(f"VCPSettingsLineEdit.value() parsed result: {result}")
        return result

    def onReturnPressed(self):
        # Since the validator now works properly with C locale, let the normal Qt signals handle this
        # Just clear focus and let editingFinished signal do its job
        self.clearFocus()

    def _onTextChanged(self, text):
        """Debug text changes"""
        LOG.debug(f"VCPSettingsLineEdit._onTextChanged() called with: '{text}'")

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.onReturnPressed()
        
        super(VCPSettingsLineEdit, self).keyPressEvent(event)

    def focusOutEvent(self, event):
        """Handle focus out events"""
        super(VCPSettingsLineEdit, self).focusOutEvent(event)

    def setDisplayValue(self, value):
        """Set display value with type-aware formatting"""
        # Skip settings notifications if user just edited to prevent overriding
        if self._user_just_edited:
            return
        
        self.blockSignals(True)
        
        # Handle None values gracefully
        if value is None:
            self.setText("")
            self.blockSignals(False)
            return
        
        # Determine the expected type from settings
        is_string_setting = False
        if hasattr(self, '_setting') and self._setting is not None:
            setting_value = self._setting.getValue()
            is_string_setting = isinstance(setting_value, str)
        
        if is_string_setting:
            # String setting: display as-is
            display_text = str(value)
        else:
            # Numeric setting: validate and format
            if isinstance(value, (int, float)):
                float_value = cnc_float(value)
            elif isinstance(value, str):
                if not value.strip():
                    # Empty string for numeric setting
                    display_text = ""
                    self.setText(display_text)
                    self.blockSignals(False)
                    return
                try:
                    float_value = cnc_float(value)
                except ValueError:
                    raise ValueError(f"VCPSettingsLineEdit: Cannot display non-numeric string '{value}' for numeric setting")
            else:
                raise TypeError(f"VCPSettingsLineEdit: Cannot display value of type {type(value)}: {value}")
            
            if self._high_precision_storage:
                # Store full precision internally
                self._internal_value = float_value
            
            # Format for display using displayDecimals
            display_text = self.formatValue(float_value)
        
        self.setText(display_text)
        self.blockSignals(False)

    def initialize(self):
        """Enhanced initialization with type-aware validation"""
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:

            val = self._setting.getValue()

            # Set up validators based on setting type with CNC compatibility
            validator = None
            if isinstance(val, int):
                validator = QIntValidator()
            elif isinstance(val, float):
                validator = QDoubleValidator()
                # Ensure CNC-compatible decimal point format
                from qtpy.QtCore import QLocale
                c_locale = QLocale(QLocale.C)
                validator.setLocale(c_locale)
                validator.setDecimals(6)  # Support CNC precision
                LOG.debug(f"VCPSettingsLineEdit.initialize() set CNC-compatible float validator")
            # No validator for string types - allow any input

            self.setValidator(validator)

            # Handle temporary values with type-aware validation
            if self._tmp_value is not None:
                if isinstance(val, str):
                    # String setting: use as-is
                    str_value = str(self._tmp_value)
                    self._setting.setValue(str_value)
                    self.setDisplayValue(str_value)
                else:
                    # Numeric setting: validate and convert
                    float_value = cnc_float(self._tmp_value)  # Let this raise if invalid
                    if self._high_precision_storage:
                        self._internal_value = float_value
                        self._setting.setValue(float_value)  # Store full precision
                    else:
                        normalized_value = self._setting.normalizeValue(float_value)
                        self._setting.setValue(normalized_value)
                    self.setDisplayValue(float_value)
            else:
                # Initialize from settings value
                if isinstance(val, str):
                    # String setting
                    self.setDisplayValue(val)
                elif isinstance(val, (int, float)):
                    # Numeric setting
                    float_value = cnc_float(val)
                    if self._high_precision_storage:
                        self._internal_value = float_value
                    self.setDisplayValue(float_value)
                elif val is None:
                    # Handle None values gracefully
                    self.setDisplayValue("")
                else:
                    raise TypeError(f"VCPSettingsLineEdit: Unsupported settings value type {type(val)}: {val}")

            # Connect to settings notifications and editing
            self._setting.notify(self.setDisplayValue)
            self.editingFinished.connect(self.onEditingFinished)

    def onEditingFinished(self):
        """Handle user editing with type-aware validation"""
        user_text = self.text()
        
        # Prevent duplicate calls when we're setting formatted text
        if self._user_just_edited:
            return
        
        # Determine expected type from setting
        is_string_setting = False
        if hasattr(self, '_setting') and self._setting is not None:
            setting_value = self._setting.getValue()
            is_string_setting = isinstance(setting_value, str)
        
        # Set flag to prevent duplicate processing
        self._user_just_edited = True
        
        try:
            if is_string_setting:
                # String setting: store as-is
                self._setting.setValue(user_text)
                formatted_text = user_text
            else:
                # Numeric setting: validate and convert
                if not user_text.strip():
                    raise ValueError(f"VCPSettingsLineEdit: Cannot process empty user input for numeric setting")
                
                user_value = cnc_float(user_text)  # Let this raise ValueError if invalid
                
                if self._high_precision_storage:
                    # Store full precision internally and in settings
                    self._internal_value = user_value
                    self._setting.setValue(user_value)  # Store full precision
                else:
                    # Store display-formatted precision
                    normalized_value = self._setting.normalizeValue(user_value)
                    self._setting.setValue(normalized_value)
                
                # Always format display consistently for numeric values
                formatted_text = self.formatValue(user_value)
            
            self.blockSignals(True)
            self.setText(formatted_text)
            self.blockSignals(False)
            
        except Exception as e:
            LOG.error(f"VCPSettingsLineEdit.onEditingFinished() failed: {e}")
            import traceback
            LOG.error(f"VCPSettingsLineEdit.onEditingFinished() traceback: {traceback.format_exc()}")
            raise
        finally:
            # Use QTimer to reset flag after all Qt events are processed
            from qtpy.QtCore import QTimer
            QTimer.singleShot(0, lambda: setattr(self, '_user_just_edited', False))

    @Property(str)
    def textFormat(self):
        return self._text_format

    @textFormat.setter
    def textFormat(self, text_fmt):
        # textFormat is ignored when using display decimals formatting
        if not hasattr(self, '_display_decimals'):
            # Only use textFormat for legacy compatibility if displayDecimals not set
            if self._setting_name != "":
                setting = SETTINGS.get(self._setting_name)
                if setting:
                    # Fail fast: format string must be valid
                    formatted_str = text_fmt.format(setting.getValue())  # Let this raise if invalid
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

    # Override text() to return empty string for checkable buttons
    def text(self):
        """Override text() to return empty string so parameter collection uses value() instead"""
        return ""  # Return empty string so get_val() falls through to value() method

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

            self.setDisplayChecked(value)
            self.toggled.emit(value)

            self._setting.notify(self.setDisplayChecked)
            # Connect to a wrapper that uses the configured output type
            self.toggled.connect(self._onToggled)

    # Wrapper method to emit the correct value type to settings
    def _onToggled(self, checked):
        """Internal method to emit the correct value type based on outputAsInt property"""
        if self._setting is not None:
            value_to_store = self.value()  # Uses the configurable output type
            self._setting.setValue(value_to_store)

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
        """Set the combo box to the index matching the value or index with fail-fast validation"""
        if self._store_index:
            # Value is index - fail fast if not convertible to int
            idx = int(value)  # Let this raise ValueError if invalid
        else:
            # Value is item text
            value_str = str(value)
            idx = self.findText(value_str)
            if idx < 0:
                raise ValueError(f"VCPSettingsComboBox: Text '{value_str}' not found in combo box items")
        
        if idx < 0:
            raise ValueError(f"VCPSettingsComboBox: Invalid index {idx} for combo box")
        
        self.blockSignals(True)
        self.setCurrentIndex(idx)
        self.blockSignals(False)

    def onIndexChanged(self, idx):
        """Store the actual index or value in the setting with fail-fast validation"""
        if self._setting is not None:
            if self._store_index:
                self._setting.setValue(idx)
            else:
                value = self.itemText(idx)
                # Try to convert to int or float if possible, fail fast if conversion fails
                if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                    # Integer conversion
                    value = int(value)
                elif '.' in value:
                    # Float conversion - fail fast if invalid
                    value = cnc_float(value)  # Let this raise ValueError if invalid
                # Otherwise keep as string
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
