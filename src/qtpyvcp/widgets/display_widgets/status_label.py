from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Property, Slot

from qtpyvcp.widgets import VCPWidget

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

class StatusLabel(QLabel, VCPWidget):
    """General purpose label for displaying status values.

    Args:
        parent (QWidget) : The parent widget, or None.
    """

    DEFAULT_RULE_PROPERTY = "Text"
    RULE_PROPERTIES = VCPWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Text': ['setText', str],
    })

    def __init__(self, parent=None):
        super(StatusLabel, self).__init__(parent)

        self._format = '{}'
        self._expression = 'val'
        self._compiled_exp = lambda val: val

        self.setText('Not Set')

    @Property(str)
    def format(self):
        """The str format specification to use for displaying the value.

        Returns:
            str : The current format specification.
        """
        return self._format

    @format.setter
    def format(self, format):
        self._format = format

    @Property(str)
    def expression(self):
        """A Python expression to process the data .

        Returns:
            str : The value of the `expression` property.
        """
        return self._expression

    @expression.setter
    def expression(self, expression):
        self._expression = expression
        try:
            self._compiled_exp = eval('lambda val: ' + self._expression, {})
        except:
            LOG.exception("Python expression is not valid: %s", self._expression)

    @Slot(str)
    @Slot(int)
    @Slot(bool)
    @Slot(float)
    def setValue(self, value):
        self.setText(self._format.format(self._compiled_exp(value)))
