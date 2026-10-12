import os
import re
from PySide6.QtCore import Property, QRegularExpression, Qt, Slot
from PySide6.QtWidgets import QLineEdit, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QPushButton
from PySide6.QtGui import QRegularExpressionValidator

from qtpyvcp import SETTINGS
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities.qt_safety import safe_qt_callback
from qtpyvcp.utilities.misc import cnc_float, cnc_eval, CNC_UNITS_IN_METRES
from qtpyvcp.widgets.input_widgets.entry_units import (
    SHOWN_FIGURES, STORED_FIGURES, entry_base_unit, entry_pattern, round_figures, round_whole,
    set_entry_state, to_unit_system)

from qtpyvcp.utilities import logger
from qtpyvcp.widgets.base_widgets.base_widget import reset_to

IN_DESIGNER = os.getenv('DESIGNER', False)
LOG = logger.getLogger(__name__)

class VCPAbstractSettingsWidget(VCPWidget):
    def __init__(self,parent=None):
        super(VCPAbstractSettingsWidget, self).__init__()
        self._setting = None
        self._setting_name = ''

    @Property(str, freset=reset_to('settingName', ''))
    def settingName(self):
        return self._setting_name

    @settingName.setter
    def settingName(self, name):
        self._setting_name = name


class _EntryCheckRefused(ValueError):
    """A typed number the field's entry check refused (setEntryCheck)."""


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
        self._units_in_mm = False
        self._units_ft_m = False
        # The text this field last showed for its stored value. Finishing an
        # edit with the text unchanged means nothing was typed.
        self._shown_text = None
        # An extra rule a typed number must pass, set from code (setEntryCheck),
        # and the tooltip the field had before it showed why one was refused
        self._entry_check = None
        self._tooltip_before_refusal = None
        # Which unit system the field is SHOWN in, when that differs from the
        # INI units it is stored in (see setDisplayUnitsSource); None: the INI
        self._display_units_source = None

        self.returnPressed.connect(self.onReturnPressed)
        self.textEdited.connect(self._onEntryEdited)

    @Property(bool, freset=reset_to('unitsInMm', False))
    def unitsInMm(self):
        """Tick to hold the value in mm on a metric machine, in on an inch
        one. The field then also accepts a number typed with a unit and
        converts it: 1.5in shows as 38.1 on a metric machine. Exclusive with
        unitsFtM: ticking one clears the other. Leave both clear for a
        number that is not a length, such as an RPM or an angle."""
        return self._units_in_mm

    @unitsInMm.setter
    def unitsInMm(self, on):
        self._units_in_mm = bool(on)
        if self._units_in_mm:
            self._units_ft_m = False
        self._refresh_entry_validator()

    @Property(bool, freset=reset_to('unitsFtM', False))
    def unitsFtM(self):
        """Tick to hold the value in m on a metric machine, ft on an inch
        one. The field then also accepts a number typed with a unit and
        converts it: 3000mm shows as 3 on a metric machine. Exclusive with
        unitsInMm: ticking one clears the other."""
        return self._units_ft_m

    @unitsFtM.setter
    def unitsFtM(self, on):
        self._units_ft_m = bool(on)
        if self._units_ft_m:
            self._units_in_mm = False
        self._refresh_entry_validator()

    def _unit_scale(self):
        if self._units_in_mm:
            return 'in_mm'
        if self._units_ft_m:
            return 'ft_m'
        return None

    def _has_units(self):
        """Any number setting can take a unit once a units box is ticked. A
        whole-number one rounds the converted value -- see _whole_number."""
        return self._setting is not None and self._effective_value_type() in (int, float)

    def _whole_number(self, numeric):
        """The value a whole-number setting stores for numeric, or None to
        refuse it.

        With a units box ticked (a surface speed) it rounds: 600ft is 182.88
        m/min, stored as 183. With none (a tool number, a pass count) a
        fraction is refused, so 7/2 can never quietly become tool 3 or 4.
        """
        if numeric == int(numeric):
            return int(numeric)
        if self._unit_scale() is not None:
            return round_whole(numeric)
        return None

    def _is_number_entry(self):
        return self._setting is not None and self._effective_value_type() in (int, float)

    def _current_value(self):
        """The stored value an entry like +5 or /2 works on: the full value,
        never the rounded display, so repeated edits don't creep."""
        if self._high_precision_storage and self._internal_value is not None:
            return self._internal_value
        try:
            return float(self._setting.getValue())
        except (TypeError, ValueError):
            return None

    def _entry_value(self, text):
        """The value a typed number entry stores (in stored units), or
        ValueError if it can't be accepted. The entry is read in the units
        the field is shown in, and works on the current value shown in them."""
        factor = self._display_factor()
        current = self._current_value()
        if current is not None:
            current *= factor
        # Converted afterwards: rounded once, in the stored units, so the
        # rounding does not stack (50 mm / 2 shown in inches is still 25)
        numeric = cnc_eval(text, self._entry_base_unit(), current, rounded=(factor == 1.0))
        if factor != 1.0:
            numeric = round_figures(numeric / factor, STORED_FIGURES)
        if self._effective_value_type() is int:
            whole = self._whole_number(numeric)
            if whole is None:
                raise ValueError(f"'{text}' is not a whole number")
            numeric = whole
        # Outside the setting's min_value / max_value: refused like any other
        # entry that can't be accepted, never clamped -- a clamp would store
        # a number nobody typed
        low = getattr(self._setting, 'min_value', None)
        high = getattr(self._setting, 'max_value', None)
        if low is not None and numeric < low:
            raise ValueError(f"'{text}' is below the minimum {low}")
        if high is not None and numeric > high:
            raise ValueError(f"'{text}' is above the maximum {high}")
        if self._entry_check is not None:
            problem = self._entry_check(numeric)
            if problem:
                raise _EntryCheckRefused(problem)
        return numeric

    def setEntryCheck(self, check):
        """An extra rule a typed number must pass, set from code -- one that
        depends on something else, such as another setting. check(value) gets
        the value as it would be stored and returns None when it may be, or
        what is wrong in words. A refused entry is treated like any other that
        can't be accepted: marked while typing, Enter refused, dropped on
        click-away -- and the words are the field's tooltip while it is marked.
        None removes the rule. The stored value is checked too, here and
        whenever it is written (see refreshEntryCheck)."""
        self._entry_check = check
        self.refreshEntryCheck()

    def refreshEntryCheck(self):
        """Check the STORED value against the entry check and show the result:
        a value written from code -- a loaded operation, a preset, startup --
        that the rule refuses is marked like a refused entry (red, the words as
        tooltip); one it accepts is unmarked. Call it when something the rule
        depends on changes. Left alone while the field is being typed in."""
        if self._entry_check is None or self._setting is None or self.hasFocus():
            return
        value = self._setting.getValue()
        problem = self._entry_check(value) if value is not None else None
        set_entry_state(self, 'error' if problem else '')
        self._show_refusal(problem)

    def _show_refusal(self, problem):
        """The entry check's words as the tooltip while refused; the field's
        own tooltip back otherwise."""
        if problem:
            if self._tooltip_before_refusal is None:
                self._tooltip_before_refusal = self.toolTip()
            self.setToolTip(problem)
        elif self._tooltip_before_refusal is not None:
            self.setToolTip(self._tooltip_before_refusal)
            self._tooltip_before_refusal = None

    def _entry_check_problem(self, text):
        """The entry check's words when it refuses the typed text, else None."""
        if self._entry_check is None or not text.strip():
            return None
        try:
            self._entry_value(text)
        except _EntryCheckRefused as exc:
            return str(exc)
        except (TypeError, ValueError):
            return None
        return None

    def _entry_acceptable(self, text):
        if not text.strip():
            # Cleared: finishing shows the stored value again
            return True
        try:
            self._entry_value(text)
        except (TypeError, ValueError):
            return False
        return True

    def _onEntryEdited(self, text):
        """Show while typing whether Enter would accept the entry."""
        if self._is_number_entry():
            set_entry_state(self, 'editing' if self._entry_acceptable(text) else 'error')
            self._show_refusal(self._entry_check_problem(text))

    def keyPressEvent(self, event):
        if self._is_number_entry():
            if (event.key() in (Qt.Key_Return, Qt.Key_Enter)
                    and not self._entry_acceptable(self.text())):
                # Refused: the entry stays, selected and marked, until it is
                # fixed, cleared or dropped with Esc
                set_entry_state(self, 'error')
                self.selectAll()
                event.accept()
                return
            if event.key() == Qt.Key_Escape:
                # Drop the entry and show the stored value again
                self.setDisplayValue(self._setting.getValue())
                set_entry_state(self, '')
                self._show_refusal(None)
                event.accept()
                self.clearFocus()
                return
        super(VCPSettingsLineEdit, self).keyPressEvent(event)

    def setDisplayUnitsSource(self, source):
        """Show this field in another unit system than the INI units its value
        is stored in.

        source is a callable returning True for metric, False for inch, or
        None if it can't tell (the field then shows the stored units and
        refuses a typed unit rather than guess). A lathe page, for one, shows
        its fields in the page's own INCH/MM: 2 in stored shows as 50.8000 on
        a MM page. Only the display, typing and value() follow it -- the
        stored value is the same physical size whatever it returns, and
        setValue (rules, code) always takes stored units. After what it
        returns changes, call refreshDisplay(). None: show the INI units.
        """
        self._display_units_source = source

    def _display_units_metric(self):
        """What the display source says: True metric, False inch, None if it
        can't tell or fails."""
        try:
            metric = self._display_units_source()
        except Exception:
            LOG.exception("Display units source for '%s' failed", self._setting_name)
            return None
        return None if metric is None else bool(metric)

    def _stored_base_unit(self):
        """The unit the value is stored in: the INI units."""
        if not self._has_units():
            return None
        return entry_base_unit(self._unit_scale())

    def _entry_base_unit(self):
        """The unit the field is shown and typed in."""
        if not self._has_units():
            return None
        if self._display_units_source is None:
            return self._stored_base_unit()
        metric = self._display_units_metric()
        if metric is None:
            # Can't tell which system the field is shown in: plain numbers only
            return None
        return entry_base_unit(self._unit_scale(), metric)

    def _display_factor(self):
        """Stored value x this = shown value. 1.0 when they are the same unit."""
        stored, shown = self._stored_base_unit(), self._entry_base_unit()
        if not stored or not shown or stored == shown:
            return 1.0
        return CNC_UNITS_IN_METRES[stored] / CNC_UNITS_IN_METRES[shown]

    def _to_display_number(self, stored):
        """A stored number in the units the field is shown in."""
        factor = self._display_factor()
        if factor == 1.0:
            return stored
        shown = round_figures(float(stored) * factor, SHOWN_FIGURES)
        if self._effective_value_type() is int:
            return round_whole(shown)
        return shown

    def storedValue(self):
        """The value as stored, in the INI units, at full precision."""
        if self._setting is None:
            return None
        if self._high_precision_storage and self._internal_value is not None:
            return self._internal_value
        return self._setting.getValue()

    def toStoredUnits(self, value, metric):
        """value, given in metric (True) or inch (False) units of this field's
        kind, in the units the field stores -- for code that writes values
        that arrive in some other system, such as a loaded operation."""
        if not self._has_units():
            return value
        converted = to_unit_system(value, self._unit_scale(), bool(metric))
        if converted is value:
            return value
        if self._effective_value_type() is int:
            return round_whole(converted)
        return converted

    def refreshDisplay(self):
        """Show the stored value again, in the current display units. Call
        after what the display source returns has changed. An unfinished
        entry is dropped: it was typed in the old units."""
        if self._setting is None:
            return
        set_entry_state(self, '')
        self.setDisplayValue(self.storedValue())

    def _refresh_entry_validator(self):
        """Number fields accept arithmetic, and unit letters if a units box
        is ticked. Only once bound: before that the setting type is unknown."""
        if self._setting is None or self._effective_value_type() not in (int, float):
            return
        scale = self._unit_scale() if self._has_units() else None
        self.setValidator(QRegularExpressionValidator(
            QRegularExpression(entry_pattern(scale)), self))

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

    @Property(str, freset=reset_to('settingTypeMode', 'auto'))
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

    @Property(bool, freset=reset_to('highPrecisionStorage', False))
    def highPrecisionStorage(self):
        """Keep full float precision internally while formatting display text."""
        return self._high_precision_storage

    @highPrecisionStorage.setter
    def highPrecisionStorage(self, enabled):
        self._high_precision_storage = bool(enabled)

    @Property(int, freset=reset_to('displayDecimals', 4))
    def displayDecimals(self):
        """Number of decimals shown for float settings."""
        return self._display_decimals

    @displayDecimals.setter
    def displayDecimals(self, decimals):
        self._display_decimals = max(0, int(decimals))
        if self._setting is not None:
            self.setDisplayValue(self._setting.getValue())

    def value(self):
        """Return the current value normalized to the setting type, in the
        units the field is shown in -- the INI units unless a display units
        source says otherwise (see setDisplayUnitsSource)."""
        if self._setting is not None:
            if self._setting.value_type in (int, float):
                if self._high_precision_storage and self._internal_value is not None:
                    stored = self._internal_value
                else:
                    try:
                        stored = self._setting.normalizeValue(self._entry_value(self.text()))
                    except (TypeError, ValueError):
                        stored = self._setting.getValue()
                return self._to_display_number(stored)

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

    @Slot()
    def clearValue(self):
        """Clear field while committing the new value through setting channels.

        This is intended for Qt Designer signal-slot connections that need a
        no-argument slot. For numeric settings, it writes zero (instead of an
        empty string) so downstream consumers do not keep stale values.
        """
        if self._setting is None:
            self.clear()
            return

        value_type = self._effective_value_type()
        if value_type is int:
            self.setValue(0)
        elif value_type is float:
            self.setValue(0.0)
        else:
            self.setValue("")

    def setDisplayValue(self, value):
        """Show a STORED value, in the units the field is shown in."""
        self.blockSignals(True)
        try:
            if self._has_units() and value is not None and value != '':
                value = self._to_display_number(cnc_float(value))
            self.setText(self.formatValue(value))
        except Exception as e:
            # Keep widget usable if a user enters an invalid format string.
            LOG.warning("VCPSettingsLineEdit setDisplayValue fallback due to format error: %s", e)
            self.setText(str(value) if value is not None else "")
        self._shown_text = self.text()
        self.blockSignals(False)

    def onSettingChanged(self, value):
        """Apply an external setting change to the widget.

        Refreshes the high-precision internal cache BEFORE updating the display
        -- setSetting()-driven restores (e.g. loading a stored operation back
        into a page) must be reflected by value(), not just by the visible
        text, otherwise value() keeps returning whatever was last typed into
        the field even though the field displays the restored number.
        normalizeValue() is lossless for in-range floats, so the setting's
        value is safe to adopt as the new full-precision cache.
        """
        if self._high_precision_storage and self._effective_value_type() is float:
            try:
                self._internal_value = float(value)
            except (TypeError, ValueError):
                pass
        self.setDisplayValue(value)
        self.refreshEntryCheck()

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:

            val = self._setting.getValue()
            value_type = self._effective_value_type()

            # Number fields also take arithmetic -- 1.4*25.4, 3/4, (50-12)/2 --
            # and, with a units box ticked, a unit (38mm, 600ft),
            # all worked out when editing finishes and the answer shown in
            # its place (see onEditingFinished). The validator only limits
            # which keys can be typed; cnc_eval decides what is a valid entry.
            self.setValidator(None)
            self._refresh_entry_validator()

            if self._tmp_value:
                self.setValue(self._tmp_value)
            else:
                self.onSettingChanged(self._setting.getValue())

            self._setting.notify(safe_qt_callback(self, self.onSettingChanged))

            self.editingFinished.connect(self.onEditingFinished)

    def onEditingFinished(self):
        if self._setting is None:
            return

        value_type = self._effective_value_type()

        if value_type in (int, float):
            set_entry_state(self, '')
            self._show_refusal(None)

            # Nothing typed: the text is still what the field was showing.
            # Storing it would replace the stored value with its rounded
            # display -- 1/3 would become 0.3333 just by clicking in and out.
            if self.text() == self._shown_text:
                return

            # Clearing a number field changes nothing: the stored value is
            # shown again. Qt used to refuse to finish editing on an empty
            # field, so nothing was written; this keeps that, rather than
            # letting an empty field be read as 0.
            if not self.text().strip():
                self.setDisplayValue(self._setting.getValue())
                return

            # An entry that can't be accepted is dropped when the field loses
            # focus (Enter never gets here with one -- see keyPressEvent)
            try:
                numeric = self._entry_value(self.text())
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

    @Property(bool, freset=reset_to('outputAsInt', False))
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

            if str(self._setting_name).startswith('backplot.'):
                LOG.debug(
                    "[vtk-diag] button %r bound to %s, initial value %r",
                    self.objectName(), self._setting_name, value,
                )

            # Use wrapper for settings notification to handle type conversion
            self._setting.notify(safe_qt_callback(self, lambda v: self.setDisplayChecked(bool(v))))
            # Connect to a wrapper that uses the configured output type
            self.toggled.connect(self._onToggled)

    # Wrapper method to emit the correct value type to settings
    def _onToggled(self, checked):
        """Internal method to emit the correct value type based on outputAsInt property"""
        if self._setting is not None:
            value_to_store = self.value()  # Uses the configurable output type
            # Temporary diagnostics for the backplot display-option buttons.
            # Proves the click reached the setting layer. Remove when resolved.
            if str(self._setting_name).startswith('backplot.'):
                LOG.debug(
                    "[vtk-diag] button %r toggled -> %s = %r (checked=%r)",
                    self.objectName(), self._setting_name, value_to_store, checked,
                )
            self._setting.setValue(value_to_store)


