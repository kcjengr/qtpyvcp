from qtpy.QtWidgets import QApplication, QMessageBox

from qtpyvcp import DIALOGS
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

ACTIVE_DIALOGS = []


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

    win = QApplication.instance().activeWindow()
    win_pos = win.mapToGlobal(win.rect().center())
    dialog.move(win_pos.x() - dialog.width() / 2, win_pos.y() - dialog.height() / 2)

    dialog.show()
    ACTIVE_DIALOGS.append(dialog)


def hideActiveDialog():
    try:
        dialog = ACTIVE_DIALOGS.pop(-1)
        dialog.hide()
    except:
        pass


def hideDialog(name):
    dialog = getDialog(name)
    dialog.hide()


def askQuestion(title='', message='', parent=None):
    """Ask Question

    Args:
        title (str) : The title of the dialog window.
        message (str) : The message to show in the dialog.
        parent (QWidget) : The window to use as the dialog parent. If None
            the currently active application window will be used.

    Returns:
        True if the user answered Yes, False if No. None if no answer.
    """
    parent = parent or QApplication.instance().activeWindow()
    reply = QMessageBox.question(parent, title, message,
                                 QMessageBox.Yes,
                                 QMessageBox.No)
    if reply == QMessageBox.Yes:
        return True
    elif reply == QMessageBox.No:
        return False
