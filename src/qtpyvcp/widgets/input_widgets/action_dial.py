from qtpy.QtWidgets import QDial
from qtpy.QtCore import Property

from qtpyvcp.actions import bindWidget


class ActionDial(QDial):
    """docstring for ActionDial."""
    def __init__(self, parent=None):
        super(ActionDial, self).__init__(parent)

        self._action_name = ''

    @Property(str)
    def actionName(self):
        """The fully qualified name of the action the dial should trigger.

        Returns:
            str : The action name.
        """
        return self._action_name

    @actionName.setter
    def actionName(self, action_name):
        """Sets the name of the action the dial should trigger.

        Args:
            action_name (str) : A fully qualified action name.
        """
        self._action_name = action_name
        bindWidget(self, action_name)
