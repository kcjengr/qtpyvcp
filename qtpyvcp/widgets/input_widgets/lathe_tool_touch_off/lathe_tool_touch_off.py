import os

# Workarround for nvidia propietary drivers

import ctypes
import ctypes.util

ctypes.CDLL(ctypes.util.find_library("GL"), mode=ctypes.RTLD_GLOBAL)

# end of Workarround

from hal import component, HAL_BIT, HAL_IN

from qtpy.QtCore import Signal, Slot, QUrl
from qtpy.QtQuickWidgets import QQuickWidget

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class LatheToolTouchOff(QQuickWidget):

    def __init__(self, parent=None):
        super(LatheToolTouchOff, self).__init__(parent)

        if parent is None:
            return

        self.engine().rootContext().setContextProperty("tool_touch_off", self)
        url = QUrl.fromLocalFile(os.path.join(WIDGET_PATH, "lathe_tool_touch_off.qml"))
        self.setSource(url)

        self.selected_tool = None
