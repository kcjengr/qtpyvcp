#!/usr/bin/env python

import os
import sys
import subprocess

from qtpy.QtWidgets import QApplication, QFileDialog

from qtpyvcp.utilities.config_loader import load_config_files


app = QApplication(sys.argv)

options = QFileDialog.Options()
options |= QFileDialog.DontUseNativeDialog
file_name, _ = QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()", "",
                                          "VCP Config (*.yml);;UI Files (*.ui);;All Files (*)", options=options)

if file_name:
    print(file_name)

ui_file = ''
ext = os.path.splitext(file_name)[1]
if ext == '.yml':
    data = load_config_files(file_name).get('qtdesigner')

    if data is not None:
        yml_dir = os.path.dirname(file_name)

        ui_file = data.get('ui_file')
        if ui_file is not None:
            ui_file = os.path.realpath(os.path.join(yml_dir, ui_file))

        qss_file = data.get('qss_file')
        if qss_file is not None:
            qss_file = os.path.realpath(os.path.join(yml_dir, qss_file))
            os.environ['QSS_STYLESHEET'] = qss_file

elif ext == '.ui':
    ui_file = file_name

print ui_file

base = os.path.dirname(__file__)

sys.path.insert(0, base)
os.environ['PYQTDESIGNERPATH'] = os.path.join(base, 'qtpyvcp/widgets')
os.environ['QT_SELECT'] = 'qt5'

sys.exit(subprocess.call(['designer', ui_file]))
