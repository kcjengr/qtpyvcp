import os

# Workarround for nvidia propietary drivers

import ctypes
import ctypes.util

ctypes.CDLL(ctypes.util.find_library("GL"), mode=ctypes.RTLD_GLOBAL)

# end of Workarround


import linuxcnc
from qtpy.QtCore import Signal, Slot, QUrl, QTimer
from qtpy.QtQuickWidgets import QQuickWidget

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.hal_qlib import QComponent

LOG = logger.getLogger(__name__)
STATUS = getPlugin('status')
TOOLTABLE = getPlugin('tooltable')
IN_DESIGNER = os.getenv('DESIGNER', False)
WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class DynATC(QQuickWidget):
    moveToPocketSig = Signal(int, int, arguments=['previous_pocket', 'pocket_num'])

    # toolInSpindleSig = Signal(int, arguments=['tool_num'])

    rotateFwdSig = Signal(int, arguments=['steps'])
    rotateRevSig = Signal(int, arguments=['steps'])

    showToolSig = Signal(int, int, arguments=['pocket', 'tool_num'])
    hideToolSig = Signal(int, arguments=['tool_num'])

    homeMsgSig = Signal(str, arguments=["message"])
    homingMsgSig = Signal(str, arguments=["message"])

    def __init__(self, parent=None):
        super(DynATC, self).__init__(parent)

        if IN_DESIGNER:
            return

        self.atc_position = 0
        self.home = 0
        self.homing = 0

        self.component = QComponent("atcsim")

        self.component.newPin('home', "float", "in")
        self.component.newPin('homing', "float", "in")

        self.component.newPin("goto", "s32", "in")

        self.component.newPin('fwd', "bit", "in")
        self.component.newPin('rev', "bit", "in")

        self.component['home'].valueChanged.connect(self.home_message)
        self.component['homing'].valueChanged.connect(self.homing_message)

        self.component['fwd'].valueChanged.connect(self.rotate_fw)
        self.component['rev'].valueChanged.connect(self.rotate_rev)

        self.component.ready()

        inifile = os.getenv("INI_FILE_NAME")
        self.inifile = linuxcnc.ini(inifile)

        self.parameter_file = self.inifile.find("RS274NGC", "PARAMETER_FILE")

        self.engine().rootContext().setContextProperty("atc_spiner", self)
        qml_path = os.path.join(WIDGET_PATH, "atc.qml")
        url = QUrl.fromLocalFile(qml_path)

        self.setSource(url)  # Fixme fails on qtdesigner

        self.parameter = dict()

        self.tool_table = None
        self.status_tool_table = None
        self.pockets = dict()
        self.tools = None

        self.offsets = [
            5190,
            5191,
            5192,
            5193,
            5194,
            5195,
            5196,
            5197,
            5198,
            5199,
            5200,
            5201
        ]

        self.load_tools()
        self.draw_tools()

        STATUS.tool_table.notify(self.load_tools)
        STATUS.pocket_prepped.notify(self.on_pocket_prepped)
        STATUS.tool_in_spindle.notify(self.on_tool_in_spindle)

    def hideEvent(self, *args, **kwargs):
        pass  # hack to prevent animation glitch when we are on another tab

    def load_tools(self):

        with open(self.parameter_file) as param:
            for line in param.read().splitlines():
                offset = int(line[0:4])
                val = float(line[5:])
                self.parameter[offset] = val

        self.tool_table = TOOLTABLE.getToolTable()
        self.status_tool_table = STATUS.tool_table

        self.pockets = dict()
        self.tools = dict()

        for index, offset in enumerate(self.offsets):
            self.pockets[index + 1] = self.parameter[offset]

    def draw_tools(self):
        for i in range(1, 13):
            self.hideToolSig.emit(i)

        for pocket, tool in self.pockets.items():
            if 0 < pocket < 13:
                if tool != 0:
                    self.showToolSig.emit(pocket, tool)

    def on_tool_in_spindle(self, tool):
        self.load_tools()
        self.draw_tools()

    def on_pocket_prepped(self, pocket_num):
        self.load_tools()
        self.draw_tools()

    def homing_message(self, *args, **kwargs):

        self.homing = args[0]

        if self.homing:
            self.homingMsgSig.emit("REFERENCING")
        else:
            self.homingMsgSig.emit("")

    def home_message(self, *args, **kwargs):

        self.home = args[0]

        if self.homing:
            self.homeMsgSig.emit("")
        else:
            self.homeMsgSig.emit("UN REFERENCED")

    def rotate_fw(self, *args, **kwargs):

        steps = self.component["goto"].value
        print(steps)

        self.rotateFwdSig.emit(steps)

    def rotate_rev(self, *args, **kwargs):

        steps = self.component["goto"].value
        print(steps)

        self.rotateRevSig.emit(steps)

