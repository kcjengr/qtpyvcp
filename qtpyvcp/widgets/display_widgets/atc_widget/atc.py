import os

# Workarround for nvidia propietary drivers

import ctypes
import ctypes.util
from pprint import pprint

ctypes.CDLL(ctypes.util.find_library("GL"), mode=ctypes.RTLD_GLOBAL)

# end of Workarround

from qtpy.QtCore import Signal, Slot, QUrl
from qtpy.QtQuickWidgets import QQuickWidget

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)
STATUS = getPlugin('status')
TOOLTABLE = getPlugin('tooltable')
IN_DESIGNER = os.getenv('DESIGNER', False)

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class DynATC(QQuickWidget):

    moveToPocketSig = Signal(int, int, arguments=['previous_pocket', 'pocket_num'])

    toolInSpindleSig = Signal(int, arguments=['tool_num'])

    rotateFwdSig = Signal(int, arguments=['position'])
    rotateRevSig = Signal(int, arguments=['position'])

    showToolSig = Signal(int, int, arguments=['pocket', 'tool_num'])
    hideToolSig = Signal(int,  arguments=['tool_num'])

    def __init__(self, parent=None):
        super(DynATC, self).__init__(parent)

        self.engine().rootContext().setContextProperty("atc_spiner", self)
        url = QUrl.fromLocalFile(os.path.join(WIDGET_PATH, "atc.qml"))

        self.setSource(url)

        self.atc_position = 1

        self.tool_table = None
        self.status_tool_table = None
        self.pockets = None
        self.tools = None

        self.load_tools()
        self.draw_tools()

        STATUS.tool_table.notify(self.load_tools)
        STATUS.pocket_prepped.notify(self.on_pocket_prepped)

    def hideEvent(self, *args, **kwargs):
        pass  # hack to prevent animation glitch

    def load_tools(self):
        self.tool_table = TOOLTABLE.getToolTable()
        self.status_tool_table = STATUS.tool_table

        self.pockets = dict()
        self.tools = dict()

        for index, tool in self.tool_table.items():
            self.pockets[tool['P']] = tool['T']
            self.tools[tool['T']] = tool['P']

    def draw_tools(self):
        for i in range(1, 12):
            self.hideToolSig.emit(i)

        for pocket, tool in self.pockets.items():
            if 0 < pocket < 13:
                self.showToolSig.emit(pocket, tool)

    def on_pocket_prepped(self, pocket_num):

        if pocket_num > 0:

            self.draw_tools()

            tool = self.status_tool_table[pocket_num][0]
            next_pocket = self.tool_table[tool]['P']

            self.moveToPocketSig.emit(self.atc_position - 1, next_pocket - 1)
            self.atc_position = next_pocket

        if pocket_num == -1:
            tool = self.status_tool_table[self.atc_position][0]
            self.hideToolSig.emit(tool)

    @Slot()
    def rotate_forward(self):
        self.rotateFwdSig.emit(self.atc_position - 1)
        self.atc_position += 1

    @Slot()
    def rotate_reverse(self):
        self.rotateRevSig.emit(self.atc_position - 1)
        self.atc_position -= 1
