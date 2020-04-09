from qtpy.QtWidgets import QApplication, QMessageBox

from qtpyvcp.app import DIALOGS
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


def getDialog(name):
    """Get dialog instance from name.

    Args:
        name (str) : The dialog name as defined in the YAML file.

    Returns:
        A dialog instance, or None.
    """
    try:
        return DIALOGS[name]
    except KeyError:
        LOG.error("The requested dialog '{}' was not found.".format(name))


def showDialog(name):
    """Show Dialog

    Args:
        name (str) : The name of the dialog to show.
    """

    dialog = getDialog(name)

    if dialog is None:
        msg = "The requested dialog <b>{}</b> was not found.".format(name)
        QMessageBox.critical(None, "Dialog not found!", msg)
        return

    dialog.show()

    win = QApplication.instance().activeWindow()
    win_pos = win.mapToGlobal(win.rect().center())
    dialog.move(win_pos.x() - dialog.width() / 2, win_pos.y() - dialog.height() / 2)
