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

from qtpy.QtWidgets import QLabel
from qtpy.QtCore import Slot, Property

from qtpyvcp.plugins import getPlugin
STATUS = getPlugin('status')

from qtpyvcp.core import Info
INFO = Info()

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.enums import Axis, ReferenceType, Units

IN_DESIGNER = os.getenv('DESIGNER') != None

class DROWidget(QLabel, VCPWidget, Axis, ReferenceType, Units):

    if IN_DESIGNER:
        from PyQt5.QtCore import Q_ENUMS
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
        STATUS.program_units.onValueChanged(self.updateUnits)
        STATUS.updateAxisPositions()
        self.updateUnits(STATUS.stat.program_units)

    @Slot(tuple)
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

    #==========================================================================
    # Designer property Getters/Setters
    #==========================================================================

    def getReferenceType(self):
        return self._type
    @Slot(ReferenceType)
    def setReferenceType(self, ref_type):
        self._type = ref_type
        STATUS.updateAxisPositions()
    reference_type = Property(ReferenceType, getReferenceType, setReferenceType)

    def getAxis(self):
        return self._axis
    @Slot(Axis)
    def setAxis(self, axis):
        self._axis = axis
        STATUS.updateAxisPositions()
    axis = Property(Axis, getAxis, setAxis)

    def getUnits(self):
        return self._units
    @Slot(Units)
    def setUnits(self, units):
        self._units = units
        self.updateUnits(STATUS.stat.program_units)
    units = Property(Units, getUnits, setUnits)

    def getDiamterMode(self):
        return self._diameter_mode
    @Slot(bool)
    def setDiamterMode(self, diameter_mode):
        self._diameter_mode = diameter_mode
        self.updateUnits(STATUS.stat.program_units)
    diameter_mode = Property(bool, getDiamterMode, setDiamterMode)

    def getMetricTemplate(self):
        return self._metric_template
    @Slot(str)
    def setMetricTemplate(self, value):
        self._metric_template = value
        STATUS.updateAxisPositions()
    metric_template = Property(str, getMetricTemplate, setMetricTemplate)

    def getImperialTemplate(self):
        return self._imperial_template
    @Slot(str)
    def setImperialTemplate(self, value):
        self._imperial_template = value
        STATUS.updateAxisPositions()
    imperial_template = Property(str, getImperialTemplate, setImperialTemplate)

    @Slot(float)
    def setTest(self, value):
        print value
    def getTest(self):
        return 2.0
    test = Property(float, getTest, setTest)

if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DROWidget()
    w.show()
    sys.exit(app.exec_())
