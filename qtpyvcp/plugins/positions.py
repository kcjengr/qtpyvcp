"""Smart Axis and Join positions plugin.

Calculates Absolute, Relative, and Distance-To-Go values for each axis.
Configurable to report actual or commanded positions and values in either
machine or program units.

Usage:
    Example syntax to use in Widget Rules Editor::

        position:axis?abs        # returns tuple of ABS positions
        position:axis?rel        # returns tuple of REL positions
        position:axis?dtg        # returns tuple of DTG values

ToDO:
    Add joint positions.
"""

import math

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import QtPyVCPDataPlugin, QtPyVCPDataChannel, getPlugin

STATUS = getPlugin('status')
STAT = STATUS.stat
INFO = Info()

# Set up logging
LOG = getLogger(__name__)

MACHINE_COORDS = INFO.getCoordinates()
MACHINE_UNITS = 2 if INFO.getIsMachineMetric() else 1

# Set the conversions used for changing the DRO units
# Only convert linear axes (XYZUVW), use factor of unity for ABC
if MACHINE_UNITS == 2:
    # List of factors for converting from mm to inches
    CONVERSION_FACTORS = [1.0 / 25.4] * 3 + [1] * 3 + [1.0 / 25.4] * 3
else:
    # List of factors for converting from inches to mm
    CONVERSION_FACTORS = [25.4] * 3 + [1] * 3 + [25.4] * 3


class AxisPositions(QtPyVCPDataChannel):
    """Axis Position Channel.

    Axis positions are updated every cycle (~50ms). To save computation
    resources cached values are returned instead of recalculating for each
    request.
    """
    def __init__(self):
        super(AxisPositions, self).__init__(description="Axis positions")

        self._report_actual = True
        self._positions = [[0.0]*9]*3

    @property
    def value(self):
        """Tuple of tuples. REL, ABS and DTG axis positions"""
        return self._positions

    @property
    def abs(self):
        """Tuple of ABS axis positions."""
        return self._positions[0]

    @property
    def rel(self):
        """Tuple of REL axis positions."""
        return self._positions[1]

    @property
    def dtg(self):
        """Tuple of DTG values for each axis"""
        return self._positions[2]

    def _update(self):

        if self._report_actual:
            pos = STAT.actual_position
        else:
            pos = STAT.position

        dtg = STAT.dtg
        g5x_offset = STAT.g5x_offset
        g92_offset = STAT.g92_offset
        tool_offset = STAT.tool_offset

        rel = [0] * 9
        for axis in INFO.AXIS_NUMBER_LIST:
            rel[axis] = pos[axis] - g5x_offset[axis] - tool_offset[axis]

        if STAT.rotation_xy != 0:
            t = math.radians(-STAT.rotation_xy)
            xr = rel[0] * math.cos(t) - rel[1] * math.sin(t)
            yr = rel[0] * math.sin(t) + rel[1] * math.cos(t)
            rel[0] = xr
            rel[1] = yr

        for axis in INFO.AXIS_NUMBER_LIST:
            rel[axis] -= g92_offset[axis]

        if STAT.program_units != MACHINE_UNITS:
            pos = [pos[anum] * CONVERSION_FACTORS[anum] for anum in range(9)]
            rel = [rel[anum] * CONVERSION_FACTORS[anum] for anum in range(9)]
            dtg = [dtg[anum] * CONVERSION_FACTORS[anum] for anum in range(9)]

        self._positions = tuple([tuple(pos), tuple(rel), tuple(dtg)])
        self.valueChanged.emit(self._positions)


class Position(QtPyVCPDataPlugin):

    protocol = 'position'

    axis = AxisPositions()

    def __init__(self, report_actual_pos=True, use_program_units=True):
        super(Position, self).__init__()

        self._report_actual_pos = report_actual_pos
        self._use_program_units = use_program_units

        self.axis._update()

        # all these should cause the positions to update
        STATUS.position.onValueChanged(self.axis._update)
        STATUS.g5x_offset.onValueChanged(self.axis._update)
        STATUS.g92_offset.onValueChanged(self.axis._update)
        STATUS.tool_offset.onValueChanged(self.axis._update)
        STATUS.program_units.onValueChanged(self.axis._update)

    @property
    def report_actual(self):
        """Whether to report the actual position. Default True."""
        return self._report_actual_pos

    @report_actual.setter
    def report_actual(self, report_actual_pos):
        if report_actual_pos == self._report_actual_pos:
            return
        self._report_actual_pos = report_actual_pos

        if self._report_actual_pos:
            # disconnect commanded pos update signals
            STATUS.position.valueChanged.disconect(self.axis._update)
            STATUS.joint_position.valueChanged.disconnect(self.joint._update)
            # connect actual pos update signals
            STATUS.actual_position.valueChanged.connect(self.axis._update)
            STATUS.joint_actual_position.valueChanged.connect(self.joint._update)
        else:
            # disconnect actual pos update signals
            STATUS.actual_position.valueChanged.disconnect(self.axis._update)
            STATUS.joint_actual_position.valueChanged.disconnect(self.joint._update)
            # connect commanded pos update signals
            STATUS.position.valueChanged.connect(self.axis._update)
            STATUS.joint_position.valueChanged.connect(self.joint._update)


