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

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QEvent, pyqtSlot, pyqtProperty, Q_ENUMS

from QtPyVCP.core import Status, Action, Info
STATUS = Status()
ACTION = Action()
INFO = Info()

from QtPyVCP.enums import Axis, ReferenceType, Units

class DROWidget(QLabel, Axis, ReferenceType, Units):

    Q_ENUMS(Axis)
    Q_ENUMS(ReferenceType)
    Q_ENUMS(Units)

    coords = INFO.getCoordinates()
    machine_metric = INFO.getIsMachineMetric()

    # Set the conversions used for changing the DRO units
    # Only convert linear axes (XYZUVW), use factor of unity for ABC
    if machine_metric:
        # List of factors for converting from mm to inches
        CONVERSION_FACTORS = [1.0/25.4]*3 + [1]*3 + [1.0/25.4]*3
    else:
        # List of factors for converting from inches to mm
        CONVERSION_FACTORS = [25.4]*3 + [1]*3 + [25.4]*3

    def __init__(self, parent=None):
        super(DROWidget, self).__init__(parent)

        # self.axis_letter = axis_letter
        # self.axis_num = 'xyzabcuvw'.index(self.axis_letter.lower())
        # self.joint_num = self.coords.index(self.axis_letter   .lower())
        # self.dro_type = dro_type

        self._axis = Axis.X
        self._type = ReferenceType.Absolute
        self._units = Units.Program
        self._diameter_mode = False

        self._metric_template = '%10.3f'
        self._imperial_template = '%9.4f'

        self._temp = self._imperial_template
        self._factor = 1

        self.setNum(0.1234)

        STATUS.axis_positions.connect(self.setPosition)
        STATUS.program_units.connect(self.updateUnits)
        STATUS.updateAxisPositions()
        self.updateUnits(STATUS.stat.program_units)

    @pyqtSlot(tuple)
    def setPosition(self, positions):
        pos = positions[self._type][self._axis] * self._factor
        try:
            pos_str = self._temp % pos
            self.setText(pos_str)
        except:
            self.setText("<font color='red'>Format ERROR!</font>")

    def updateUnits(self, units):
        if self._units == Units.Program:
            if units == Units.Inch:
                self._temp = self._imperial_template
                if self.machine_metric:
                    self._factor = self.CONVERSION_FACTORS[self._axis]
                else:
                    self._factor = 1
            else:
                self._temp = self.metric_template
                if self.machine_metric:
                    self._factor = 1
                else:
                    self._factor = self.CONVERSION_FACTORS[self._axis]
        elif self._units == Units.Metric:
            self._temp = self._metric_template
            if self.machine_metric:
                self._factor = 1
            else:
                self._factor = self.CONVERSION_FACTORS[self._axis]
        else:
            self._temp = self._imperial_template
            if self.machine_metric:
                self._factor = self.CONVERSION_FACTORS[self._axis]
            else:
                self._factor = 1

        if self._diameter_mode and self._axis == 0:
            self._factor *= 2

        STATUS.updateAxisPositions()

    #--------------------
    # Designer methods
    # -------------------

    def getReferenceType(self):
        return self._type
    @pyqtSlot(ReferenceType)
    def setReferenceType(self, ref_type):
        self._type = ref_type
        STATUS.updateAxisPositions()
    reference_type = pyqtProperty(ReferenceType, getReferenceType, setReferenceType)

    def getAxis(self):
        return self._axis
    @pyqtSlot(Axis)
    def setAxis(self, axis):
        self._axis = axis
        STATUS.updateAxisPositions()
    axis = pyqtProperty(Axis, getAxis, setAxis)

    def getUnits(self):
        return self._units
    @pyqtSlot(Units)
    def setUnits(self, units):
        self._units = units
        self.updateUnits(STATUS.stat.program_units)
    units = pyqtProperty(Units, getUnits, setUnits)

    @pyqtSlot(bool)
    def setDiamterMode(self, diameter_mode):
        self._diameter_mode = diameter_mode
        self.updateUnits(STATUS.stat.program_units)
    def getDiamterMode(self):
        return self._diameter_mode
    diameter_mode = pyqtProperty(bool, getDiamterMode, setDiamterMode)

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

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    led = DROWidget()
    led.show()
    sys.exit(app.exec_())
