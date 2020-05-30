"""
DROBaseWidget
-------------

"""

from qtpy.QtCore import Slot, Property

from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

class Axis(object):
    ALL = -1
    X, Y, Z, A, B, C, U, V, W = range(9)


class Units(object):
    Program = 0  # Use program units
    Inch = 1     # CANON_UNITS_INCHES=1
    Metric = 2   # CANON_UNITS_MM=2


class RefType(object):
    Absolute = 0
    Relative = 1
    DistanceToGo = 2

    @classmethod
    def toString(self, ref_type):
        return ['abs', 'rel', 'dtg'][ref_type]


class DROBaseWidget(VCPWidget):
    """DROBaseWidget

    This class implements the basic functionality needed for DRO widgets.

    """

    def __init__(self):
        super(DROBaseWidget, self).__init__()

        self.status = getPlugin('status')
        self.pos = getPlugin('position')

        self._anum = Axis.X
        self._ref_typ = RefType.Relative
        self._mm_fmt = '%10.3f'
        self._in_fmt = '%9.4f'

        self._fmt = self._in_fmt

        self.updateValue()

        self.status.program_units.notify(self.updateUnits, 'string')

    def updateUnits(self, units=None):
        """Force update of DRO display units.

        Args:
            units (str) : Display unis, either `in` or `mm`. Optional
                If no unit type is specified the current program units will
                be used.
        """
        if units is None:
            units = str(self.status.program_units)

        if units == 'in':
            self._fmt = self._in_fmt
        else:
            self._fmt = self._mm_fmt

        # force update
        self.updateValue()

    def initialize(self):
        getattr(self.pos, RefType.toString(self._ref_typ)).notify(self.updateValue)
        self.updateValue()

    def updateValue(self, pos=None):
        """Refresh displayed text, used in designer."""
        if pos is None:
            pos = getattr(self.pos, RefType.toString(self._ref_typ)).getValue()
        self.setText(self._fmt % pos[self._anum])

    @Property(int)
    def referenceType(self):
        return self._ref_typ

    @referenceType.setter
    def referenceType(self, ref_type):
        self._ref_typ = ref_type
        self.updateValue()

    @Property(int)
    def axisNumber(self):
        return self._anum

    @axisNumber.setter
    def axisNumber(self, axis):
        self._anum = axis
        self.updateValue()

    @Property(str)
    def inchFormat(self):
        return self._in_fmt

    @inchFormat.setter
    def inchFormat(self, inch_format):
        self._in_fmt = inch_format
        self.updateUnits()

    @Property(str)
    def metricFormat(self):
        return self._mm_fmt

    @metricFormat.setter
    def metricFormat(self, metric_format):
        self._mm_fmt = metric_format
        self.updateUnits()
