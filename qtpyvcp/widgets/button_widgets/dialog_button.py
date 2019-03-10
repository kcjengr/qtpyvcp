"""Button for launching dialogs.
"""

from qtpy.QtCore import Property, Slot

from qtpyvcp.widgets import VCPButton
from qtpyvcp.widgets.dialogs import showDialog


class DialogButton(VCPButton):
    """Dialog Button.

    Args:
        parent (QObject) : The dialog's parent or None.
        dialog_name (str) : The name of the dialog to show then the button is clicked.
    """

    def __init__(self, parent=None, dialog_name=''):
        super(DialogButton, self).__init__(parent)

        self._dialog_name = dialog_name

        self.clicked.connect(self.showDialog)

    @Slot()
    def showDialog(self):
        showDialog(self._dialog_name)

    @Property(str)
    def dialogName(self):
        return self._dialog_name

    @dialogName.setter
    def dialogName(self, dialog_name):
        self._dialog_name = dialog_name