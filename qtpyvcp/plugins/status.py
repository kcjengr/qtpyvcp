import os
import time
import linuxcnc

from qtpy.QtCore import QTimer, Signal, QFileSystemWatcher

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.prefs import Prefs

INFO = Info()
PREFS = Prefs()

LOG = getLogger(__name__)
STAT = linuxcnc.stat()
CMD = linuxcnc.command()


class Status(DataPlugin):

    stat = STAT

    def __init__(self, cycle_time=100):
        super(Status, self).__init__()

        self.no_force_homing = INFO.noForceHoming()

        self.file_watcher = None

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
        # initialize data channels
        for item in dir(STAT):
            if item in self.channels:
                self.old[item] = getattr(STAT, item)
                self.channels[item].setValue(getattr(STAT, item))
            elif item not in excluded_items and not item.startswith('_'):
                self.old[item] = getattr(STAT, item)
                chan = DataChannel(doc=item)
                chan.setValue(getattr(STAT, item))
                self.channels[item] = chan
                setattr(self, item, chan)

        # add joint status channels
        self.joint = tuple(JointStatus(jnum) for jnum in range(9))
        for joint in self.joint:
            for chan, obj in joint.channels.items():
                self.channels['joint.{}.{}'.format(joint.jnum, chan)] = obj

        # add spindle status channels
        self.spindle = tuple(SpindleStatus(snum) for snum in range(8))
        for spindle in self.spindle:
            for chan, obj in spindle.channels.items():
                self.channels['spindle.{}.{}'.format(spindle.snum, chan)] = obj

        self.all_axes_homed.setValue(STAT.homed)
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
    def on(self, chan):
        """True if machine power is ON."""
        return STAT.task_state == linuxcnc.STATE_ON

    @DataChannel
    def file(self, chan):
        """Currently loaded file including path"""
        return chan.value or 'No file loaded'

    @file.setter
    def file(self, chan, fname):
        if STAT.interp_state == linuxcnc.INTERP_IDLE \
                and STAT.call_level == 0:

            if self.file_watcher is not None:
                self.file_watcher.removePath(chan.value)
                self.file_watcher.addPath(fname)

            chan.value = fname
            chan.signal.emit(fname)

    def updateFile(self, path):
        LOG.debug("Reloading edited G-Code file: %s", path)
        self.file.signal.emit(path)
        CMD.program_open(path)

    @DataChannel
    def state(self, chan):
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
    def state(self, chan):
        states = {0: "N/A",
                       linuxcnc.RCS_DONE: "Done",
                       linuxcnc.RCS_EXEC: "Exec",
                       linuxcnc.RCS_ERROR: "Error"}

        return states[STAT.state]

    @DataChannel
    def exec_state(self, chan):
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
    def exec_state(self, chan):
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
    def interp_state(self, chan):
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
    def interp_state(self, chan):
        interp_states = {0: "N/A",
                            linuxcnc.INTERP_IDLE: "Idle",
                            linuxcnc.INTERP_READING: "Reading",
                            linuxcnc.INTERP_PAUSED: "Paused",
                            linuxcnc.INTERP_WAITING: "Waiting"}

        return interp_states[STAT.interp_state]


    @DataChannel
    def interpreter_errcode(self, chan):
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
    def interpreter_errcode(self, chan):
        interpreter_errcodes = {0: "Ok",
                                1: "Exit",
                                2: "Finished",
                                3: "Endfile",
                                4: "File not open",
                                5: "Error"}

        return interpreter_errcodes[STAT.interpreter_errcode]

    @DataChannel
    def task_state(self, chan, query=None):
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
    def task_state(self, chan):
        task_states = {0: "N/A",
                       linuxcnc.STATE_ESTOP: "E-Stop",
                       linuxcnc.STATE_ESTOP_RESET: "Reset",
                       linuxcnc.STATE_ON: "On",
                       linuxcnc.STATE_OFF: "Off"}

        return task_states[STAT.task_state]

    @DataChannel
    def task_mode(self, chan):
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
    def task_mode(self, chan):
        task_modes = {0: "N/A",
                       linuxcnc.MODE_MANUAL: "Manual",
                       linuxcnc.MODE_AUTO: "Auto",
                       linuxcnc.MODE_MDI: "MDI"}

        return task_modes[STAT.task_mode]

    @DataChannel
    def motion_mode(self, chan):
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
    def motion_mode(self, chan):
        modes = {0: "N/A",
                  linuxcnc.TRAJ_MODE_COORD: "Coord",
                  linuxcnc.TRAJ_MODE_FREE: "Free",
                  linuxcnc.TRAJ_MODE_TELEOP: "Teleop"}

        return modes[STAT.motion_mode]

    @DataChannel
    def motion_type(self, chan, query=None):
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
    def motion_type(self, chan):
        motion_types = {0: "None",
                        linuxcnc.MOTION_TYPE_TRAVERSE: "Traverse",
                        linuxcnc.MOTION_TYPE_FEED: "Linear Feed",
                        linuxcnc.MOTION_TYPE_ARC: "Arc Feed",
                        linuxcnc.MOTION_TYPE_TOOLCHANGE: "Tool Change",
                        linuxcnc.MOTION_TYPE_PROBING: "Probing",
                        linuxcnc.MOTION_TYPE_INDEXROTARY: "Rotary Index"}

        return motion_types[STAT.motion_type]

    @DataChannel
    def program_units(self, chan):
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
    def program_units(self, chan, format='short'):
        if format == 'short':
            return ["N/A", "in", "mm", "cm"][STAT.program_units]
        else:
            return ["N/A", "Inches", "Millimeters", "Centimeters"][STAT.program_units]

    @DataChannel
    def linear_units(self, chan):
        """Machine linear units

        Available as float (units/mm), or in short or long string formats.

        To return the string in a status label::

            status:linear_units
            status:linear_units?string
            status:linear_units?string&format=long

        :returns: machine linear units
        :rtype: float, str
        """
        return STAT.linear_units

    @linear_units.tostring
    def linear_units(self, chan, format='short'):
        if format == 'short':
            return {0.0: "N/A", 1.0: "mm", 1 / 25.4: "in"}[STAT.linear_units]
        else:
            return {0.0: "N/A", 1.0: "Millimeters", 1 / 25.4: "Inches"}[STAT.linear_units]

    @DataChannel
    def gcodes(self, chan, fmt=None):
        """G-codes

        active G-codes for each modal group

        | syntax ``status:gcodes`` returns tuple of strings
        | syntax ``status:gcodes?raw`` returns tuple of integers
        | syntax ``status:gcodes?string`` returns str
        """
        if fmt == 'raw':
            return STAT.gcodes
        return chan.value

    @gcodes.tostring
    def gcodes(self, chan):
        return " ".join(chan.value)

    @gcodes.setter
    def gcodes(self, chan, gcodes):
        chan.value = tuple(["G%g" % (c/10.) for c in sorted(gcodes[1:]) if c != -1])
        chan.signal.emit(self.gcodes.value)

    @DataChannel
    def mcodes(self, chan, fmt=None):
        """M-codes

        active M-codes for each modal group

        | syntax ``status:mcodes`` returns tuple of strings
        | syntax ``status:mcodes?raw`` returns tuple of integers
        | syntax ``status:mcodes?string`` returns str
        """
        if fmt == 'raw':
            return STAT.mcodes
        return chan.value

    @mcodes.tostring
    def mcodes(self, chan):
        return " ".join(chan.value)

    @mcodes.setter
    def mcodes(self, chan, gcodes):
        chan.value = tuple(["M%g" % gcode for gcode in sorted(gcodes[1:]) if gcode != -1])
        chan.signal.emit(chan.value)

    @DataChannel
    def g5x_index(self, chan):
        """Current G5x work coord system

        | syntax ``status:g5x_index`` returns int
        | syntax ``status:g5x_index?string`` returns str
        """
        return STAT.g5x_index

    @g5x_index.tostring
    def g5x_index(self, chan):
        return ["G53", "G54", "G55", "G56", "G57", "G58",
                "G59", "G59.1", "G59.2", "G59.3"][STAT.g5x_index]

    @DataChannel
    def settings(self, chan, item=None):
        """Interpreter Settings

        Available Items:
            0) sequence_number
            1) feed
            2) speed

        :return: interpreter settings
        :rtype: tuple, int, float
        """
        if item is None:
            return STAT.settings
        return STAT.settings[{'sequence_number': 0, 'feed': 1, 'speed': 2}[item]]

    @DataChannel
    def homed(self, chan, anum=None):
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
    def all_axes_homed(self, chan):
        """All axes homed status

        True if all axes are homed or if [TRAJ]NO_FORCE_HOMING set in INI.

        :returns: all homed
        :rtype: bool
        """
        return chan.value

    @all_axes_homed.setter
    def all_axes_homed(self, chan, homed):
        if self.no_force_homing:
            chan.value = True
        else:
            for anum in INFO.AXIS_NUMBER_LIST:
                if homed[anum] is not 1:
                    chan.value = False
                    break
            else:
                chan.value = True
        chan.signal.emit(chan.value)

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

        # watch the gcode file for changes and reload as needed
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.addPath(self.file.value)
        self.file_watcher.fileChanged.connect(self.updateFile)

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

        # status updates
        for item, old_val in self.old.iteritems():
            new_val = getattr(STAT, item)
            if new_val != old_val:
                self.old[item] = new_val
                self.channels[item].setValue(new_val)

        # joint status updates
        for joint in self.joint:
            joint._update()

        # spindle status updates
        for spindle in self.spindle:
            spindle._update()

        # print time.time() - s


