#!/usr/bin/env python3

import os

from qtpy import uic
from qtpy.QtWidgets import QWidget

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger

IN_DESIGNER = os.getenv('DESIGNER') != None

LOG = logger.getLogger(__name__)
WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))

class GCodeProperties(QWidget):

    def __init__(self, parent=None, standalone=False):
        super(GCodeProperties, self).__init__(parent)
        if not IN_DESIGNER:

            self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "gcode_properties.ui"), self)