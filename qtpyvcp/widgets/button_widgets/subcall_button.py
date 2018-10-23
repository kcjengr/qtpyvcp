#!/usr/bin/env python

import os
import re
from qtpy.QtWidgets import QPushButton, qApp
from qtpy.QtCore import Qt, QEvent, Property

from qtpyvcp.core import Info
INFO = Info()

from qtpyvcp.widgets import CMDWidget
from qtpyvcp.actions.machine_actions import issue_mdi

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

# input: #<param_name> = #1 (=0.125 comment)
# result: [("param_name", "1", "0.125", "comment")]
# if a group is not present it will be an empty string
PARSE_POSITIONAL_ARGS = re.compile(r' *# *<([a-z0-9_-]+)> *= *#([0-9]+) *(?:\(= *([0-9.+-]+[0-9.]*?|) *(.*)\))?', re.I)

SUBROUTINE_PATH = INFO.getSubroutinePath()

class SubCallButton(QPushButton, CMDWidget):
    """Button for calling ngc subroutines.

    Args:
        parent (QWidget, optional) : The parent widget of the button, or None.
        filename (str, optional) : The filename of the NGCGUI style subroutine
            the button should call, including any extension. The subroutine must
            be on the subroutine path specified in the INI.

    Todo:
        Add NGCGUI subroutine file format example.
    """
    def __init__(self, parent=None, filename=''):
        super(SubCallButton, self).__init__(parent)

        self._filename = filename

        issue_mdi.bindOk(widget=self)
        self.clicked.connect(self.callSub)

    def callSub(self):
        window = qApp.activeWindow()

        subfile = os.path.join(SUBROUTINE_PATH, self._filename)
        if not os.path.exists(subfile):
            LOG.error('Subroutine file does not exist: yellow<{}>'.format(subfile))
            return False

        with open(subfile, 'r') as fh:
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

        LOG.debug('Calling sub file: yellow<{}> with args blue<{}>'.format(subfile, arg_str))
        issue_mdi(cmd_str)

    @Property(str)
    def filename(self):
        """Gets or sets the filename of the subroutine the button should call (str).

        The subroutine file must be on the subroutine path as specified in the INI.
        """
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = filename

if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = SubCallButton()
    w.show()
    sys.exit(app.exec_())
