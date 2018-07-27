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
parser = argparse.ArgumentParser(description="PyQtVCP - A user interface toolkit for LinuxCNC")
parser.add_argument('-ini', help='path to the INI file, REQUIRED', required=True)
parser.add_argument('-ui', help="UI file to use, overrides INI setting")
parser.add_argument('-py', help="Py file to use, overrides INI setting")
parser.add_argument('-qss', help="QSS theme file to use, overrides INI setting")
parser.add_argument('-t', '--theme', help="Qt theme to use, defaults to 'fusion' theme")
parser.add_argument('-v', '--verbose', action='store_true', help="verbose debug message flag")
args = parser.parse_args()

# Set up logging
from QtPyVCP.utilities import logger
log_level = logger.WARNING
if args.verbose:
    log_level = logger.DEBUG
LOG = logger.initBaseLogger('QtPyVCP', log_file=None, log_level=log_level)

# Catch unhandled exceptions and display in dialog
from QtPyVCP.widgets.dialogs.error_dialog import ErrorDialog
def excepthook(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    LOG.exception(msg)
    error_dialog = ErrorDialog(msg)
    error_dialog.exec_()

# Connect the excepthook
sys.excepthook = excepthook

# init the ini INFO module
from QtPyVCP.utilities.info import Info
INFO = Info(args.ini)

# init the linuxcnc STATUS module
from QtPyVCP.utilities.status import Status
STATUS = Status()

# init the linuxcnc ACTION module
from QtPyVCP.utilities.action import Action
ACTION = Action()

confg_dir, ini_file = os.path.split(args.ini)
ini_name = os.path.splitext(ini_file)[0]

ui_file_path = args.ui or INFO.getUiFile(default='{}.ui'.format(ini_name))
if not os.path.exists(ui_file_path):
    raise ValueError("UI file '{}' does not exist".format(ui_file_path))
LOG.info("Using UI file: yellow<{}>".format(ui_file_path))

py_file_path = args.py or INFO.getPyFile(default='{}.py'.format(ini_name))
if not os.path.exists(py_file_path):
    raise ValueError("Py file '{}' does not exist".format(py_file_path))
LOG.info("Using Py file: yellow<{}>".format(py_file_path))

qss_file_path = args.qss or INFO.getQssFile(default='{}.qss'.format(ini_name))
style_sheet = ''
if os.path.exists(qss_file_path):
    with open(qss_file_path, 'r') as fh:
        style_sheet = fh.read()
    LOG.info("Using QSS file: yellow<{}>".format(qss_file_path))

# add the py dir to the path so we can import
py_dir, py_file = os.path.split(py_file_path)
sys.path.insert(1, py_dir)

# import the py file
from importlib import import_module
module_name = os.path.splitext(py_file)[0]
module = import_module(module_name)
recources = import_module(module_name + '_rc')

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QStyleFactory
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(STATUS.onShutdown)
    app.setStyle(QStyleFactory.create(args.theme))
    app.setStyleSheet(style_sheet)
    ui = module.MainWindow(ui_file=ui_file_path)
    ui.show()
    sys.exit(app.exec_())
