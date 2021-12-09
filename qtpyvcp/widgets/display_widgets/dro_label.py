"""
DROLabel
--------

"""

from PySide2.QtWidgets import QLabel
from PySide2.QtCore import Slot, Property

from qtpyvcp.widgets.base_widgets.dro_base_widget import DROBaseWidget


class DROLabel(QLabel, DROBaseWidget):
    """DROLabel
    """

    def __init__(self, parent=None):
        super(DROLabel, self).__init__(parent)
