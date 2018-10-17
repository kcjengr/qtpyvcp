#!/usr/bin/env python
# coding: utf-8

#   Copyright (c) 2018 Kurt Jacobson
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with This program.  If not, see <http://www.gnu.org/licenses/>.

import os       # For file path manipulation
import linuxcnc # For commanding linuxcnc

from qtpyvcp.lib.notify import Notification, Urgency, init

from qtpy import uic, QtWidgets
from qtpyvcp.utilities.info import Info

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))

INFO = Info()

# Change this path to match [RS274NGC] SUBROUTINE_PATH given in the INI
SUBROUTINE_PATH = INFO.getSubroutinePath()

CMD = linuxcnc.command()
STAT = linuxcnc.stat()

class SubCaller(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(SubCaller, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self. ui = uic.loadUi(os.path.join(PARENT_DIR, "probe.ui"), self)

        self.notification = Notification("ProbeScreen")
        self.notification.setUrgency(Urgency.NORMAL)
        self.notification.setCategory("device")
        self.notification.setIconPath("/usr/share/icons/Tango/scalable/status/dialog-error.svg")

        for filename in os.listdir(SUBROUTINE_PATH):
            filename_and_ext = os.path.splitext(filename)
            subname = filename_and_ext[0]
            self.ui.subComboBox.addItem(filename, subname)

        self.ui.callSubButton.clicked.connect(self.callSub)

    def callSub(self):

        filename = self.subComboBox.currentText()
        subname = self.subComboBox.currentData()

        filepath = os.path.join(SUBROUTINE_PATH, filename)
        arg_str = ''
        with open(filepath, 'r') as fh:
            line = fh.readline()
            if line.startswith('(ARGS,'):
                args_format = line.strip('(ARGS,').strip().strip(')')

                args =  self.getArgs()
                arg_str = args_format.format(**args)

        cmd_str = "o<{}> call {}".format(subname, arg_str)

        # Print the command to the terminal so the user can see what is happening
        print "Calling MDI command: ", cmd_str

        # self.status_label.setStyleSheet("QStatusBar{color:black}")
        # self.status_label.setText("Probing ...")
        self.notification.show("Probing ...")

        # Set the LinuxCNC mode to MDI
        CMD.mode(linuxcnc.MODE_MDI)

        # Issue the MDI command to call the sub
        CMD.mdi(cmd_str)
        CMD.wait_complete(10000)
        print 'Done'
        STAT.poll()
        if STAT.probe_tripped:
            # self.status_label.setStyleSheet("QStatusBar{color:green}")
            # self.status_label.setText("Probing finished successfully")

            self.notification.show("Probing finished successfully")

            self.onProbeSuccess()
        else:
            # self.status_label.setStyleSheet("QStatusBar{color:red}")
            # self.status_label.setText("ERROR: Probe move finished without making contact")

            self.notification.show("ERROR: Probe move finished without making contact")

    def onProbeSuccess(self):
        probed_pos = STAT.probed_position

        for anum, aletter in enumerate('xyz'):
            pos_str = "{:6.4f}".format(probed_pos[anum])
            print "Probed {} pos: {}".format(aletter.upper(), pos_str)
            getattr(self, '{}_probed_pos'.format(aletter)).setText(pos_str)

    def getArgs(self):
        args = {}
        for line_edit in self.findChildren(QtWidgets.QLineEdit):
            key = line_edit.objectName()
            value = line_edit.text()
            args[key] = value
        return args


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    sub_caller = SubCaller()
    sub_caller.show()

    sys.exit(app.exec_())
