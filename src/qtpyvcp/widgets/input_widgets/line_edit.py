"""
Line Edit
---------
"""

from qtpy.QtCore import Property
from qtpy.QtWidgets import QLineEdit

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget

LOG = getLogger(__name__)


class VCPLineEdit(QLineEdit, CMDWidget):
    """VCP Entry Widget"""

    DEFAULT_RULE_PROPERTY = "Text"
    RULE_PROPERTIES = CMDWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Text': ['setText', str],
        'Value': ['setValue', float],
    })

    def __init__(self, parent=None):
        super(VCPLineEdit, self).__init__(parent)

        self._action_name = ''
        
        # High-precision storage properties
        self._high_precision_storage = False
        self._internal_value = None
        self._display_decimals = 4

        self.returnPressed.connect(self.onReturnPressed)
        self.textChanged.connect(self._on_text_changed)

    @Property(bool)
    def highPrecisionStorage(self):
        """Enable high precision internal storage while displaying formatted values"""
        return self._high_precision_storage

    @highPrecisionStorage.setter
    def highPrecisionStorage(self, enabled):
        self._high_precision_storage = enabled
        if enabled and self._internal_value is None:
            self._internal_value = 0.0

    @Property(int)
    def displayDecimals(self):
        """Number of decimal places to display when high precision storage is enabled"""
        return self._display_decimals

    @displayDecimals.setter
    def displayDecimals(self, decimals):
        self._display_decimals = decimals
        if self._high_precision_storage and self._internal_value is not None:
            self._update_display()

    def setValue(self, value):
        """Set the value - high precision if enabled, otherwise as text"""
        try:
            numeric_value = float(value)
            if self._high_precision_storage:
                self._internal_value = numeric_value
                self._update_display()
            else:
                self.setText(str(value))
        except (ValueError, TypeError):
            if self._high_precision_storage:
                self._internal_value = 0.0
                self.clear()
            else:
                self.setText(str(value))

    def value(self):
        """Return the stored value - high precision if enabled, otherwise current text value"""
        if self._high_precision_storage and self._internal_value is not None:
            return self._internal_value
        else:
            try:
                return float(self.text()) if self.text() else 0.0
            except ValueError:
                return 0.0

    def _update_display(self):
        """Update the displayed text with formatted precision"""
        if not self._high_precision_storage or self._internal_value is None:
            return
        
        if self._internal_value == 0.0:
            self.clear()
        else:
            format_str = f"{{:.{self._display_decimals}f}}"
            display_text = format_str.format(self._internal_value)
            # Block signals to prevent recursive calls
            self.blockSignals(True)
            self.setText(display_text)
            self.blockSignals(False)

    def _on_text_changed(self, text):
        """Update internal value when user types (only if high precision storage is enabled)"""
        if self._high_precision_storage:
            try:
                self._internal_value = float(text) if text else 0.0
            except ValueError:
                # Keep previous internal value if user enters invalid text
                pass

    def onReturnPressed(self):
        self.clearFocus()
        LOG.debug("Action entry activated with text: %s", self.text())

    @Property(str)
    def actionName(self):
        """The name of the action the entry should trigger.

        Returns:
            str : The action name.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        self._action_name = action_name
        # ToDo: activate action on enter
        # bindWidget(self, action_name)

    def initialize(self):
        pass

    def terminate(self):
        pass