class JointStatus(DataPlugin):
    def __init__(self, jnum):
        super(JointStatus, self).__init__()

        self.jnum = jnum
        self.jstat = STAT.joint[jnum]

        for key, value in self.jstat.items():
            chan = DataChannel(doc=key, data=value)
            self.channels[key] = chan
            setattr(self, key, chan)

    def _update(self):
        """Periodic joint item updates."""

        jstat = STAT.joint[self.jnum].items()
        changed_items = tuple(set(jstat) - set(self.jstat.items()))
        for item in changed_items:
            LOG.debug('JOINT_{0} {1}: {2}'.format(self.jnum, item[0], item[1]))
            self.channels[item[0]].setValue(item[1])

        self.jstat.update(jstat)


class SpindleStatus(DataPlugin):
    def __init__(self, snum):
        super(SpindleStatus, self).__init__()

        self.snum = snum
        self.sstat = STAT.spindle[snum]

        for key, value in self.sstat.items():
            chan = DataChannel(doc=key, data=value)
            self.channels[key] = chan
            setattr(self, key, chan)

    def _update(self):
        """Periodic spindle item updates."""

        sstat = STAT.spindle[self.snum].items()
        changed_items = tuple(set(sstat) - set(self.sstat.items()))
        for item in changed_items:
            LOG.debug('Spindle_{0} {1}: {2}'.format(self.snum, item[0], item[1]))
            self.channels[item[0]].setValue(item[1])

        self.sstat.update(sstat)
