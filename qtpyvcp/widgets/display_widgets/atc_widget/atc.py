import os

# Workarround for nvidia propietary drivers

import ctypes
import ctypes.util

ctypes.CDLL(ctypes.util.find_library("GL"), mode=ctypes.RTLD_GLOBAL)

# end of Workarround


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
    hideToolSig = Signal(int, arguments=['pocket'])

    homeMsgSig = Signal(str, arguments=["message"])
    homingMsgSig = Signal(str, arguments=["message"])

    def __init__(self, parent=None):
        super(DynATC, self).__init__(parent)

        if IN_DESIGNER:
            return

        self.atc_position = 0
        self.pocket = 1
        self.home = 0
        self.homing = 0
        self.pocket_slots = 12

        # self.component = QComponent("atc-widget")
        #
        # # define pocket pins to store tools
        #
        # for i in range(self.pocket_slots):
        #     pin_name = "pocket-{}".format(i+1)
        #     self.component.newPin(pin_name, "float", "in")
        #     self.component[pin_name].valueChanged.connect(self.pocket_changed)
        #
        # self.component.newPin('home', "bit", "in")
        # self.component.newPin('homing', "bit", "in")
        #
        # self.component.newPin("goto", "float", "in")
        # self.component.newPin('goto-enable', "bit", "in")
        #
        # self.component.newPin("steps", "float", "in")
        # self.component.newPin('steps-fwd', "bit", "in")
        # self.component.newPin('steps-rev', "bit", "in")
        #
        # self.component.newPin('jog-fwd', "bit", "in")
        # self.component.newPin('jog-rev', "bit", "in")
        #
        # self.component['home'].valueIncreased.connect(self.home_message)
        # self.component['homing'].valueIncreased.connect(self.homing_message)
        #
        # self.component['goto-enable'].valueIncreased.connect(self.goto)
        # self.component['steps-fwd'].valueIncreased.connect(self.steps_fwd)
        # self.component['steps-rev'].valueIncreased.connect(self.steps_rev)
        #
        # self.component['jog-fwd'].valueIncreased.connect(self.jog_fwd)
        # self.component['jog-rev'].valueIncreased.connect(self.jog_rev)
        #
        # self.component.ready()

        self.engine().rootContext().setContextProperty("atc_spiner", self)
        qml_path = os.path.join(WIDGET_PATH, "atc.qml")
        url = QUrl.fromLocalFile(qml_path)

        self.setSource(url)  # Fixme fails on qtdesigner

        self.tool_table = None
        self.status_tool_table = None
        self.pockets = dict()
        self.tools = None

        for pocket in range(1, 13):
            self.hideToolSig.emit(pocket)

        STATUS.tool_table.notify(self.load_tools)
        STATUS.pocket_prepped.notify(self.on_pocket_prepped)
        STATUS.tool_in_spindle.notify(self.on_tool_in_spindle)

    def hideEvent(self, *args, **kwargs):
        pass  # hack to prevent animation glitch when we are on another tab FIXME

    def load_tools(self):
        for i in range(1, self.pocket_slots+1):
            self.hideToolSig.emit(i)

        for pocket, tool in self.pockets.items():
            self.store_tool(pocket, tool)

    def store_tool(self, pocket, tool):
        self.pockets[pocket] = tool
        if tool != 0:
            self.showToolSig.emit(pocket, tool)
        else:
            self.hideToolSig.emit(pocket)

    def on_tool_in_spindle(self, tool):
        self.load_tools()

    def on_pocket_prepped(self, pocket_num):
        self.load_tools()

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

    def goto(self, pocket):

        if self.pocket > pocket:
            steps = self.pocket - pocket
            self.rotate_rev(steps)
        elif self.pocket < pocket:
            steps = pocket - self.pocket
            self.rotate_fwd(steps)

    def steps_fwd(self, steps):
        self.rotate_fwd(steps)

    def steps_rev(self, steps):
        self.rotate_rev(steps)

    def rotate_fwd(self, steps):
        self.rotateFwdSig.emit(steps)

    def rotate_rev(self, steps):
        self.rotateRevSig.emit(steps)

    def jog_fwd(self):
        self.rotateFwdSig.emit(1)

    def jog_rev(self):
        self.rotateRevSig.emit(1)
