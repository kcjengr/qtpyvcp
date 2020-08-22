"""
DROBaseWidget
-------------

"""

from enum import IntEnum

from qtpy.QtCore import Slot, Property

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import getSetting

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger

from qtpyvcp.utilities.info import Info

LOG = logger.getLogger(__name__)
INFO = Info()


class Axis(IntEnum):
    ALL = -1
    X, Y, Z, A, B, C, U, V, W = range(9)


class Units(IntEnum):
    Program = 0  # Auto based on G20/G21
    Inch = 1     # Always show inch units
    Metric = 2   # Always show metric units


class RefType(IntEnum):
    Absolute = 0      # Relative to G53
    Relative = 1      # Relative to current WCS
    DistanceToGo = 2  # Remaining distance of the current move


class LatheMode(IntEnum):
    Auto = 0      # Auto based on G7/G8
    Radius = 1    # Always show radius
    Diameter = 2  # Always show diameter


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
        self._deg_fmt = '%10.2f' #'%(deg) %(min)\' %(sec)"'

        self._use_global_fmt_settings = True

        # settings
        self.in_fmt_setting = None
        self.mm_fmt_setting = None
        self.deg_fmt_setting = None
        self.lathe_mode_setting = None

        self._angular_axis = False

        # lathe
        self._is_lathe = INFO.getIsLathe()
        self._g7_active = False
        self._lathe_mode = LatheMode.Auto  # latheDiameterMode

        self._fmt = self._in_fmt
        self._input_type = 'number:float'

        self.updateValue()

        self.status.program_units.notify(self.updateUnits, 'string')

    def updateUnits(self, units=None):
        """Force update of DRO display units.

        Args:
            units (str) : Display unis, either `in` or `mm`. Optional
                If no unit type is specified the current program units will
                be used.
        """

        if self._angular_axis:
            self._fmt = self._deg_fmt

        else:
            if units is None:
                units = str(self.status.program_units)

            if units == 'in':
                self._fmt = self._in_fmt
            else:
                self._fmt = self._mm_fmt

        # force update
        self.updateValue()

    def initialize(self):
        getattr(self.pos, self._ref_typ.name).notify(self.updateValue)
        self.updateValue()

        if self._is_lathe:
            self.status.gcodes.notify(self.updateDiameterMode)

        if self._use_global_fmt_settings:

            self.in_fmt_setting = getSetting('dro.inch-format')
            self.mm_fmt_setting = getSetting('dro.millimeter-format')
            self.deg_fmt_setting = getSetting('dro.degree-format')
            self.lathe_mode_setting = getSetting('dro.lathe-radius-mode')

            try:
                self.in_fmt_setting.notify(self.setInchFormat)
                self.mm_fmt_setting.notify(self.setMillimeterFormat)
                self.deg_fmt_setting.notify(self.setDegreeFormat)
                self.lathe_mode_setting.notify(self.setLatheMode)

            except AttributeError:  # settings not found
                pass

    def updateDiameterMode(self, gcodes):
        self._g7_active = 'G7' in gcodes
        self.updateValue()

    def updateValue(self, pos=None):
        """Update the displayed position."""
        if pos is None:
            pos = getattr(self.pos, self._ref_typ.name).getValue()

        if self._is_lathe and self._anum == Axis.X:
            if self._lathe_mode == LatheMode.Diameter or \
                    (self._lathe_mode == LatheMode.Auto and self._g7_active):
                self.setText(self._fmt % (pos[self._anum] * 2))
            else:
                self.setText(self._fmt % pos[self._anum])

        else:
            self.setText(self._fmt % pos[self._anum])

    @Property(int)
    def referenceType(self):
        return self._ref_typ

    @referenceType.setter
    def referenceType(self, ref_type):
        self._ref_typ = RefType(ref_type)
        self.updateValue()

    @Property(int)
    def axisNumber(self):
        return self._anum

    @axisNumber.setter
    def axisNumber(self, axis):
        self._anum = axis
        if axis in [3, 4, 5]:
            self._angular_axis = True
            self._fmt = self._deg_fmt
        self.updateValue()

    @Property(str)
    def inchFormat(self):
        return self._in_fmt

    @inchFormat.setter
    def inchFormat(self, in_fmt):
        if in_fmt == '' and self.mm_fmt_setting:
            self.in_fmt_setting.resetValue()

        else:
            try:
                txt = in_fmt % 360.42
                self._in_fmt = in_fmt
            except:
                if self.in_fmt_setting:
                    self.in_fmt_setting.setValue(self._in_fmt)

        self.updateUnits()

    @Slot(str)
    @Slot(object)
    def setInchFormat(self, fmt):
        self.inchFormat = fmt

    @Property(str)
    def millimeterFormat(self):
        return self._mm_fmt

    @millimeterFormat.setter
    def millimeterFormat(self, mm_fmt):
        if mm_fmt == '' and self.mm_fmt_setting:
            self.mm_fmt_setting.resetValue()

        else:
            try:
                txt = mm_fmt % 360.42
                self._mm_fmt = mm_fmt
            except:
                if self.mm_fmt_setting:
                    self.mm_fmt_setting.setValue(self._mm_fmt)

        self.updateUnits()

    @Slot(str)
    @Slot(object)
    def setMillimeterFormat(self, fmt):
        self.millimeterFormat = fmt

    # ToDO: Add support for DMS angle notation
    # https://stackoverflow.com/questions/2579535
    @Property(str)
    def degreeFormat(self):
        return self._deg_fmt

    @degreeFormat.setter
    def degreeFormat(self, deg_fmt):

        if deg_fmt == '' and self.deg_fmt_setting:
            self.deg_fmt_setting.resetValue()

        else:
            try:
                txt = deg_fmt % 360.42
                self._deg_fmt = deg_fmt
            except:
                if self.deg_fmt_setting:
                    self.deg_fmt_setting.setValue(self._deg_fmt)

        self.updateUnits()

    @Slot(str)
    @Slot(object)
    def setDegreeFormat(self, fmt):
        self.degreeFormat = fmt

    @Property(bool)
    def useGlobalDroFormatSettings(self):
        return self._use_global_fmt_settings

    @useGlobalDroFormatSettings.setter
    def useGlobalDroFormatSettings(self, use_fmt_settings):
        self._use_global_fmt_settings = use_fmt_settings

    @Property(int)
    def latheMode(self):
        return self._lathe_mode

    @latheMode.setter
    def latheMode(self, mode):
        self._lathe_mode = LatheMode(mode)
        self.updateValue()

    @Property(str)
    def inputType(self):
        return self._input_type

    @inputType.setter
    def inputType(self, input_type):
        self._input_type = input_type

    @Slot(int)
    @Slot(object)
    def setLatheMode(self, mode):
        self.latheMode = LatheMode(mode)

    @Slot()
    def latheDiameterMode(self):
        self.latheMode = LatheMode.Diameter

    @Slot()
    def latheRadiusMode(self):
        self.latheMode = LatheMode.Radius

    @Slot()
    def latheAutoMode(self):
        self.latheMode = LatheMode.Auto
