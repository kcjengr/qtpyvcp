#!/usr/bin/env python

#   Copyright (c) 2018 Kurt Jacobson
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   Generic button for calling a NGCGUI style subroutines. Useful for probing
#   quill-up, go home, goto etc functionality.

import os
import re
from PyQt5.QtWidgets import QPushButton, qApp
from PyQt5.QtCore import Qt, QEvent, pyqtSlot, pyqtProperty

from QtPyVCP.core import Info
INFO = Info()

from QtPyVCP.actions.machine_actions import issue_mdi

from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

# input: #<param_name> = #1 (=0.125 comment)
# result: [("param_name", "1", "0.125", "comment")]
# if a group is not present it will be an empty string
PARSE_POSITIONAL_ARGS = re.compile(r' *# *<([a-z0-9_-]+)> *= *#([0-9]+) *(?:\(= *([0-9.+-]+[0-9.]*?|) *(.*)\))?', re.I)

SUBROUTINE_PATH = INFO.getSubroutinePath()

class SubCallButton(QPushButton):
    def __init__(self, parent=None):
        super(SubCallButton, self).__init__(parent)

        self._sub_name = ''
        self._sub_path = ''

        self.clicked.connect(self.onClick)

    def onClick(self):
        window = qApp.activeWindow()

        if not os.path.exists(self._sub_path):
            LOG.error('Subroutine file does not exist: yellow<{}>'.format(self._sub_path))
            return False

        with open(self._sub_path, 'r') as fh:
            lines = fh.readlines()

        args = []
        for line in lines:
            line = line.strip()
            if not line.startswith('#'):
                continue
            result_list = PARSE_POSITIONAL_ARGS.findall(line)
            if len(result_list) == 0:
                continue

            pname, pnumber, default_val, comment = result_list[0]

            if int(pnumber) > 30:
                # only #1-#30 are passed to the sub
                continue

            try:
                # get the value from the GUI input widget
                val = getattr(window, pname).text()
            except:
                val = default_val
                LOG.warning('No input for red<{}> parameter, using default value blue<{}>'.format(pname, val))

            if val == '':
                LOG.error('No value given for parameter red<{}>, and no default specified'.format(pname))
                return False

            try:
                val = float(val)
            except ValueError:
                LOG.error('Input value "{}" given for parameter "{}" is not a valid number'.format(val, pname))
                return False

            index = int(pnumber) - 1
            while len(args) <= index:
                args.append("[0.0000]")

            args[index] = "[{}]".format(val)

        arg_str = ' '.join(args)

        cmd_str = "o<{}> call {}".format(self._sub_name, arg_str)

        LOG.debug('Calling sub file: yellow<{}> with args blue<{}>'.format(self._sub_path, arg_str))
        issue_mdi(cmd_str)

    def getSubName(self):
        return self._sub_name
    @pyqtSlot(str)
    def setSubName(self, sub_name):
        self._sub_name = sub_name
        self._sub_path = os.path.join(SUBROUTINE_PATH, sub_name + '.ngc')
    sub_name = pyqtProperty(str, getSubName, setSubName)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = SubCallButton()
    w.show()
    sys.exit(app.exec_())
