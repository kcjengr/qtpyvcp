#!/usr/bin/env python

from qtpy.QtWidgets import QApplication, QMessageBox

from qtpyvcp import DIALOGS
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

def showDialog(dialog_name):
    """Show Dialog

    Args:
        dialog_name (str) : The name of the dialog to show.
    """

    dialog = DIALOGS.get(dialog_name)

    if dialog is None:
        LOG.error("The requested dialog '{}' was not found.".format(dialog_name))
        msg = "The requested dialog <b>{}</b> was not found.".format(dialog_name)
        QMessageBox.critical(None, "Dialog not found!", msg)
        return

    dialog.show()

    win = QApplication.instance().activeWindow()
    win_pos = win.mapToGlobal(win.rect().center())
    dialog.move(win_pos.x() - dialog.width() / 2, win_pos.y() - dialog.height() / 2)
