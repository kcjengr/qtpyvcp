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

import subprocess

from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QPushButton, QVBoxLayout, QCheckBox

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog


from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities import logger

Log = logger.getLogger(__name__)


class ProbeSim(BaseDialog):

    def __init__(self, parent=None):
        super(ProbeSim, self).__init__(parent=parent)

        self.info = Info()
        self.log = Log

        self.close_button = QPushButton("Touch")
        self.pulse_checkbox = QCheckBox("Pulse")

        main_layout = QVBoxLayout()

        main_layout.addWidget(self.close_button)
        main_layout.addWidget(self.pulse_checkbox)

        self.setLayout(main_layout)
        self.setWindowTitle("Simulate touch probe")

        self.close_button.pressed.connect(self.touch_on)
        self.close_button.released.connect(self.touch_off)

        self.timer = QTimer()
        self.timer.timeout.connect(self.pulse_off)
        self.timer.setSingleShot(True)

    def touch_on(self):

        if self.pulse_checkbox.checkState():
            self.timer.start(1000)
            subprocess.Popen(['halcmd', 'setp', 'motion.probe-input', '1'])
            
        else:
            subprocess.Popen(['halcmd', 'setp', 'motion.probe-input', '1'])

    def touch_off(self):

        if self.pulse_checkbox.checkState():
            return

        subprocess.Popen(['halcmd', 'setp', 'motion.probe-input', '0'])

    def pulse_off(self):
        subprocess.Popen(['halcmd', 'setp', 'motion.probe-input', '0'])

    def close(self):
        self.hide()
