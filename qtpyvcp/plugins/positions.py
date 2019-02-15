"""Smart Axis and Join positions plugin.

Calculates Absolute, Relative, and Distance-To-Go values for each axis.
Configurable to report actual or commanded positions and values in either
machine or program units.

Usage:
    Example syntax to use in Widget Rules Editor::

        position:abs?string&axis=x        # returns X axis absolute position
        position:rel?string&axis=x        # returns X axis relative position
        position:dtg?string&axis=x        # returns X axis DTG value

ToDO:
    Add joint positions.
"""

import math

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

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


class Position(DataPlugin):
    """Positions Plugin"""
    def __init__(self, report_actual_pos=True, use_program_units=True,
                 metric_format='%9.3f', imperial_format='%8.4f'):
        super(Position, self).__init__()

        self._report_actual_pos = report_actual_pos
        self._use_program_units = use_program_units
        self._metric_format = metric_format
        self._imperial_format = imperial_format

        self._current_format = self._imperial_format

        self._update()

        # all these should cause the positions to update
        STATUS.position.onValueChanged(self._update)
        STATUS.g5x_offset.onValueChanged(self._update)
        STATUS.g92_offset.onValueChanged(self._update)
        STATUS.tool_offset.onValueChanged(self._update)
        STATUS.program_units.onValueChanged(self.updateUnits)

    def getChannel(self, url):
        """Get data channel from URL.

        Args:
            url (str) : The URL of the channel to get.

        Returns:
            tuple : (chan_obj, chan_exp)
        """

        chan, sep, query = url.partition('?')
        raw_args = query.split('&')

        args = []
        kwargs = {}
        for arg in [a for a in raw_args if a != '']:
            if '=' in arg:
                key, val = arg.split('=')
                kwargs[key] = val
            else:
                args.append(arg)

        try:
            chan_obj = self.channels[chan]

            if 'axis' in kwargs:
                axis = kwargs.pop('axis')
                try:
                    kwargs['anum'] = int(axis)
                except ValueError:
                    kwargs['anum'] = 'xyzabcuvw'.index(str(axis).lower())

            if len(args) > 0 and args[0] in ('string', 'text', 'str'):
                chan_exp = lambda: chan_obj.getString(*args[1:], **kwargs)
            else:
                chan_exp = lambda: chan_obj.getValue(*args, **kwargs)

        except (KeyError, SyntaxError):
            LOG.exception('Error getting channel')
            return None, None

        return chan_obj, chan_exp

    def updateUnits(self, canon_units):
        print 'updating units', canon_units
        if canon_units == 2:
            self._current_format = self._metric_format
        else:
            self._current_format = self._imperial_format

        self._update()

    @DataChannel
    def rel(self, anum=-1):
        """The current relative axis positions including all offsets

        To get a single axis pass string and the axis letter::

            position:rel?string&axis=x

        To get a tuple of all the axes pass only string::

            position:rel?

        :returns: current relative axis positions including all offsets
        :rtype: tuple, str
        """

        if anum == -1:
            return self.rel.value
        return self.rel.value[anum]

    @rel.tostring
    def rel(self, anum):
        return self._current_format % self.rel.value[anum]

    @DataChannel
    def abs(self, anum=-1):
        """The current absolute axis positions

        To get a single axis pass string and the axis letter::

            position:abs?string&axis=x

        To get a tuple of all the axes pass only string::

            position:abs?

        :returns: current absolute axis positions
        :rtype: tuple, str
        """

        if anum == -1:
            return self.abs.value
        return self.abs.value[anum]

    @abs.tostring
    def abs(self, anum):
        return self._current_format % self.abs.value[anum]


    @DataChannel
    def dtg(self, anum=-1):
        """The remaining distance-to-go for the current move

        To get a single axis pass string and the axis letter::

            position:dtg?string&axis=x

        To get a tuple of all the axes pass only string::

            position:dtg?

        :returns: remaining distance-to-go for the current move
        :rtype: tuple, str
        """

        if anum == -1:
            return self.dtg.value
        return self.dtg.value[anum]

    @dtg.tostring
    def dtg(self, anum):
        return self._current_format % self.dtg.value[anum]

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

    def _update(self):

        if self._report_actual_pos:
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

        # self._positions = tuple([tuple(pos), tuple(rel), tuple(dtg)])
        # self.valueChanged.emit(self._positions)

        self.rel.setValue(tuple(rel))
        self.abs.setValue(tuple(pos))
        self.dtg.setValue(tuple(dtg))
