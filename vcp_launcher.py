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
parser.add_argument('-vcp', help="path to the VCP to launch, overrides INI setting")

parser.add_argument('-vcp-home', help="path to the VCP home dir, overrides INI setting")

parser.add_argument('-ui', help="UI file to use, overrides INI setting")
parser.add_argument('-py', help="Py file to use, overrides INI setting")
parser.add_argument('-qss', help="QSS style file to use, overrides INI setting")

parser.add_argument('-theme', help="Qt theme to use, defaults to 'fusion' theme")

parser.add_argument('-log', help="the file to log to")
parser.add_argument('-debug', action='store_true', help="print debug message s")
args = parser.parse_args()

qtpyvcp_home = os.path.dirname(os.path.abspath(__file__))

ini_file = os.environ.get('INI_FILE_NAME')
if ini_file is None:
    ini_file = args.ini or '/dev/null'
    os.environ['INI_FILE_NAME'] = ini_file

confg_dir = os.environ.get('CONFIG_DIR')
if confg_dir is None:
    confg_dir = os.path.dirname(ini_file)
    os.environ['CONFIG_DIR'] = confg_dir


INI = linuxcnc.ini(ini_file)

# get the VCP home directory
temp = args.vcp_home or INI.find('VCP', 'VCP_HOME') or '~/linuxcnc/vcps'
from QtPyVCP.utilities.misc import normalizePath
vcp_home = normalizePath(temp, confg_dir)

# get the name of the specific VCP to launch, default to QControl
vcp = args.vcp or INI.find('VCP', 'VCP') or 'QControl'
vcp_dir = os.path.join(vcp_home, vcp)
if not os.path.exists(vcp_dir):
    vcp = 'QControl'
    vcp_home = os.path.join(qtpyvcp_home, 'examples')

# the full path to dir containing the VCP to launch
vcp_dir = os.path.join(vcp_home, vcp)

# set the environment vars so they can be used in file paths etc.
os.environ['VCP_HOME'] = vcp_home
os.environ['VCP_DIR'] = vcp_dir

# get the path to the log file
temp = args.log or INI.find('DISPLAY', 'LOG_FILE') or '~/qtpyvcp.log'
log_file = normalizePath(temp, confg_dir)
os.environ['VCP_LOG_FILE'] = log_file

# get the path to the preference file
temp = INI.find('DISPLAY', 'PREFERENCE_FILE') or '$VCP_DIR/vcp.pref'
pref_file = normalizePath(temp, confg_dir)
os.environ['VCP_PREF_FILE'] = pref_file

# Set up logging
from QtPyVCP.utilities import logger
log_level = logger.WARNING
if args.debug:
    log_level = logger.DEBUG
LOG = logger.initBaseLogger('QtPyVCP', log_file=log_file, log_level=log_level)

LOG.info("VCP package: yellow<{}>".format(vcp_dir))
LOG.info("Using preference file: yellow<{}>".format(pref_file))


# Create the application instance
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

# Catch unhandled exceptions and display in dialog
from QtPyVCP.widgets.dialogs.error_dialog import ErrorDialog
def excepthook(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    LOG.exception(msg)
    print exc_value
    error_dialog = ErrorDialog(traceback=msg, error_type=exc_type.__name__, error_value=str(exc_value))
    error_dialog.exec_()

# Connect the excepthook
sys.excepthook = excepthook

# init the ini INFO module
from QtPyVCP.utilities.info import Info
INFO = Info(args.ini)

# init the linuxcnc ACTION module
from QtPyVCP.utilities.prefs import Prefs
PREFS = Prefs()
# init the linuxcnc STATUS module
from QtPyVCP.utilities.status import Status
STATUS = Status()

# init the linuxcnc ACTION module
from QtPyVCP.utilities.action import Action
ACTION = Action()

# ini_name = os.path.splitext(ini_file)[0]

# default_ui_file_path = os.path.join(vcp_dir, 'ui/{}.ui'.format(vcp_name))
# ui_file_path = args.ui or INFO.getUiFile(default=default_ui_file_path)
# if not os.path.exists(ui_file_path):
#     raise ValueError("UI file '{}' does not exist".format(ui_file_path))
# LOG.info("Using UI file: yellow<{}>".format(ui_file_path))

# default_py_file_path = os.path.join(vcp_dir, '{}.py'.format(vcp_name))
# py_file_path = args.py or INFO.getPyFile(default=default_py_file_path)
# if not os.path.exists(py_file_path):
#     raise ValueError("Py file '{}' does not exist".format(py_file_path))
# LOG.info("Using Py file: yellow<{}>".format(py_file_path))

sys.path.insert(1, vcp_home)

# import the VCP package
from importlib import import_module
vcp_package = import_module(vcp)

# initialize the VCP
vcp_instance = vcp_package.VCPMainWindow(ui_file=vcp_package.UI_FILE)

theme = args.theme or vcp_package.THEME
if theme is not None:
    from PyQt5.QtWidgets import QStyleFactory
    app.setStyle(QStyleFactory.create(theme))

qss_file = args.qss or vcp_package.QSS_FILE
if qss_file and os.path.exists(qss_file):
    LOG.info("Using QSS file: yellow<{}>".format(qss_file))
    with open(qss_file, 'r') as fh:
        style_sheet = fh.read()
    app.setStyleSheet(style_sheet)

app.aboutToQuit.connect(STATUS.onShutdown)

vcp_instance.show()
sys.exit(app.exec_())
