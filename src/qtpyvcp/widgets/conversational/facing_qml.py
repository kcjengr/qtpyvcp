# required packages
# sudo apt-get install python3-pyqt5.qtquick qml-module-qtquick-controls

import os

import linuxcnc

# Workarround for nvidia propietary drivers

import ctypes
import ctypes.util

ctypes.CDLL(ctypes.util.find_library("GL"), mode=ctypes.RTLD_GLOBAL)

# end of Workarround

from qtpy.QtCore import Property, Signal, Slot, QUrl, QObject
from qtpy.QtQuickWidgets import QQuickWidget

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)
STATUS = getPlugin('status')
IN_DESIGNER = os.getenv('DESIGNER', False)
WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


from qtpyvcp.ops.face_ops import FaceOps
from .base_widget import ConversationalBaseWidget

class FacingWidgetQML(QQuickWidget):
    def __init__(self, parent=None):
        super(FacingWidgetQML, self).__init__(parent)

        if parent is None:
            return

        self.engine().rootContext().setContextProperty("facing_handler", self)
        url = QUrl.fromLocalFile(os.path.join(WIDGET_PATH, "facing_widget.qml"))
        self.setSource(url)



