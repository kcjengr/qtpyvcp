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

from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import QObject, pyqtSignal, pyqtBoundSignal, pyqtSlot, QTimer, QThread

import os
import time
import linuxcnc

from QtPyVCP.utilities.info import Info
from QtPyVCP.utilities.prefs import Prefs
INFO = Info()
PREFS = Prefs()

from QtPyVCP.utilities import logger
log = logger.getLogger(__name__)
log.setLevel("DEBUG")

NUM_SPINDLES = INFO.spindles()


class GCodes:
    def __getitem__(self, gcodes):
        formated_gcodes = []
        for gcode in sorted(gcodes[1:]):
            if gcode == -1:
                continue
            if gcode % 10 == 0:
                formated_gcodes.append("G{0}".format(gcode / 10))
            else:
                formated_gcodes.append("G{0}.{1}".format(gcode / 10, gcode % 10))
        return " ".join(formated_gcodes)

class MCodes:
    def __getitem__(self, mcodes):
        formated_mcodes = []
        for mcode in sorted(mcodes[1:]):
            if mcode == -1:
                continue
            formated_mcodes.append("M{0}".format(mcode))
        return " ".join(formated_mcodes)

class Status(QObject):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = _Status()
        return cls._instance

class _Status(QObject):

    STATE_STRING_LOOKUP = {
        "task_state": {
            0: "Unknown",
            linuxcnc.STATE_ESTOP: "Estop",
            linuxcnc.STATE_ESTOP_RESET: "Reset",
            linuxcnc.STATE_ON: "On",
            linuxcnc.STATE_OFF: "Off",
        },
        "state": {
            0: "Unknown",
            linuxcnc.RCS_DONE: "Done",
            linuxcnc.RCS_EXEC: "Exec",
            linuxcnc.RCS_ERROR: "Error",
        },
        "task_mode": {
            0: "Unknown",
            linuxcnc.MODE_MANUAL: "Manual",
            linuxcnc.MODE_AUTO: "Auto",
            linuxcnc.MODE_MDI: "MDI",
        },
        "interp_state": {
            0: "Unknown",
            linuxcnc.INTERP_IDLE: "Idle",
            linuxcnc.INTERP_READING: "Reading",
            linuxcnc.INTERP_PAUSED: "Paused",
            linuxcnc.INTERP_WAITING: "Waiting",
        },
        "motion_mode": {
            0: "Unknown",
            linuxcnc.TRAJ_MODE_COORD: "Coord",
            linuxcnc.TRAJ_MODE_FREE: "Free",
            linuxcnc.TRAJ_MODE_TELEOP: "Teleop",
        },
        "motion_type": {
            0: "None",
            linuxcnc.MOTION_TYPE_TRAVERSE: "Traverse",
            linuxcnc.MOTION_TYPE_FEED: "Linear Feed",
            linuxcnc.MOTION_TYPE_ARC: "Arc Feed",
            linuxcnc.MOTION_TYPE_TOOLCHANGE: "Tool Change",
            linuxcnc.MOTION_TYPE_PROBING: "Probing",
            linuxcnc.MOTION_TYPE_INDEXROTARY: "Rotary Index",
        },
        "interpreter_errcode": {
            0: "Unknown",
            1: "Ok",
            2: "Exit",
            3: "Finished",
            4: "Endfile",
            4: "File not open",
            5: "Error",
        },
        "g5x_index": ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"],
        "program_units": ["NA", "in", "mm", "cm"],
        "linear_units": {
            0.0: "N/A",
            1.0: "mm",
            1/25.4: "in",
        },
        "gcodes": GCodes(),
        "mcodes": MCodes(),
    }


    stat = linuxcnc.stat()
    timer = QTimer()

    # Queues
    active_queue = pyqtSignal(int)          # number of motions blending
    queue = pyqtSignal(int)                 # current size of the trajectory planner queue
    queue_full = pyqtSignal(bool)           # the trajectory planner queue full flag
    queued_mdi_commands = pyqtSignal(int)   #

    # Positions
    position = pyqtSignal(tuple)            # trajectory position
    actual_position = pyqtSignal(tuple)     # current position, in machine units
    joint_position = pyqtSignal(tuple)      # joint commanded positions
    joint_actual_position = pyqtSignal(tuple) # joint actual positions
    dtg = pyqtSignal(tuple)                 # DTG per axis, as reported by trajectory planner
    distance_to_go = pyqtSignal(float)      # vector DTG, as reported by trajectory planner

    # Velocities
    current_vel = pyqtSignal(float)         # current velocity in user units per second
    velocity = pyqtSignal(float)            # unclear

    # Offsets
    g5x_index = pyqtSignal([int], [str])    # active coordinate system index, G54=1, G55=2 etc
    g5x_offset = pyqtSignal(tuple)          # offset of the currently active coordinate system
    g92_offset = pyqtSignal(tuple)          # values of the current g92 offset
    tool_offset = pyqtSignal(tuple)         # offset values of the current tool
    rotation_xy = pyqtSignal(float)         # current XY rotation angle around Z axis

    # I/O
    ain = pyqtSignal(tuple)                 # current value of the analog input pins
    aout = pyqtSignal(tuple)                # current value of the analog output pins
    din = pyqtSignal(tuple)                 # current value of the digital input pins
    dout = pyqtSignal(tuple)                # current value of the digital output pins

    # Cooling
    mist = pyqtSignal(bool)                 # mist self.status
    flood = pyqtSignal(bool)                # flood self.status, either FLOOD_OFF or FLOOD_ON

    # M-codes and G-codes
    mcodes = pyqtSignal([tuple], [str])     # currently active M-codes
    gcodes = pyqtSignal([tuple], [str])     # active G-codes for each modal group

    # Home and Limit
    homed = pyqtSignal(tuple)               # homed flag for each joint
    inpos = pyqtSignal(bool)                # machine-in-position flag
    limit = pyqtSignal(tuple)               # axis limit self.status masks

    # Delays
    delay_left = pyqtSignal(float)          # remaining time on dwell (G4) command, seconds
    input_timeout = pyqtSignal(bool)        # flag for M66 timer in progress

    # Lube
    lube = pyqtSignal(bool)                 # lube on flag
    lube_level = pyqtSignal(int)            # lube level, reflects iocontrol.0.lube_level.

    # Program control
    optional_stop = pyqtSignal(bool)        # option stop enables flag
    block_delete = pyqtSignal(bool)         # block delete current self.status
    paused = pyqtSignal(bool)               # motion paused flag
    feed_hold_enabled = pyqtSignal(bool)    # enable flag for feed hold

    # Probe
    probe_tripped = pyqtSignal(bool)        # probe tripped flag (latched)
    probe_val = pyqtSignal(bool)            # reflects value of the motion.probe-input pin
    probed_position = pyqtSignal(tuple)     # position where probe tripped
    probing = pyqtSignal(bool)              # probing in progress flag

    # Program File
    file = pyqtSignal(str)                  # path of currently loaded gcode file
    program_units = pyqtSignal([int], [str])# one of CANON_UNITS_INCHES=1, CANON_UNITS_MM=2
    motion_line = pyqtSignal(int)           # source line number motion is currently executing
    current_line = pyqtSignal(int)          # currently executing line
    read_line = pyqtSignal(int)             # line the RS274NGC interpreter is currently reading
    call_level = pyqtSignal(int)            #

    # Overrides
    feedrate = pyqtSignal(float)            # feed-rate override, 0-1
    rapidrate = pyqtSignal(float)           # rapid-rate override, 0-1
    max_velocity = pyqtSignal(float)        # max velocity in machine units/s
    feed_override_enabled = pyqtSignal(bool)# enable flag for feed override
    adaptive_feed_enabled = pyqtSignal(bool)# self.status of adaptive feedrate override

    # State
    enabled = pyqtSignal(bool)              # trajectory planner enabled
    estop = pyqtSignal([int], [bool])       # linuxcnc.STATE_ESTOP or not
    state = pyqtSignal([int], [str])        # current command execution status. One of RCS_DONE, RCS_EXEC, RCS_ERROR.
    exec_state = pyqtSignal([int], [str])   # task execution state
    task_mode = pyqtSignal([int], [str])    # current task mode
    task_paused = pyqtSignal(bool)          # task paused flag
    task_state = pyqtSignal([int], [str])   # current task state
    motion_mode = pyqtSignal([int], [str])  # mode of the motion controller
    motion_type = pyqtSignal([int], [str])  # type of the currently executing motion
    interp_state = pyqtSignal([int], [str]) # current state of RS274NGC interpreter
    interpreter_errcode = pyqtSignal([int], [str]) # current RS274NGC interpreter return code
    settings = pyqtSignal(tuple)            # interpreter settings. (sequence_number, feed_rate, speed)

    jog_mode_signal = pyqtSignal(bool)             # jog mode = true
    linear_units = pyqtSignal([float], [str])
    angular_units = pyqtSignal([float], [str])

    # Tool
    tool_in_spindle = pyqtSignal(int)       # current tool number
    pocket_prepped = pyqtSignal(int)        # Tx command completed, and this pocket is prepared
    tool_table = pyqtSignal(tuple)          # list of tool entries

    # Extended status signals
    axis_positions = pyqtSignal(tuple)      # ABS, REL and DTG axis values
    joint_positions = pyqtSignal(tuple)     # joint pos respecting INI settings
    file_loaded = pyqtSignal(str)           # file loaded

    # interpreter settings
    feed = pyqtSignal(float)                # Current requested feed
    speed = pyqtSignal(float)               # Current requested speed

    on = pyqtSignal(bool)
    moving = pyqtSignal(bool)
    all_homed = pyqtSignal(bool)

    # Gcode Backplot
    backplot_line_selected = pyqtSignal(int)
    backplot_loading_started = pyqtSignal()
    backplot_loading_progress = pyqtSignal(int)
    backplot_loading_finished = pyqtSignal()
    backplot_gcode_error = pyqtSignal(str)
    reload_backplot = pyqtSignal()

    recent_files_changed = pyqtSignal(tuple)

    # Emitted when the UI is loaded
    init_ui = pyqtSignal()

    # Emitted on app shutdown
    on_shutown = pyqtSignal()

    def __init__(self):
        super(_Status, self).__init__()

        self.no_force_homing = INFO.noForceHoming()
        self._report_actual_position = False

        self.max_recent_files = PREFS.getPref("STATUS", "MAX_RECENT_FILES", 10, int)
        files = PREFS.getPref("STATUS", "RECENT_FILES", [], list)
        self.recent_files = [file for file in files if os.path.exists(file)]

        self.jog_increment = 0 # jog
        self.step_jog_increment = INFO.getIncrements()[0]
        self.jog_mode = True
        self.linear_jog_velocity = INFO.getJogVelocity()
        self.angular_jog_velocity = INFO.getJogVelocity()

        # Try initial poll
        try:
            self.stat.poll()
        except:
            pass

        excluded_items = ['axes', 'joints', 'axis', 'joint', 'spindle',
            'acceleration', 'max_acceleration', 'kinematics_type', 'axis_mask',
            'cycle_time', 'echo_serial_number', 'id', 'poll', 'command', 'debug']

        self.old = {}
        # initialize the old values dict
        for item in dir(self.stat):
            if item.startswith('_') or item in excluded_items:
                continue
            self.old[item] = getattr(self.stat, item)

        # These signals should all cause position updates
        self.position.connect(self.updateAxisPositions)
        self.g5x_offset.connect(self.updateAxisPositions)
        self.g92_offset.connect(self.updateAxisPositions)
        self.tool_offset.connect(self.updateAxisPositions)
        self.joint_position.connect(self.updateJointPositions)

        self.homed.connect(self._allHomed)

        self.task_state.connect(lambda v: self.on.emit(v == linuxcnc.STATE_ON))

        # File
        self.file.connect(self.updateFileLoaded)

        # feed and speed signals
        self.settings.connect(lambda s: self.feed.emit(s[1]))
        self.settings.connect(lambda s: self.feed.emit(s[2]))

        # Initialize Joint status class
        self.joint = tuple(_Joint(self.stat.joint[i], i) for i in range(INFO.NUM_JOINTS))

        # Initialize Spindle status classes
        self.spindle = tuple(_Spindle(self.stat.spindle[i], i) for i in range(NUM_SPINDLES))

        # Initialize Error status class
        self.error = _Error()

        # Set up the periodic update timer
        self._cycle_time = 75
        self.timer.timeout.connect(self._periodic)

        # Use a single shot to stat the main periodic timer, this ensures it
        # starts after the main Qt event loop to prevent errors
        QTimer.singleShot(0, self.startPeriodic)

    def startPeriodic(self):
        self.timer.start(self._cycle_time)

    def _periodic(self):
        # s = time.time()
        try:
            self.stat.poll()
        except Exception as e:
            log.warning("Status polling failed, is LinuxCNC running?", exc_info=e)
            self.timer.stop()
            return

        for key, old_value in self.old.iteritems():
            new_value = getattr(self.stat, key)
            if old_value != new_value:
                getattr(self, key).emit(new_value)

                str_dict = self.STATE_STRING_LOOKUP.get(key)
                if str_dict is not None:
                    str_val = str_dict[new_value]
                    getattr(self, key)[str].emit(str_val)
                    log.debug("{}: {}".format(key, str_val))

                # update old values dict
                self.old[key] = new_value

        # joint status updates
        for joint in self.joint:
            joint._update(self.stat.joint[joint.number])

        # spindle status updates
        for spindle in self.spindle:
            spindle._update(self.stat.spindle[spindle.number])

        self.error._periodic()
        # print time.time() - s

    def forceUpdate(self):
        for key, value in self.old.iteritems():
                getattr(self, key).emit(value)



    #===========================  Helper Functions  ===========================

    def _from_internal_linear_unit(self, v, unit=None):
        if unit is None:
            unit = self.stat.linear_units
        lu = (unit or 1) * 25.4
        return v * lu

    def _parse_increment(self, jogincr):
        scale = 1;
        if isinstance(jogincr, basestring):
            if jogincr.endswith("mm"):
                scale = self._from_internal_linear_unit(1 / 25.4)
            elif jogincr.endswith("cm"):
                scale = self._from_internal_linear_unit(10 / 25.4)
            elif jogincr.endswith("um"):
                scale = self._from_internal_linear_unit(.001 / 25.4)
            elif jogincr.endswith("in") or jogincr.endswith("inch"):
                scale = self._from_internal_linear_unit(1.)
            elif jogincr.endswith("mil"):
                scale = self._from_internal_linear_unit(.001)
            else:
                scale = 1
            jogincr = jogincr.rstrip(" inchmuil")
            if "/" in jogincr:
                p, q = jogincr.split("/")
                jogincr = float(p) / float(q)
            else:
                jogincr = float(jogincr)
        return jogincr * scale

    def setJogIncrement(self, raw_increment):
        if not self.jog_mode:
            self.step_jog_increment = raw_increment # save current step increment
        self.jog_increment = self._parse_increment(raw_increment)

    def setJogMode(self, mode):
        # insert checks around state and safety
        self.jog_mode = mode
        if mode == True:
            self.setJogIncrement(0)
        else:
            self.setJogIncrement(self.step_jog_increment)
        self.jog_mode_signal.emit(self.jog_mode)


    def setReportActualPosition(self, report_actual):
        # reports commanded by default
        if report_actual != self._report_actual_position:
            self._report_actual_position = report_actual
            if self._report_actual_position:
                # disconnect commanded pos update signals
                self.position.disconnect(self.updateAxisPositions)
                self.joint_position.disconnect(self.updateJointPositions)
                # connect actual pos update signals
                self.actual_position.connect(self.updateAxisPositions)
                self.joint_actual_position.connect(self.updateJointPositions)
            else:
                # disconnect actual pos update signals
                self.actual_position.disconnect(self.updateAxisPositions)
                self.joint_actual_position.disconnect(self.updateJointPositions)
                # connect commanded pos update signals
                self.position.connect(self.updateAxisPositions)
                self.joint_position.connect(self.updateJointPositions)

    def updateAxisPositions(self, pos=None):
        # To allow forced updates, mostly for use by QtDesigner methods
        if pos is None:
            if self._report_actual_position:
                pos = self.stat.actual_position
            else:
                pos = self.stat.position

        dtg = self.stat.dtg
        g5x_offset = self.stat.g5x_offset
        g92_offset = self.stat.g92_offset
        tool_offset = self.stat.tool_offset

        rel = [0] * 9
        for axis in INFO.AXIS_NUMBER_LIST:
            rel[axis] = pos[axis] - g5x_offset[axis] - tool_offset[axis]

        if self.stat.rotation_xy != 0:
            t = math.radians(-self.stat.rotation_xy)
            xr = rel[0] * math.cos(t) - rel[1] * math.sin(t)
            yr = rel[0] * math.sin(t) + rel[1] * math.cos(t)
            rel[0] = xr
            rel[1] = yr

        for axis in INFO.AXIS_NUMBER_LIST:
            rel[axis] -= g92_offset[axis]

        self.axis_positions.emit(tuple([pos, tuple(rel), tuple(dtg)]))

    def updateJointPositions(self, pos=None):
        # To allow forced updates, mostly for use by QtDesigner methods
        if pos is None:
            if self._report_actual_position:
                pos = self.stat.joint_actual_position
            else:
                pos = self.stat.joint_position
        self.joint_positions.emit(pos)

    def updateFileLoaded(self, file):
        if self.stat.interp_state == linuxcnc.INTERP_IDLE \
                and self.stat.call_level == 0:
            self.file_loaded.emit(file)

    def _allHomed(self):
        self.all_homed.emit(self.allHomed())

    def allHomed(self):
        '''Returns TRUE if all joints are homed.'''
        if self.no_force_homing:
            return True
        for jnum in range(self.stat.joints):
            if not self.stat.joint[jnum]['homed']:
                return False
        return True

    def onShutdown(self):
        self.on_shutown.emit()
        PREFS.setPref("STATUS", "RECENT_FILES", self.recent_files)
        PREFS.setPref("STATUS", "MAX_RECENT_FILES", self.max_recent_files)


