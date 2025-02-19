

import os

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QFile
from PySide6.QtWidgets import QDialog

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.pyside_ui_loader import PySide6Ui

LOG = getLogger(__name__)


class BaseDialog(QDialog):
    """Base Dialog

    Base QtPyVCP dialog class.

    This is intended to be used as a base class for custom dialogs, as well
    as a provider for use in YAML config files. This allows loading custom
    dialogs from .ui files without needing to write any python code.

    You can launch dialogs using a 
    :doc:`Dialog Button </widgets/buttons/index>` or
    from a window menu item.

    Example:

        YAML config for loading a custom dialog called `my_dialog` from a .ui
        file named ``my_diloag.ui`` located in the same dir as the .yml file::

            dialogs:
              my_dialog:
                provider: qtpyvcp.widgets.dialogs.base_dialog:BaseDialog
                kwargs:
                  ui_file: {{ file.dir }}/my_dialog.ui
                  title: My Dialog Title    # optional, set the dialog title
                  modal: false              # optional, whether the dialog is modal
                  popup: false              # optional, whether the dialog is a popup
                  frameless: false          # optional, whether the dialog is frameless
                  stay_on_top: true         # optional, whether the dialog stays on top

    Args:
        parent (QWidget, optional) : The dialog's parent window, or None.
        ui_file (str, optional) : The path of a .ui file to load the dialog
            from. The ui base widget should be a QDialog.
        title (str, optional) : The title to use for the dialog. This will
            override any title property set in QtDesigner.
        modal (bool, optional) : Whether the dialog should be application modal.
            This will override any modality hints set in QtDesigner.
        frameless (bool, optional) : Whether the window has a frame or not.
            If the window does not have a frame you will need some way to
            close it, like an Ok or Cancel button.
        popup: (bool, optional) : Makes the dialog use a frame less window
            that automatically hides when it looses focus.
        stay_on_top (bool, optional) : Sets the stay on top hint window flag.
            This overrides any window flags set in QtDesiger.
    """
    def __init__(self, parent=None, ui_file=None, title=None, modal=None,
                 popup=None, frameless=None, stay_on_top=None):
        super(BaseDialog, self).__init__(parent)

        if ui_file is not None:
            self.loadUiFile(ui_file)

        if title is not None:
            self.setWindowTitle(title)

        if modal is not None:
            if modal:
                self.setWindowModality(Qt.ApplicationModal)
            else:
                self.setWindowModality(Qt.NonModal)

        if popup is not None:
            self.setWindowFlags(Qt.Popup)

        if frameless is not None:
            self.setWindowFlag(Qt.FramelessWindowHint, frameless)

        if stay_on_top is not None:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, stay_on_top)

    def loadUiFile(self, ui_file):
        """Load dialog from a .ui file.

        The .ui file base class should be a QDialog.

        Args:
            ui_file (str) : path to the .ui file to load.
        """

        file_path = os.path.join(os.path.dirname(__file__), ui_file)
        #ui_file = QFile(file_path)
        #ui_file.open(QFile.ReadOnly)
        
        #loader = QUiLoader()
        #self.ui = loader.load(ui_file, self)
        #self.ui.show()
        form_class, base_class = PySide6Ui(file_path).load()
        form = form_class()
        form.setupUi(self)

    def setWindowFlag(self, flag, on):
        """BackPort QWidget.setWindowFlag() implementation from Qt 5.9

        This method was introduced in Qt 5.9 so is not present
        in Qt 5.7.1 which is standard on Debian 9 (stretch), so
        add our own implementation.
        """
        if on:
            # add flag
            self.setWindowFlags(self.windowFlags() | flag)
        else:
            # remove flag
            self.setWindowFlags(self.windowFlags() ^ flag)
