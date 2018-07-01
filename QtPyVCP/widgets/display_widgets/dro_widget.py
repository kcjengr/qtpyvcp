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
from enum import Enum

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QEvent, pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.core import Status, Action, Info
STATUS = Status()
ACTION = Action()
INFO = Info()

class DROWidget(QLabel):
    coords = INFO.getCoordinates()
    machine_metric = INFO.getIsMachineMetric()

    # Set the conversions used for changing the DRO units
    # Only convert linear axes (XYZUVW), use factor of unity for ABC
    if machine_metric:
        # List of factors for converting from mm to inches
        conversion_list = [1.0/25.4]*3 + [1]*3 + [1.0/25.4]*3
    else:
        # List of factors for converting from inches to mm
        conversion_list = [25.4]*3 + [1]*3 + [25.4]*3

    def __init__(self, parent=None):
        super(DROWidget, self).__init__(parent)

        # self.axis_letter = axis_letter
        # self.axis_num = 'xyzabcuvw'.index(self.axis_letter.lower())
        # self.joint_num = self.coords.index(self.axis_letter   .lower())
        # self.dro_type = dro_type

        self._dro_type = 0                  # 0=>ABS, 1=>REL, 2=>DTG
        self._dro_number = 0                # Axis or Joint number
        self._metric_template = '%10.3f'
        self._imperial_template = '%9.4f'
        self.factor = 1

        self.setNum(0.1234)

        STATUS.axis_positions.connect(self.setPosition)
        STATUS.updateAxisPositions()

    @pyqtSlot(tuple)
    def setPosition(self, positions):
        pos = positions[self._dro_type][self._dro_number] * self.factor
        try:
            pos_str = self._imperial_template % pos
            self.setText(pos_str)
        except:
            self.setText("<font color='red'>Format ERROR!</font>")



    def _update_units(self, status, units):
        if units == self.machine_units:
            self.factor = 1
        else:
            self.factor = self.conversion_factor
        if units == Units.IN:
            self.dec_plcs = self.in_decimal_places
        else:
            self.dec_plcs = self.mm_decimal_places

    #--------------------
    # Designer methods
    # -------------------

    @pyqtSlot(int)
    def setAxis(self, value):
        self._dro_number = clamp(value, 0, 8)
        STATUS.updateAxisPositions()
        return False
    def getAxis(self):
        return self._dro_number
    axis_number = pyqtProperty(int, getAxis, setAxis)

    @pyqtSlot(int)
    def setReferenceType(self, value):
        self._dro_type = clamp(value, 0, 2)
        STATUS.updateAxisPositions()
    def getReferenceType(self):
        return self._dro_type
    reference_type = pyqtProperty(int, getReferenceType, setReferenceType)

    @pyqtSlot(str)
    def setMetricTemplate(self, value):
        self._metric_template = value
        STATUS.updateAxisPositions()
    def getMetricTemplate(self):
        return self._metric_template
    metric_template = pyqtProperty(str, getMetricTemplate, setMetricTemplate)

    @pyqtSlot(str)
    def setImperialTemplate(self, value):
        self._imperial_template = value
        STATUS.updateAxisPositions()
    def getImperialTemplate(self):
        return self._imperial_template
    imperial_template = pyqtProperty(str, getImperialTemplate, setImperialTemplate)


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    led = DROWidget()
    led.show()
    sys.exit(app.exec_())