#==============================================================================
# Joint status class
#==============================================================================

class _Joint(QObject):
    """Joint status class.
        An instance of this class is created for each joint.
    """

    # `linuxcnc.stat.join[n]` attribute signals
    jointType = pyqtSignal(int)         # reflects [JOINT_n]TYPE
    backlash = pyqtSignal(float)        # backlash in machine units
    enabled = pyqtSignal(bool)          # enabled flag
    fault = pyqtSignal(bool)            # active fault flag
    ferror_current = pyqtSignal(float)  # current following error
    ferror_highmark = pyqtSignal(float) # magnitude of max following error
    homed = pyqtSignal(bool)            # homed flag
    homing = pyqtSignal(bool)           # currently homing flag
    inpos = pyqtSignal(bool)            # in position flag
    input = pyqtSignal(bool)            # current input position
    max_ferror = pyqtSignal(float)      # reflects [JOINT_n]FERROR
    max_hard_limit = pyqtSignal(bool)   # max hard limit exceeded flag
    max_soft_limit = pyqtSignal(bool)   # max soft limit exceeded flag
    min_hard_limit = pyqtSignal(bool)   # min hard limit exceeded flag
    min_soft_limit = pyqtSignal(bool)   # max soft limit exceeded flag
    output = pyqtSignal(float)          # commanded output position
    override_limits = pyqtSignal(bool)  # override limits flag
    velocity = pyqtSignal(float)        # current velocity

    units = pyqtSignal(float)
    min_ferror= pyqtSignal(float)
    max_position_limit = pyqtSignal(float)
    min_position_limit = pyqtSignal(float)

    def __init__(self, status, number):
        super(_Joint, self).__init__()

        self.number = number
        self.status = status

    def _update(self, new_status):
        """Periodic joint item updates."""

        changed_items = tuple(set(new_status.items()) - set(self.status.items()))
        for item in changed_items:
            log.debug('JOINT_{0} {1}: {2}'.format(self.number, item[0], item[1]))
            getattr(self, item[0]).emit(item[1])

        self.status = new_status

