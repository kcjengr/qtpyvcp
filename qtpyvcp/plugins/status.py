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
                self.channels[item]._data = getattr(STAT, item)
            elif item not in excluded_items and not item.startswith('_'):
                chan = DataChannel(doc=item, data=getattr(STAT, item))
                chan._data = getattr(STAT, item)
                self.channels[item] = chan
                setattr(self, item, chan)


        self.homed.notify(self.all_homed)
        # self.task_state.notify(lambda s: self.on._data)

        # Set up the periodic update timer
        self.timer = QTimer()
        self._cycle_time = cycle_time
        self.timer.timeout.connect(self._periodic)

    on = DataChannel(doc="Machine power state", data=False)
    recent_files = DataChannel(doc='List of recently loaded files', settable=True, data=[])
    file_loaded = DataChannel(doc='File changed')

    @DataChannel
    def task_state(chan, query=None):
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
            return chan.fstr()
        return chan._data

    @task_state.tostring
    def task_state(chan):
        task_states = {0: "N/A",
                       linuxcnc.STATE_ESTOP: "E-Stop",
                       linuxcnc.STATE_ESTOP_RESET: "Reset",
                       linuxcnc.STATE_ON: "On",
                       linuxcnc.STATE_OFF: "Off"}

        return task_states[chan._data]

    @DataChannel
    def interp_state(chan, query=None):
        """Current interpreter state"""
        if query == 'string':
            return str(chan)
        return chan._data

    @interp_state.tostring
    def interp_state(chan):
        states = {0: "N/A",
                  linuxcnc.INTERP_IDLE: "Idle",
                  linuxcnc.INTERP_READING: "Reading",
                  linuxcnc.INTERP_PAUSED: "Paused",
                  linuxcnc.INTERP_WAITING: "Waiting"}

        return states[STAT.interp_state]

    @DataChannel
    def motion_mode(chan, query=None):
        """Current motion controller mode"""
        if query == 'string':
            return str(chan)
        return chan._data

    @motion_mode.tostring
    def motion_mode(chan):
        modes = {0: "N/A",
                  linuxcnc.TRAJ_MODE_COORD: "Coord",
                  linuxcnc.TRAJ_MODE_FREE: "Free",
                  linuxcnc.TRAJ_MODE_TELEOP: "Teleop"}

        return modes[chan._data]


    all_homed = DataChannel(doc='True if all homed, or NO_FORCE_HOMING is True',
                            data=False)

    @all_homed.setter
    def all_homed(chan, *args, **kwargs):
        if chan.no_force_homing:
            chan._date = True
        for jnum in range(STAT.joints):
            if not STAT.joint[jnum]['homed']:
                chan._data = False
        chan._data = True


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
        PREFS.setPref("STATUS", "RECENT_FILES", self.recent_files._data)
        PREFS.setPref("STATUS", "MAX_RECENT_FILES", self.max_recent_files)

    def _periodic(self):

        # s = time.time()

        try:
            STAT.poll()
        except Exception:
            LOG.warning("Status polling failed, is LinuxCNC running?", exc_info=True)
            self.timer.stop()
            return

        for chan, chan_obj in self.channels.iteritems():
            new_value = getattr(STAT, chan, None)
            if new_value is None:
                continue
            if chan_obj._data != new_value:
                # update the status items
                chan_obj._data = new_value
                chan_obj._signal.emit(new_value)

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
