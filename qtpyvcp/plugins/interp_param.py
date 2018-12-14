"""Interp Parameter data plugin.

Exposes all the info available in the tool table. Watches the
tool table file for changes and re-loads as needed.
"""

import os

from qtpy.QtCore import QFileSystemWatcher, QTimer

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import QtPyVCPDataPlugin, QtPyVCPDataChannel, getPluginFromProtocol

STATUS = getPluginFromProtocol('status')
INFO = Info()

print "###############"

# Set up logging
LOG = getLogger(__name__)

#                          E X A M P L E   I N T E R F A C E
# tooltable:current_tool?            # will return the current tool data dictionary
# tooltable:current_tool?diameter    # will return the current tool diameter
# toollife:current_tool?hours

class CurrentTool(QtPyVCPDataChannel):
    """Current tool data channel.
    """

    def __init__(self):
        super(CurrentTool, self).__init__()

        print "Init"

        self._value = None

    def _update(self, value):
        self._value = value
        self.valueChanged.emit(value)


class ToolTable(QtPyVCPDataPlugin):

    protocol = 'tooltable'

    # data channels
    parameters = CurrentTool()

    TOOL_TABLE = {}

    def __init__(self):
        super(ToolTable, self).__init__()

        self.fs_watcher = None

        self.var_file = INFO.getParameterFile()
        if not os.path.exists(self.var_file):
            return

        # self.current_tool._update(self.TOOL_TABLE[STATUS.tool_in_spindle.value])

        # update signals
        STATUS.tool_in_spindle.onValueChanged(self.onToolChanged)

    def initialise(self):

        self.readVarFile()

        self.fs_watcher = QFileSystemWatcher()
        self.fs_watcher.addPath(self.var_file)
        self.fs_watcher.fileChanged.connect(self.onVarFileChanged)

    def onVarFileChanged(self, path):
        LOG.debug('Tool Table file changed: {}'.format(path))
        # ToolEdit deletes the file and then rewrites it, so wait
        # a bit to ensure the new data has been writen out.
        QTimer.singleShot(50, self.readVarFile)

    def onToolChanged(self, tool_num):
        self.current_tool._update(self.TOOL_TABLE[tool_num])

    def reloadToolTable(self):
        # rewatch the file if it stop being watched because it was deleted
        if self.var_file not in self.fs_watcher.files():
            self.fs_watcher.addPath(self.var_file)

        # reload with the new data
        self.loadToolTable()

    def readVarFile(self):

        if not os.path.exists(self.var_file):
            LOG.critical("Var file does not exist: {}".format(self.var_file))
            return

        with open(self.var_file, 'r') as fh:
            lines = fh.readlines()

        data = {}
        for line in lines:
            var, value = line.split()
            data[int(var)] = float(value)

        print data

        # update tooltable
        self.parameters._update(data)

        # import json
        # print json.dumps(table, sort_keys=True, indent=4)
