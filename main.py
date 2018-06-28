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
import argparse
import traceback
import linuxcnc

# parse command line args
parser = argparse.ArgumentParser(description='PyQtVCP - A LinuxCNC user interface')
parser.add_argument('-ini', help='path to the INI file', required=True)
parser.add_argument('-v', '--verbose', action='store_true', help='verbose debug message flag')
args = parser.parse_args()


from QtPyVCP.widgets.dialogs.error_dialog import ErrorDialog

# Catch unhandled exceptions and display in dialog
def excepthook(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    LOG.exception(msg)
    error_dialog = ErrorDialog(msg)
    error_dialog.exec_()

# Connect the excepthook
sys.excepthook = excepthook


# Set up logging
from QtPyVCP.utilities import logger
log_level = logger.WARNING
if args.verbose:
    log_level = logger.DEBUG

LOG = logger.initBaseLogger('QtPyVCP', log_file=None, log_level=log_level)

# init the INI module
from QtPyVCP.utilities import ini_info
ini_info.init(args.ini)

confg_dir, ini_file = os.path.split(args.ini)
ini_name = os.path.splitext(ini_file)[0]

ui_file_path = ini_info.get_ui_file(default='{}.ui'.format(ini_name))
if not os.path.exists(ui_file_path):
    raise ValueError("UI file '{}' does not exist".format(ui_file_path))

py_file_path = ini_info.get_py_file(default='{}.py'.format(ini_name))
if not os.path.exists(py_file_path):
    raise ValueError("Py file '{}' does not exist".format(ui_file_path))

print "Py File: ", py_file_path
print "UI File: ", ui_file_path

# add the py dir to the path
py_dir, py_file = os.path.split(py_file_path)
sys.path.insert(1, py_dir)

# import the py file
from importlib import import_module
module_name = os.path.splitext(py_file)[0]
module = import_module(module_name)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # app.setStyle(QStyleFactory.create('Windows'))
    ex = module.MainWindow(ui_file_path)
    ex.show()
    sys.exit(app.exec_())
