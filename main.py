#!/usr/bin/env python

#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
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

import os
import sys
import traceback
import linuxcnc

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QStyleFactory, QErrorMessage

# Set up logging
from QtPyVCP.core import logger
log = logger.get('QtPyVCP')

from QtPyVCP.widgets.dialogs.error_dialog import ErrorDialog


# File paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
uifile = os.path.join(PYDIR, 'QtPyVCP/demo.ui')
form, base = uic.loadUiType(uifile)

# Log exceptions
def excepthook(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log.exception(msg)
    error_dialog = ErrorDialog(msg)
    error_dialog.exec_()

sys.excepthook = excepthook

class PyQtUI(base, form):
    def __init__(self):
        super(base, self).__init__()
        self.setupUi(self)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setStyle(QStyleFactory.create('Windows'))
    ex = PyQtUI()
    ex.show()
    sys.exit(app.exec_())
