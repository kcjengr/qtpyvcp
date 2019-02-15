import os
import time
import linuxcnc

from qtpy.QtCore import QTimer, Signal

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.prefs import Prefs

INFO = Info()
PREFS = Prefs()

LOG = getLogger(__name__)
STAT = linuxcnc.stat()


class Status(DataPlugin):

    stat = STAT

    def __init__(self, cycle_time=100):
        super(Status, self).__init__()

        self.no_force_homing = INFO.noForceHoming()

        self.max_recent_files = PREFS.getPref("STATUS", "MAX_RECENT_FILES", 10, int)
        files = PREFS.getPref("STATUS", "RECENT_FILES", [], list)
        self.recent_files = [file for file in files if os.path.exists(file)]

        self.jog_increment = 0  # jog
        self.step_jog_increment = INFO.getIncrements()[0]
        self.jog_mode = True
        self.linear_jog_velocity = INFO.getJogVelocity()
        self.angular_jog_velocity = INFO.getJogVelocity()

        try:
            STAT.poll()
        except:
            pass

        excluded_items = ['axis', 'joint', 'spindle', 'poll', 'command', 'debug']

        self.old = {}
        # initialize the old values dict
        for item in dir(STAT):
            if item in self.channels:
                self.channels[item].value = getattr(STAT, item)
            elif item not in excluded_items and not item.startswith('_'):
                chan = DataChannel(doc=item, data=getattr(STAT, item))
                self.channels[item] = chan
                setattr(self, item, chan)

        self.homed.notify(self.all_axes_homed.setValue)

        # Set up the periodic update timer
        self.timer = QTimer()
        self._cycle_time = cycle_time
        self.timer.timeout.connect(self._periodic)

        self.on.settable = True
        self.task_state.notify(lambda ts:
                               self.on.setValue(ts == linuxcnc.STATE_ON))

    recent_files = DataChannel(doc='List of recently loaded files', settable=True, data=[])

    @DataChannel
    def on(self):
        """True if machine power is ON."""
        return STAT.task_state == linuxcnc.STATE_ON

    @DataChannel
    def file(self):
        """Currently loaded file."""
        return self.file.value or 'No file loaded'

    @file.setter
    def file(self, fname):
        if STAT.interp_state == linuxcnc.INTERP_IDLE \
                and STAT.call_level == 0:
            self.file.value = fname
            self.signal.emit(fname)

    @DataChannel
    def task_state(self, query=None):
        """Current status of task

        1) E-Stop
        2) Reset
        3) Off
        4) On

        To return the string in a status label::

            status:task_state?string

        :returns: current task state
        :rtype: int, str
        """
        return STAT.task_state

    @task_state.tostring
    def task_state(self):
        task_states = {0: "N/A",
                       linuxcnc.STATE_ESTOP: "E-Stop",
                       linuxcnc.STATE_ESTOP_RESET: "Reset",
                       linuxcnc.STATE_ON: "On",
                       linuxcnc.STATE_OFF: "Off"}

        return task_states[STAT.task_state]

    @DataChannel
    def motion_mode(self):
        """Current motion controller mode

        1) Free
        2) Coord
        3) Teleop

        To return the string in a status label::

            status:motion_mode?string

        :returns: current motion mode
        :rtype: int, str
        """
        return STAT.motion_mode

    @motion_mode.tostring
    def motion_mode(self):
        modes = {0: "N/A",
                  linuxcnc.TRAJ_MODE_COORD: "Coord",
                  linuxcnc.TRAJ_MODE_FREE: "Free",
                  linuxcnc.TRAJ_MODE_TELEOP: "Teleop"}

        return modes[STAT.motion_mode]

    @DataChannel
    def state(self):
        """Current command execution status

        1) Done
        2) Exec
        3) Error

        To return the string in a status label::

            status:state?string

        :returns: current command execution state
        :rtype: int, str
        """
        return STAT.state

    @state.tostring
    def state(self):
        states = {0: "N/A",
                       linuxcnc.RCS_DONE: "Done",
                       linuxcnc.RCS_EXEC: "Exec",
                       linuxcnc.RCS_ERROR: "Error"}

        return states[STAT.state]

    @DataChannel
    def exec_state(self):
        """Current task execution state

        1) Error
        2) Done
        3) Waiting for Motion
        4) Waiting for Motion Queue
        5) Waiting for Pause
        6) --
        7) Waiting for Motion and IO
        8) Waiting for Delay
        9) Waiting for system CMD
        10) Waiting for spindle orient

        To return the string in a status label::

            status:exec_state?string

        :returns: current task execution error
        :rtype: int, str
        """
        return STAT.exec_state

    @exec_state.tostring
    def exec_state(self):
        exec_states = {0: "N/A",
                        linuxcnc.EXEC_ERROR: "Error",
                        linuxcnc.EXEC_DONE: "Done",
                        linuxcnc.EXEC_WAITING_FOR_MOTION: "Waiting for Motion",
                        linuxcnc.EXEC_WAITING_FOR_MOTION_QUEUE: "Waiting for Motion Queue",
                        linuxcnc.EXEC_WAITING_FOR_IO: "Waiting for Pause",
                        linuxcnc.EXEC_WAITING_FOR_MOTION_AND_IO: "Waiting for Motion and IO",
                        linuxcnc.EXEC_WAITING_FOR_DELAY: "Waiting for Delay",
                        linuxcnc.EXEC_WAITING_FOR_SYSTEM_CMD: "Waiting for system CMD",
                        linuxcnc.EXEC_WAITING_FOR_SPINDLE_ORIENTED: "Waiting for spindle orient"}

        return exec_states[STAT.exec_state]

    @DataChannel
    def task_mode(self):
        """Current task mode

        1) Manual
        2) Auto
        3) MDI

        To return the string in a status label::

            status:task_mode?string

        :returns: current task mode
        :rtype: int, str
        """
        return STAT.task_mode

    @task_mode.tostring
    def task_mode(self):
        task_modes = {0: "N/A",
                       linuxcnc.MODE_MANUAL: "Manual",
                       linuxcnc.MODE_AUTO: "Auto",
                       linuxcnc.MODE_MDI: "MDI"}

        return task_modes[STAT.task_mode]

    @DataChannel
    def motion_type(self, query=None):
        """Motion type

        0) None
        1) Traverse
        2) Linear Feed
        3) Arc Feed
        4) Tool Change
        5) Probing
        6) Rotary Index

        To return the string in a status label::

            status:motion_type?string

        :returns:  current motion type
        :rtype: int, str
        """
        return STAT.motion_type

    @motion_type.tostring
    def motion_type(self):
        motion_types = {0: "None",
                        linuxcnc.MOTION_TYPE_TRAVERSE: "Traverse",
                        linuxcnc.MOTION_TYPE_FEED: "Linear Feed",
                        linuxcnc.MOTION_TYPE_ARC: "Arc Feed",
                        linuxcnc.MOTION_TYPE_TOOLCHANGE: "Tool Change",
                        linuxcnc.MOTION_TYPE_PROBING: "Probing",
                        linuxcnc.MOTION_TYPE_INDEXROTARY: "Rotary Index"}

        return motion_types[STAT.motion_type]

    @DataChannel
    def interp_state(self):
        """Current state of RS274NGC interpreter

        1) Idle
        2) Reading
        3) Paused
        4) Waiting

        To return the string in a status label::

            status:interp_state?string

        :returns: RS274 interpreter state
        :rtype: int, str
        """
        return STAT.interp_state

    @interp_state.tostring
    def interp_state(self):
        interp_states = {0: "N/A",
                            linuxcnc.INTERP_IDLE: "Idle",
                            linuxcnc.INTERP_READING: "Reading",
                            linuxcnc.INTERP_PAUSED: "Paused",
                            linuxcnc.INTERP_WAITING: "Waiting"}

        return interp_states[STAT.interp_state]


    @DataChannel
    def interpreter_errcode(self):
        """Current RS274NGC interpreter return code

        0) Ok
        1) Exit
        2) Finished
        3) Endfile
        4) File not open
        5) Error

        To return the string in a status label::

            status:interpreter_errcode?string

        :returns: interp error code
        :rtype: int, str
        """
        return STAT.interpreter_errcode

    @interpreter_errcode.tostring
    def interpreter_errcode(self):
        interpreter_errcodes = {0: "Ok",
                                1: "Exit",
                                2: "Finished",
                                3: "Endfile",
                                4: "File not open",
                                5: "Error"}

        return interpreter_errcodes[STAT.interpreter_errcode]

    @DataChannel
    def program_units(self):
        """Program units

        Available as an integer, or in short or long string formats.

        1) in, Inches
        2) mm, Millimeters
        3) cm, Centimeters

        To return the string in a status label::

            status:program_units
            status:program_units?string
            status:program_units?string&format=long

        :returns: current program units
        :rtype: int, str
        """
        return STAT.program_units

    @program_units.tostring
    def program_units(self, format='short'):
        if format == 'short':
            return ["N/A", "in", "mm", "cm"][STAT.program_units]
        else:
            return ["N/A", "Inches", "Millimeters", "Centimeters"][STAT.program_units]

    @DataChannel
    def homed(self, anum=None):
        """Axis homed status

        If no axis number is specified returns a tuple of integers.
        If ``anum`` is specified returns True if the axis is homed, else False.

        Rules syntax::

            status:homed
            status:homed?anum=0

        Args:
         anum (int, optional) : the axis number to return the homed state of.

        :returns: axis homed states
        :rtype: tuple, bool

        """
        if anum is None:
            return STAT.homed
        return bool(STAT.homed[int(anum)])

    @DataChannel
    def all_axes_homed(self):
        """All axes homed status

        True if all axes are homed or if [TRAJ]NO_FORCE_HOMING set in INI.

        :returns: all homed
        :rtype: bool
        """
        if self.no_force_homing:
            self.all_axes_homed.value = True
        else:
            for anum in INFO.AXIS_NUMBER_LIST:
                if STAT.homed[anum] is not 1:
                    self.all_axes_homed.value = False
                    break
            else:
                self.all_axes_homed.value = True
        return self.all_axes_homed.value

    # this is used by File "qtpyvcp/qtpyvcp/actions/program_actions.py",
    # line 83, in _run_ok elif not STATUS.allHomed():

    def allHomed(self):
        if self.no_force_homing:
            return True
        for jnum in range(STAT.joints):
            if not STAT.joint[jnum]['homed']:
                return False
        return True

    def initialise(self):
        """Start the periodic update timer."""
        LOG.debug("Starting periodic updates with %ims cycle time",
                  self._cycle_time)
        self.timer.start(self._cycle_time)

    def terminate(self):
        """Save persistent settings on terminate."""
        PREFS.setPref("STATUS", "RECENT_FILES", self.recent_files.value)
        PREFS.setPref("STATUS", "MAX_RECENT_FILES", self.max_recent_files)

    def _periodic(self):

        # s = time.time()

        try:
            STAT.poll()
        except Exception:
            LOG.warning("Status polling failed, is LinuxCNC running?", exc_info=True)
            self.timer.stop()
            return

        for self, chan_obj in self.channels.iteritems():
            new_value = getattr(STAT, self, None)
            if new_value is None:
                continue
            if chan_obj.value != new_value:
                # update the status items
                chan_obj.value = new_value
                chan_obj.signal.emit(new_value)

        # print time.time() - s


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])

    s = Status()

    def onInterpStateChanged(*args, **kwargs):
        print 'Interp State:', s.interp_state

    def onTaskStateChanged(*args, **kwargs):
        print 'Task State:', s.task_state

    s.interp_state.notify(onInterpStateChanged)
    s.task_state.notify(onTaskStateChanged)

    s.initialise()

    app.exec_()
