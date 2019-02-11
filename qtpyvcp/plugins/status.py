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
                self.value = getattr(STAT, item)
                self.channels[item] = chan
                setattr(self, item, chan)


        self.homed.notify(self.all_homed)
        # self.task_state.notify(lambda s: self.on.value)

        # Set up the periodic update timer
        self.timer = QTimer()
        self._cycle_time = cycle_time
        self.timer.timeout.connect(self._periodic)

        self.on.settable = True
        self.task_state.notify(lambda ts:
                               self.on.setValue(ts == linuxcnc.STATE_ON))

    recent_files = DataChannel(doc='List of recently loaded files', settable=True, data=[])

    class task_state(DataChannel):
        def value(self):
            return self.value


    @DataChannel
    def on(self):
        """True if machine power is ON."""
        return STAT.task_state == linuxcnc.STATE_ON

    @DataChannel
    def file(self):
        """Currently loaded file."""
        return self.value or 'No file loaded'

    @file.setter
    def file(self, fname):
        if STAT.interp_state == linuxcnc.INTERP_IDLE \
                and STAT.call_level == 0:
            self.value = fname
            self.signal.emit(fname)

    @DataChannel
    def task_state(self, query=None):
        """Current status of task

        * E-Stop
        * Reset
        * On
        * Off

        To return the string in a status label::

            status:task_state?string

        :returns:
        :rtype: int, str
        """
        if query == 'string':
            return str(self.task_state)
        return self.task_state.value

    @task_state.tostring
    def task_state(self):
        task_states = {0: "N/A",
                       linuxcnc.STATE_ESTOP: "E-Stop",
                       linuxcnc.STATE_ESTOP_RESET: "Reset",
                       linuxcnc.STATE_ON: "On",
                       linuxcnc.STATE_OFF: "Off"}

        return task_states[self.task_state.value]

    @DataChannel
    def interp_state(self, query=None):
        """Current interpreter state

        * Idle
        * Reading
        * Paused
        * Waiting

        To return the string in a status label::

            status:interp_state?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return str(self.interp_state)
        return self.interp_state.value

    @interp_state.tostring
    def interp_state(self):
        states = {0: "N/A",
                  linuxcnc.INTERP_IDLE: "Idle",
                  linuxcnc.INTERP_READING: "Reading",
                  linuxcnc.INTERP_PAUSED: "Paused",
                  linuxcnc.INTERP_WAITING: "Waiting"}

        return states[STAT.interp_state]

    @DataChannel
    def motion_mode(self, query=None):
        """Current motion controller mode

        * Coord
        * Free
        * Teleop

        To return the string in a status label::

            status:motion_mode?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return str(self.motion_mode)
        return self.motion_mode.value

    @motion_mode.tostring
    def motion_mode(self):
        modes = {0: "N/A",
                  linuxcnc.TRAJ_MODE_COORD: "Coord",
                  linuxcnc.TRAJ_MODE_FREE: "Free",
                  linuxcnc.TRAJ_MODE_TELEOP: "Teleop"}

        return modes[self.motion_mode.value]

    @DataChannel
    def state(self, query=None):
        """Current command execution status

        * Done
        * Exec
        * Error

        To return the string in a status label::

            status:state?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return self.fstr()
        return self.value

    @state.tostring
    def state(self):
        states = {0: "N/A",
                       linuxcnc.RCS_DONE: "Done",
                       linuxcnc.RCS_EXEC: "Exec",
                       linuxcnc.RCS_ERROR: "Error"}

        return states[self.value]

    @DataChannel
    def exec_state(self, query=None):
        """Current task execution state

        * Error
        * Done
        * Waiting for Motion
        * Waiting for Motion Queue
        * Waiting for Pause
        * Waiting for Motion and IO
        * Waiting for Delay
        * Waiting for system CMD
        * Waiting for spindle orient

        To return the string in a status label::

            status:exec_state?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return self.fstr()
        return self.value

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
        return exec_states[self.value]

    @DataChannel
    def task_mode(self, query=None):
        """Current task mode

        * Manual
        * Auto
        * MDI

        To return the string in a status label::

            status:task_mode?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return self.fstr()
        return self.value

    @task_mode.tostring
    def task_mode(self):
        task_modes = {0: "N/A",
                       linuxcnc.MODE_MANUAL: "Manual",
                       linuxcnc.MODE_AUTO: "Auto",
                       linuxcnc.MODE_MDI: "MDI"}

        return task_modes[self.value]

    @DataChannel
    def motion_type(self, query=None):
        """Current executing motion

        * Traverse
        * Linear Feed
        * Arc Feed
        * Tool Change
        * Probing
        * Rotary Index

        To return the string in a status label::

            status:motion_type?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return self.fstr()
        return self.value

    @motion_type.tostring
    def motion_type(self):
        motion_types = {0: "N/A",
                        linuxcnc.MOTION_TYPE_TRAVERSE: "Traverse",
                        linuxcnc.MOTION_TYPE_FEED: "Linear Feed",
                        linuxcnc.MOTION_TYPE_ARC: "Arc Feed",
                        linuxcnc.MOTION_TYPE_TOOLCHANGE: "Tool Change",
                        linuxcnc.MOTION_TYPE_PROBING: "Probing",
                        linuxcnc.MOTION_TYPE_INDEXROTARY: "Rotary Index"}
        return motion_types[self.value]

    @DataChannel
    def interp_state(self, query=None):
        """Current state of RS274NGC interpreter

        * Idle
        * Reading
        * Paused
        * Waiting

        To return the string in a status label::

            status:interp_state?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return str(self.interp_state)
        return self.interp_state.value

    @interp_state.tostring
    def interp_state(self):
        interp_states = {0: "N/A",
                            linuxcnc.INTERP_IDLE: "Idle",
                            linuxcnc.INTERP_READING: "Reading",
                            linuxcnc.INTERP_PAUSED: "Paused",
                            linuxcnc.INTERP_WAITING: "Waiting"}

        return interp_states[self.interp_state.value]


    @DataChannel
    def interpreter_errcode(self, query=None):
        """Current RS274NGC interpreter return code

        * Ok
        * Exit
        * Finished
        * Endfile
        * File not open
        * Error

        To return the string in a status label::

            status:interpreter_errcode?string

        :returns:
        :rtype: int, str
        """

        if query == 'string':
            return self.fstr()
        return self.value

    @interpreter_errcode.tostring
    def interpreter_errcode(self):
        interpreter_errcodes = {0: "N/A",
                                1: "Ok",
                                2: "Exit",
                                3: "Finished",
                                4: "Endfile",
                                4: "File not open",
                                5: "Error"}

        return interpreter_errcodes[self.value]

    all_homed = DataChannel(doc='True if all homed, or NO_FORCE_HOMING is True',
                            data=False)

    @all_homed.setter
    def all_homed(self, *args, **kwargs):
        if self.no_force_homing:
            self._date = True
        for jnum in range(STAT.joints):
            if not STAT.joint[jnum]['homed']:
                self.value = False
        self.value = True


    def allHomed(self):
        """Returns TRUE if all joints are homed."""
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
