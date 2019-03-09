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

    showToolSig = Signal(int, int,  arguments=['pocket', 'tool'])
    hideToolSig = Signal(int,  arguments=['tool'])

    def __init__(self, parent=None):
        super(DynATC, self).__init__(parent)

        self.engine().rootContext().setContextProperty("atc_spiner", self)
        url = QUrl.fromLocalFile(os.path.join(WIDGET_PATH, "atc.qml"))
        self.setSource(url)

        if IN_DESIGNER:
            return

        self.atc_position = 1

        self.tool_table = None
        self.pockets = None
        self.tools = None

        self.load_tools()

        STATUS.tool_table.notify(self.load_tools)
        STATUS.tool_in_spindle.notify(self.on_tool_in_spindle)
        STATUS.pocket_prepped.notify(self.on_pocket_prepped)

    def load_tools(self):

        self.tool_table = TOOLTABLE.getToolTable()

        self.pockets = dict()
        self.tools = dict()
        for index, tool in self.tool_table.items():
            self.pockets[tool['P']] = tool['T']
            self.tools[tool['T']] = tool['P']

        for i in range(12):
            self.hideToolSig.emit(i)

        for pocket, tool in self.pockets.items():
            self.showToolSig.emit(pocket - 1, tool)

    def on_pocket_prepped(self, pocket_num):
        if pocket_num > 0:
            print(self.tools)
            print(pocket_num)

            next_pocket = self.tools[pocket_num + 1]

            print(next_pocket)

            print("Tool Prepared: {}".format(pocket_num))
            print("Rotate from pocket {} to {}".format(self.atc_position, next_pocket))
            self.moveToPocketSig.emit(self.atc_position - 1, next_pocket - 1)
            self.atc_position = next_pocket
        else:
            print("Pocket Clear {}".format(pocket_num))

    def on_tool_in_spindle(self, tool_num):
        print("Tool in Spindle: {}".format(tool_num))
        self.toolInSpindleSig.emit(tool_num)

    @Slot()
    def rotate_forward(self):
        self.rotateFwdSig.emit(self.atc_position - 1)
        self.atc_position += 1

    @Slot()
    def rotate_reverse(self):
        self.rotateRevSig.emit(self.atc_position - 1)
        self.atc_position -= 1
