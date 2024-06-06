#!/usr/bin/env python3

import os

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtWidgets import QWidget

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger

IN_DESIGNER = os.getenv('DESIGNER') != None

LOG = logger.getLogger(__name__)
WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))

class GCodeProperties(QWidget):

    def __init__(self, parent=None, standalone=False):
        super(GCodeProperties, self).__init__(parent)
        if not IN_DESIGNER:
            file_path = os.path.join(os.path.dirname(__file__), "gcode_properties.ui")
            ui_file = QFile(file_path)
            ui_file.open(QFile.ReadOnly)

            loader = QUiLoader()
            self.ui = loader.load(ui_file, self)
            self.ui.show()
