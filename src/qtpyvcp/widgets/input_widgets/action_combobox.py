import os

from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Property

from qtpyvcp.actions import bindWidget
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin


LOG = getLogger(__name__)


IN_DESIGNER = os.getenv('DESIGNER', False)
if not IN_DESIGNER:
    STATUS = getPlugin('status')


class ActionComboBox(QComboBox):
    """General purpose combobox for triggering QtPyVCP actions.

    Args:
        parent (QWidget) : The parent widget of the combobox, or None.

    Attributes:
        _action_name (str) : The fully qualified name of the action the
            combobox triggers when the selection is changed.
    """
    def __init__(self, parent=None):
        super(ActionComboBox, self).__init__(parent)

        self._action_name = ''

    @Property(str)
    def actionName(self):
        """The `actionName` property for setting the action the combobox
            should trigger from within QtDesigner.

        Returns:
            str : The action name.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        """Sets the name of the action the button should trigger and
            binds the widget to that action.

        Args:
            action_name (str) : A fully qualified action name.
        """
        self._action_name = action_name
        bindWidget(self, action_name)

    def mousePressEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept mouse Press Event')
            event.accept()
            return 
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if STATUS.isLocked():
            LOG.debug('Accept mouse Release Event')
            event.accept()
            return 
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept keyPressEvent Event')
            event.accept()
            return 
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept keyReleaseEvent Event')
            event.accept()
            return 
        super().keyReleaseEvent(event)