class VCPSettingsComboBox(QComboBox, VCPAbstractSettingsWidget):
    """Settings ComboBox"""

    DEFAULT_RULE_PROPERTY = 'Enable'

    def __init__(self, parent):
        super(VCPSettingsComboBox, self).__init__(parent=parent)
        # Backward-compatible default: persist index unless explicitly disabled.
        self._store_index = True

    @Property(bool, freset=reset_to('storeIndex', True))
    def storeIndex(self):
        return self._store_index

    @storeIndex.setter
    def storeIndex(self, value):
        self._store_index = bool(value)

    def _stores_index(self):
        """Return True when this combo should persist index values."""
        prop = self.property('storeIndex')
        # Backward compatibility: if property is absent, keep legacy index behavior.
        if prop is None:
            wants_index = bool(self._store_index)
        elif isinstance(prop, bool):
            wants_index = prop
        elif isinstance(prop, (int, float)):
            wants_index = bool(prop)
        # Some .ui loaders can return dynamic properties as strings.
        elif isinstance(prop, str):
            normalized = prop.strip().lower()
            if normalized in ('false', '0', 'no', 'off'):
                wants_index = False
            elif normalized in ('true', '1', 'yes', 'on'):
                wants_index = True
            else:
                wants_index = bool(prop)
        else:
            wants_index = bool(prop)

        if not wants_index:
            return False

        # If numeric setting values in the combo are not 0..N-1, storing index
        # writes wrong values (then often clamps to the minimum setting value).
        if self._setting is not None and self.count() > 0 and self._setting.value_type in (int, float):
            item_values = [self._item_value(i) for i in range(self.count())]
            if item_values != list(range(self.count())):
                return False

        return True

    def _item_value(self, index):
        """Return item text converted to the underlying setting value type."""
        text = self.itemText(index)
        if self._setting is None:
            return text

        value_type = self._setting.value_type
        if value_type in (int, float):
            try:
                return value_type(text)
            except ValueError:
                # Labels like "2x" or "0.5x" carry the actual numeric value
                # plus a unit/multiplier suffix - extract it directly rather
                # than falling back to interpolation, which only works when
                # combo values are evenly spaced (e.g. "1x/2x/4x/8x/...").
                match = re.match(r'^\s*([-+]?\d*\.?\d+)', text)
                if match:
                    try:
                        return value_type(float(match.group(1)))
                    except ValueError:
                        pass
                # If combo labels are semantic strings (e.g. inch/mm, CSS/RPM)
                # but the setting is numeric, infer the numeric value from the
                # setting range and current item index.
                inferred = self._infer_numeric_value_from_index(index)
                if inferred is not None:
                    return inferred
                return text
        return text

    def _infer_numeric_value_from_index(self, index):
        """Infer numeric setting value from combo index using setting range.

        This supports legacy configs where int/float settings use semantic
        combo labels without enum options.
        """
        if self._setting is None:
            return None

        value_type = self._setting.value_type
        if value_type not in (int, float):
            return None

        min_value = getattr(self._setting, 'min_value', None)
        max_value = getattr(self._setting, 'max_value', None)

        if min_value is None or max_value is None:
            return None

        count = self.count()
        if count <= 0:
            return None

        if count == 1:
            candidate = float(min_value)
        else:
            span = float(max_value) - float(min_value)
            step = span / float(count - 1)
            candidate = float(min_value) + (step * float(index))

        if value_type is int:
            rounded = round(candidate)
            if abs(candidate - rounded) > 1e-9:
                return None
            return int(rounded)

        return float(candidate)

    def _set_display_from_value(self, value):
        """Select combobox entry matching a persisted setting value.

        Returns:
            str: 'value' when matched by value/text,
                 'index' when matched using legacy index fallback,
                 '' when no match was found.
        """
        # First try exact typed/text matching against combo item values.
        for idx in range(self.count()):
            item_value = self._item_value(idx)
            if item_value == value or str(item_value) == str(value):
                self.setDisplayIndex(idx)
                return 'value'

        # Backward compatibility: if value looks like an index, accept it.
        if isinstance(value, int) and 0 <= value < self.count():
            self.setDisplayIndex(value)
            return 'index'

        return ''

    def _store_selected_value(self, index):
        """Persist selected value (not index) when storeIndex is disabled."""
        if self._setting is None or index < 0:
            return
        value = self._item_value(index)
        try:
            self._setting.setValue(value)
        except (ValueError, TypeError):
            LOG.warning("Could not store combo value %r for setting %r",
                        value, getattr(self._setting, 'name', None))

    def _apply_setting_update_store_index(self, value):
        """Update display for store-index mode from either index or item value."""
        if self.count() <= 0:
            return

        if isinstance(value, int) and 0 <= value < self.count():
            self.setDisplayIndex(value)
            return

        self._set_display_from_value(value)

    def _resolve_display_after_items_inserted(self, *args):
        """Ensure a valid selection after dynamic item population."""
        if self._setting is None or self.count() <= 0:
            return

        if self.currentIndex() >= 0:
            return

        value = self._setting.getValue()
        match_mode = self._set_display_from_value(value)
        if match_mode == '':
            default_match = self._set_display_from_value(self._setting.default_value)
            if default_match == '':
                self.setDisplayIndex(0)

    def setDisplayIndex(self, index):
        self.blockSignals(True)

        if self.count() <= 0:
            resolved_index = -1
        else:
            try:
                resolved_index = int(index)
            except (TypeError, ValueError):
                resolved_index = self.currentIndex()

            if resolved_index < 0 or resolved_index >= self.count():
                resolved_index = self.currentIndex() if self.currentIndex() >= 0 else 0

        self.setCurrentIndex(resolved_index)
        self.blockSignals(False)

    def initialize(self):
        self._setting = SETTINGS.get(self._setting_name)
        if self._setting is not None:

            value = self._setting.getValue()

            # Backward compatibility for index-storage combos only.
            if self._stores_index() and isinstance(value, str):
                idx = self.findText(value)
                if idx != -1:
                    value = idx

            options = self._setting.enum_options
            had_items_before = self.count() > 0
            # Only inject options if the UI has not already provided them
            if self.count() == 0 and isinstance(options, list):
                for option in options:
                    self.addItem(str(option))

            # Some combos are populated later by operation logic; re-resolve
            # their selection when items are inserted to avoid a blank state.
            model = self.model()
            needs_late_population_watch = (not had_items_before) and self.count() == 0
            if needs_late_population_watch and model is not None and not getattr(self, '_rows_inserted_connected', False):
                model.rowsInserted.connect(
                    safe_qt_callback(self, self._resolve_display_after_items_inserted)
                )
                setattr(self, '_rows_inserted_connected', True)

            if self._stores_index():
                # Prefer index when valid; otherwise support value-based fallback.
                match_mode = ''
                if isinstance(value, int) and 0 <= value < self.count():
                    self.setDisplayIndex(value)
                    match_mode = 'index'
                else:
                    match_mode = self._set_display_from_value(value)

                if match_mode == '':
                    default_match = self._set_display_from_value(self._setting.default_value)
                    if default_match == '':
                        self.setDisplayIndex(0 if self.count() else -1)

                self.currentIndexChanged.emit(self.currentIndex())

                self._setting.notify(safe_qt_callback(self, self._apply_setting_update_store_index))
                self.currentIndexChanged.connect(self._setting.setValue)
            else:
                match_mode = self._set_display_from_value(value)

                # Migrate legacy index-based persisted values to real item values.
                if match_mode == 'index':
                    migrated_value = self._item_value(self.currentIndex())
                    try:
                        self._setting.setValue(migrated_value)
                    except Exception as e:
                        LOG.warning(
                            "Failed to migrate legacy index value '%s' for setting '%s': %s",
                            value,
                            self._setting_name,
                            e,
                        )

                # If persisted data is invalid, fall back to default setting value.
                elif match_mode == '':
                    default_match = self._set_display_from_value(self._setting.default_value)
                    if default_match == '':
                        self.setDisplayIndex(0 if self.count() else -1)
                    try:
                        if self.currentIndex() >= 0:
                            self._setting.setValue(self._item_value(self.currentIndex()))
                    except Exception as e:
                        LOG.warning(
                            "Failed to restore default for setting '%s': %s",
                            self._setting_name,
                            e,
                        )

                self.currentIndexChanged.emit(self.currentIndex())

                self._setting.notify(safe_qt_callback(self, self._set_display_from_value))
                self.currentIndexChanged.connect(self._store_selected_value)