class _Spindle(QObject):
    """Spindle status class.
        An instance of this class is created for each spindle.
    """

    # `linuxcnc.stat.spindle[n]` attribute signals
    brake = pyqtSignal(bool)            # value of the spindle brake flag
    direction = pyqtSignal(int)         # spindle rotational, forward=1, reverse=-1
    enabled = pyqtSignal(bool)          # value of the spindle enabled flag
    override_enabled = pyqtSignal(bool) # spindle override enabled flag
    override = pyqtSignal(float)        # spindle override value, 0-1
    speed = pyqtSignal(float)           # spindle speed
    increasing = pyqtSignal(bool)       # spindle speed increasing flag, unclear
    orient_state = pyqtSignal(int)      # orient state
    orient_fault = pyqtSignal(bool)     # orient fault
    homed = pyqtSignal(bool)            # not implemented

    def __init__(self, status, number):
        super(_Spindle, self).__init__()

        self.number = number
        self.status = status

    def _update(self, new_status):
        """Periodic spindle item updates."""

        changed_items = tuple(set(new_status.items()) - set(self.status.items()))
        for item in changed_items:
            log.debug('SPINDLE_{0} {1}: {2}'.format(self.number, item[0], item[1]))
            getattr(self, item[0]).emit(item[1])

        self.status = new_status

#==============================================================================
# Error status class
#==============================================================================

class _Error(QObject):

    error = linuxcnc.error_channel()

    new_error = pyqtSignal(str)
    new_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super(_Error, self).__init__(parent)

    def _periodic(self):
        error = self.error.poll()
        if not error:
            return

        kind, msg = error

        if msg == "" or msg is None:
            msg = "Unknown error!"

        if kind in [linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR]:
            self.new_error.emit(msg)
            log.error(msg)
        elif kind in [linuxcnc.NML_TEXT, linuxcnc.OPERATOR_TEXT,
            linuxcnc.NML_DISPLAY, linuxcnc.OPERATOR_DISPLAY]:
            self.new_message.emit(msg)
            log.info(msg)
        else:
            # notifications.show_error("UNKNOWN ERROR!", msg)
            log.error(msg)
