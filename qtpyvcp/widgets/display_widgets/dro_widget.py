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
POSITION = getPlugin('position')

from qtpyvcp.widgets import VCPWidget

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER') != None

class Axis(object):
    ALL = -1
    X, Y, Z, A, B, C, U, V, W = range(9)

class Units(object):
    Program = 0 # Use program units
    Inch = 1    # CANON_UNITS_INCHES=1
    Metric = 2  # CANON_UNITS_MM=2

class RefType(object):
    Absolute = 0
    Relative = 1
    DistanceToGo = 2

    @classmethod
    def toString(self, ref_type):
        return ['abs', 'rel', 'dtg'][ref_type]

class DROWidget(QLabel, VCPWidget, Axis, RefType, Units):

    from PyQt5.QtCore import Q_ENUMS
    Q_ENUMS(Axis)
    Q_ENUMS(RefType)
    Q_ENUMS(Units)

    def __init__(self, parent=None):
        super(DROWidget, self).__init__(parent)

        self.log = logger.getLogger(__name__)

        self._axis_number = Axis.X
        self._ref_typ = RefType.Absolute

        self._metric_format = '%10.3f'
        self._imperial_format = '%9.4f'
        self._format = self._imperial_format

        self.update(POSITION.abs.getValue())
        STATUS.program_units.notify(self.onUnitsChanged, 'string')

    def update(self, pos):
        self.setText(self._format % pos[self._axis_number])

    def onUnitsChanged(self, units):
        if units == 'in':
            self._format = self._imperial_format
        else:
            self._format = self._metric_format
        self.update(getattr(POSITION, RefType.toString(self._ref_typ)).getValue())

    def initialize(self):
        getattr(POSITION, RefType.toString(self._ref_typ)).notify(self.update)

    # ==========================================================================
    # Designer property Getters/Setters
    # ==========================================================================

    @Property(RefType)
    def referenceType(self):
        return self._ref_typ

    @referenceType.setter
    def referenceType(self, ref_typ):
        new_ref_typ = RefType.toString(ref_typ)
        self._ref_typ = ref_typ
        self.update(getattr(POSITION, new_ref_typ).getValue())

    @Property(Axis)
    def axis(self):
        return self._axis_number

    @axis.setter
    def axis(self, axis):
        self._axis_number = axis
        self.update(getattr(POSITION, RefType.toString(self._ref_typ)).getValue())

    def getDiamterMode(self):
        return self._diameter_mode
    @Slot(bool)
    def setDiamterMode(self, diameter_mode):
        self._diameter_mode = diameter_mode
        self.updateUnits(STATUS.stat.program_units)

    @Property(str)
    def metricTemplate(self):
        return self._metric_format

    @metricTemplate.setter
    def metricTemplate(self, value):
        try:
            value % 12.456789
        except ValueError as va:
            self.log.debug(va)
            return
        self._metric_format = value
        self._format = self._metric_format
        self.update(getattr(POSITION, RefType.toString(self._ref_typ)).getValue())

    @Property(str)
    def imperialTemplate(self):
        return self._imperial_format

    @imperialTemplate.setter
    def imperialTemplate(self, value):
        try:
            value % 12.456789
        except ValueError as va:
            self.log.debug(va)
            return
        self._imperial_format = value
        self._format = self._imperial_format
        self.update(getattr(POSITION, RefType.toString(self._ref_typ)).getValue())

if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DROWidget()
    w.show()
    sys.exit(app.exec_())
