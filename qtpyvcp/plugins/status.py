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

from qtpy.QtCore import QObject, Signal, Slot, QTimer

import os
import time
import linuxcnc

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.prefs import Prefs
from qtpyvcp.plugins.plugin import QtPyVCPDataPlugin, QtPyVCPDataChannel

from qtpyvcp.utilities.logger import getLogger

INFO = Info()
PREFS = Prefs()

LOG = getLogger(__name__)
LOG.setLevel("DEBUG")

NUM_SPINDLES = INFO.spindles()

STAT = linuxcnc.stat()

class StatusItem(QtPyVCPDataChannel):
    """StatusItem object.

    Each of the `linuxcnc.stat` attributes is represented by a StatusItem.

    Args:
        item (str) : The name of the `linuxcnc.stat` item.
        typ (type) : The python type of the item's value. If no type is specified
            the type returned by `type(self.value)` will be used.
        to_str (method) : A method which returns a textual version of the
            item's value. If not specified defaults to the values `__str__` method.
        description (str) : A human readable description of the item.
    """

    def __init__(self, item, typ=None, to_str=str, description=''):
        super(StatusItem, self).__init__(description=description)

        self.item = item
        self.typ = typ or type(self.value)
        self.to_str = to_str

    @property
    def value(self):
        """The items current value.

        Returns:
            any : The value of the item as of the last `stat.poll()`.
        """
        return getattr(STAT, self.item)

    @property
    def text(self):
        """The items current text.

        Returns:
            str : The text of the item as of the last `stat.poll()`.
        """
        return self.to_str(self.value)

    def _update(self, value):
        self.valueChanged.emit(value)


class Status(QtPyVCPDataPlugin):
    """Status Class"""
    protocol = 'status'

    stat = STAT

    # Queues
    active_queue = StatusItem('active_queue', int)          # number of motions blending
    """Status of blending

    :returns: the number of motions blending
    :rtype: int

    """
    queue = StatusItem('queue', int)                        # current size of the trajectory planner queue
    """Status of the trajectory planner queue size

    :returns: the current size of the trajectory planner queue
    :rtype: int

    """
    queue_full = StatusItem('queue_full', bool)             # the trajectory planner queue full flag
    """Status of the trajectory planner queue

    :returns: True if the trajectory planner queue is full

    :rtype: bool

    """

    queued_mdi_commands = StatusItem('queued_mdi_commands', int)   #
    """Status of MDI queue

    :returns: how many MDI commands are in the queue
    :rtype: int

    """


    # Positions
    position = StatusItem('position', tuple)                 # trajectory position
    """Status of trajectory position

    :returns: the trajectory position for all axes
    :rtype: tuple

    """

    actual_position = StatusItem('actual_position', tuple)   # current position, in machine units
    """Status of current positions

    :returns: the current position, in machine units for all axes
    :rtype: tuple

    """

    joint_position = StatusItem('joint_position', tuple)     # joint commanded positions
    """Status of commanded joint positions

    :returns: the joint commanded positions for all joints
    :rtype: tuple

    """

    joint_actual_position = StatusItem('joint_actual_position', tuple) # joint actual positions
    """Status of actual joint positions

    :returns: the joint actual positions for all joints
    :rtype: tuple

    """

    dtg = StatusItem('dtg', tuple)                           # DTG per axis, as reported by trajectory planner
    """Status of Distance To Go per axis

    :returns: the DTG per axis, as reported by trajectory planner
    :rtype: tuple

    """

    distance_to_go = StatusItem('distance_to_go', float)     # vector DTG, as reported by trajectory planner
    """Status of vector Distance To Go

    :returns: vector DTG, as reported by trajectory planner
    :rtype: float

    """


    # Velocities
    current_vel = StatusItem('current_vel', float)           # current velocity in user units per second
    """Status of current velocity

    :returns: current velocity in user units per second
    :rtype: float

    """

    velocity = StatusItem('velocity', float)                 # unclear
    """Status of velocity

    :returns: unclear
    :rtype: float

    """

    # Offsets
    coords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
    g5x_index = StatusItem('g5x_index', int, coords.__getitem__)    # active coordinate system index, G54=1, G55=2 etc
    """Status of active coordinate system

    * G53=0
    * G54=1
    * G55=2
    * G56=3
    * G57=4
    * G58=5
    * G59=6
    * G59.1=7
    * G59.2=8
    * G59.3=9

    for a status label using channel 0 use a list slice like this::

    ["G53","G54","G55","G56","G57","G58","G59","G59.1","G59.2","G59.3"][ch[0]]

    :returns: active coordinate system index
    :rtype: int

"""
    g5x_offset = StatusItem('g5x_offset', tuple)          # offset of the currently active coordinate system
    """Status of currently active coordinate system offsets

    :returns: tuple of currently active coordinate system offsets joints 0-8
    :rtype: tuple

g5x_offset, tuple  offsets of the currently active coordinate system"""
    g92_offset = StatusItem('g92_offset', tuple)          # values of the current g92 offset
    """Status of current g92 offset

    :returns: tuple of current G92 offsets joints 0-8
    :rtype: tuple

    """

    tool_offset = StatusItem('tool_offset', tuple)         # offset values of the current tool
    """Status of current tool offsets

    :returns: tuple of the current tool offsets joints 0-8
    :rtype: tuple

    """

    rotation_xy = StatusItem('rotation_xy', float)         # current XY rotation angle around Z axis
    """Status of XY rotation

    :returns: current XY rotation angle around Z axis
    :rtype: float

    """


    # I/O
    ain = StatusItem('ain', tuple)                 # current value of the analog input pins
    """Status of analog input pins

    :returns: current value of the analog input pins, one for each pin created
    :rtype: tuple

    """

    aout = StatusItem('aout', tuple)                # current value of the analog output pins
    """Status of current analog output pins

    :returns: current value of the analog output pins, one for each pin created
    :rtype: tuple

    """

    din = StatusItem('din', tuple)                 # current value of the digital input pins
    """Status of digital input pins

    :returns: current value of the digital input pins, one for each pin created
    :rtype: tuple

    """

    dout = StatusItem('dout', tuple)                # current value of the digital output pins
    """Status of digital output pins

    :returns: current value of the digital output pins, one for each pin created
    :rtype: tuple

    """

    # Cooling
    mist = StatusItem('mist', bool)                 # mist self.status
    """Status of mist

    :returns: True if iocontrol.0.coolant-mist is on
    :rtype: bool

    """

    flood = StatusItem('flood', bool)                # flood self.status, either FLOOD_OFF or FLOOD_ON
    """Status of flood

    :returns: True if iocontrol.0.coolant-flood is on
    :rtype: bool

    """


    # Active codes
    to_str = lambda gcodes: " ".join(["M%g" % gcode for gcode in sorted(gcodes[1:]) if gcode != -1])
    mcodes = StatusItem('mcodes', tuple, to_str)     # currently active M-codes
    """Status of M codes

    In a status label to get the active M codes use::

        status:mcodes?text

    :returns: tuple of currently active M-codes
    :rtype: tuple

    """

    to_str = lambda mcodes: " ".join(["G%g" % (mcode/10.) for mcode in sorted(mcodes[1:]) if mcode != -1])
    gcodes = StatusItem('gcodes', tuple, to_str)     # active G-codes for each modal group
    """Status of G codes

    In a status Label to get the active G codes use::

        status:gcodes?text

    :returns: tuple of active G-codes for each modal group
    :rtype: tuple

    """

    # Home and Limit
    homed = StatusItem('homed', tuple)               # homed flag for each joint
    """Status of joint homed

    :returns: tuple of homed flag for each joint 0-8
    :rtype: tuple

    """

    inpos = StatusItem('inpos', bool)                # machine-in-position flag
    """Status of machine in position

    :returns: True if machine is in commanded position
    :rtype: bool

    """

    limit = StatusItem('limit', tuple)               # axis limit self.status masks
    """Status of limits

    :returns: tuple of limit flags for each axis
    :rtype: tuple

    """

    # Delays
    delay_left = StatusItem('delay_left', float)          # remaining time on dwell (G4) command, seconds
    """Status of G4 delay

    :returns: remaining time on G4 dwell command, seconds
    :rtype: float

    """

    input_timeout = StatusItem('input_timeout', bool)        # flag for M66 timer in progress
    """Status of M66 timer

    :returns: True if M66 timer is in progress
    :rtype: bool

    """


    # Lube
    lube = StatusItem('lube', bool)                 # lube on flag
    """Status of lube

    :returns: True if iocontrol.0.lube is on
    :rtype: bool

    """

    lube_level = StatusItem('lube_level', int)            # lube level, reflects iocontrol.0.lube_level
    """Status of lube level

    :returns: True if iocontrol.0.lube_level is on
    :rtype: int

    """

    # Program control
    optional_stop = StatusItem('optional_stop', bool)        # option stop enables flag
    """Status of optional stop

    :returns: True if optional stop is on
    :rtype: bool

    """

    block_delete = StatusItem('block_delete', bool)         # block delete current self.status
    """Status of block delete

    :returns: True if block delete is on
    :rtype: bool

    """

    paused = StatusItem('paused', bool)               # motion paused flag
    """Status of paused

    :returns: True if motion is paused
    :rtype: bool

    """

    feed_hold_enabled = StatusItem('feed_hold_enabled', bool)    # enable flag for feed hold
    """Status of feed hold

    :returns: True if feed hold is on
    :rtype: bool

    """

    # Probe
    probe_tripped = StatusItem('probe_tripped', bool)        # probe tripped flag (latched)
    """Status of probe tripped

    :returns: True if motion.probe-input is on
    :rtype: bool

    """

    # Fix Me I don't think this is correct *******************************
    probe_val = StatusItem('probe_val', bool)            # reflects value of the motion.probe-input pin
    """Status of probe value

    :returns: value of the motion.probe-input pin
    :rtype: bool

    """

    probed_position = StatusItem('probed_position', tuple)     # position where probe tripped
    """Status of probe

    :returns: Tuple of axis positions when the probe was tripped
    :rtype: tuple

    """

    probing = StatusItem('probing', bool)              # probing in progress flag
    """Status of probing

    :returns: True if probing is in progress
    :rtype: bool

    """

    # Program File
    file = StatusItem('file', str)                  # path of currently loaded gcode file
    """Status of current G code file

    :returns: path of currently loaded g code file
    :rtype: str

    """

    to_str = ["NA", "in", "mm", "cm"].__getitem__
    program_units = StatusItem('program_units', int, to_str)# one of CANON_UNITS_INCHES=1, CANON_UNITS_MM=2
    """Status of program units

    :returns: CANON_UNITS_INCHES=1, CANON_UNITS_MM=2
    :rtype: int

    """

    motion_line = StatusItem('motion_line', int)           # source line number motion is currently executing
    """Status of motion line

    :returns: source line number motion is currently executing
    :rtype: int

    """

    current_line = StatusItem('current_line', int)          # currently executing line
    """Status of executing line

    :returns: currently executing line
    :rtype: int

    """

    read_line = StatusItem('read_line', int)             # line the RS274NGC interpreter is currently reading
    """Status of interperter reading

    :returns: line the RS274NGC interpreter is currently reading
    :rtype: int

    """

    call_level = StatusItem('call_level', int)            #
    """Status of call level

    :returns: unknown
    :rtype: int

    """


    # Overrides
    feedrate = StatusItem('feedrate', float)            # feed-rate override, 0-1
    """Status of feed override

    :returns: feed-rate override, 0-1
    :rtype: float

    """

    rapidrate = StatusItem('rapidrate', float)           # rapid-rate override, 0-1
    """Status of rapid override

    :returns: rapid-rate override, 0-1
    :rtype: float

    """

    max_velocity = StatusItem('max_velocity', float)        # max velocity in machine units/s
    """Status of max velocity

    :returns: max velocity in machine units/s
    :rtype: float

    """

    feed_override_enabled = StatusItem('feed_override_enabled', bool)# enable flag for feed override
    """Status of feed override enabled

    :returns: True if feed override is on
    :rtype: bool

    """

    adaptive_feed_enabled = StatusItem('adaptive_feed_enabled', bool)# self.status of adaptive feedrate override
    """Status of adaptive feed enabled

    :returns: True if adaptive feedrate override is on
    :rtype: bool

    """

    # State
    enabled = StatusItem('enabled', bool)              # trajectory planner enabled
    """Status of trajectory planner enabled

    :returns: True if trajectory planner is enabled
    :rtype: bool

    """

    # estop = StatusItem([int], [bool])       # linuxcnc.STATE_ESTOP or not
    estop = StatusItem(item = 'estop',
                        description = "Task Mode")

    # state = StatusItem([int], [str])        # current command execution status. One of RCS_DONE, RCS_EXEC, RCS_ERROR.
    state = StatusItem(item = 'state',
                        description = "Command Execution Status",
                        to_str = {0: "Unknown",
                                    linuxcnc.RCS_DONE: "Done",
                                    linuxcnc.RCS_EXEC: "Exec",
                                    linuxcnc.RCS_ERROR: "Error",}.get
                        )
    """Status of current command execution

    * Done
    * Executing
    * Error

    To return the string in a status label::

        status:state?text

    :returns: current command execution status
    :rtype: int, str

    """

    # exec_state = StatusItem([int], [str])   # task execution state
    exec_state = StatusItem(item = 'exec_state',
                            description = "Task Execution State",
                            to_str = {linuxcnc.EXEC_ERROR: "Error",
                                    linuxcnc.EXEC_DONE: "Done",
                                    linuxcnc.EXEC_WAITING_FOR_MOTION: "Waiting for Motion",
                                    linuxcnc.EXEC_WAITING_FOR_MOTION_QUEUE: "Waiting for Motion Queue",
                                    linuxcnc.EXEC_WAITING_FOR_IO: "Waiting for Pause",
                                    linuxcnc.EXEC_WAITING_FOR_MOTION_AND_IO: "Waiting for Motion and IO",
                                    linuxcnc.EXEC_WAITING_FOR_DELAY: "Waiting for Delay",
                                    linuxcnc.EXEC_WAITING_FOR_SYSTEM_CMD: "Waiting for system CMD",
                                    linuxcnc.EXEC_WAITING_FOR_SPINDLE_ORIENTED: "Waiting for spindle orient"}.get
                            )
    """Status of task execution state

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

        status:exec_state?text

    :returns: current task execution state
    :rtype: int, str

    """

    # task_mode = StatusItem([int], [str])    # current task mode
    task_mode = StatusItem(item = 'task_mode',
                            description = "Task Mode",
                            to_str = {0: "Unknown",
                                        linuxcnc.MODE_MANUAL: "Manual",
                                        linuxcnc.MODE_AUTO: "Auto",
                                        linuxcnc.MODE_MDI: "MDI"}.get
                            )
    """Status of current task mode

    * Manual
    * Auto
    * MDI

    To return the string in a status label::

        status:task_mode?text

    :returns: 
    :rtype: int, str

    """

    # task_paused = StatusItem(bool)          # task paused flag
    task_paused = StatusItem(item = 'task_paused',
                            description = "Program Paused State",
                            to_str = ['False', 'True'].__getitem__)
    """Status of task paused state

    * False
    * True

    To return the string in a status label::

        status:task_paused?text

    :returns: 
    :rtype: bool, str

    """

    # task_state = StatusItem([int], [str])   # current task state
    task_state = StatusItem(item = 'task_state',
                            description = "Task State",
                            to_str = {0: "Unknown",
                                      linuxcnc.STATE_ESTOP: "Estop",
                                      linuxcnc.STATE_ESTOP_RESET: "Reset",
                                      linuxcnc.STATE_ON: "On",
                                      linuxcnc.STATE_OFF: "Off"}.get
                            )
    """Status of current task state

    * Estop
    * Reset
    * On
    * Off

    To return the string in a status label::

        status:task_state?text

    :returns: 
    :rtype: int, str

    """

    # mode of the motion controller
    motion_mode = StatusItem('motion_mode', int,
                            to_str = {0: "Unknown",
                                    linuxcnc.TRAJ_MODE_COORD: "Coord",
                                    linuxcnc.TRAJ_MODE_FREE: "Free",
                                    linuxcnc.TRAJ_MODE_TELEOP: "Teleop"}.get)
    """Status of mode of the motion controller

    * Coord
    * Free
    * Teleop

    To return the string in a status label::

        status:motion_mode?text

    :returns: 
    :rtype: int, str

    """

    # type of the currently executing motion
    motion_type = StatusItem('motion_type', int,
                            to_str = {0: "None",
                                    linuxcnc.MOTION_TYPE_TRAVERSE: "Traverse",
                                    linuxcnc.MOTION_TYPE_FEED: "Linear Feed",
                                    linuxcnc.MOTION_TYPE_ARC: "Arc Feed",
                                    linuxcnc.MOTION_TYPE_TOOLCHANGE: "Tool Change",
                                    linuxcnc.MOTION_TYPE_PROBING: "Probing",
                                    linuxcnc.MOTION_TYPE_INDEXROTARY: "Rotary Index"}.get)
    """Status of type of the currently executing motion

    * Traverse
    * Linear Feed
    * Arc Feed
    * Tool Change
    * Probing
    * Rotary Index

    To return the string in a status label::

        status:motion_type?text

    :returns: 
    :rtype: int, str

    """

    # current state of RS274NGC interpreter
    interp_state = StatusItem('interp_state', int,
                                to_str = {0: "Unknown",
                                        linuxcnc.INTERP_IDLE: "Idle",
                                        linuxcnc.INTERP_READING: "Reading",
                                        linuxcnc.INTERP_PAUSED: "Paused",
                                        linuxcnc.INTERP_WAITING: "Waiting"}.get)
    """Status of current state of RS274NGC interpreter

    * Idle
    * Reading
    * Paused
    * Waiting

    To return the string in a status label::

        status:interp_state?text

    :returns: 
    :rtype: int, str

    """

    # current RS274NGC interpreter return code
    interpreter_errcode = StatusItem('interpreter_errcode', int,
                                    to_str = {0: "Unknown",
                                                1: "Ok",
                                                2: "Exit",
                                                3: "Finished",
                                                4: "Endfile",
                                                4: "File not open",
                                                5: "Error"}.get)
    """Status of current RS274NGC interpreter return code

    * Unknown
    * Ok
    * Exit
    * Finished
    * Endfile
    * File not open
    * Error

    To return the string in a status label::

        status:interpreter_errcode?text

    :returns: 
    :rtype: int, str

    """

    settings = StatusItem('settings', tuple)            # interpreter settings. (sequence_number, feed_rate, speed)
    """Status of 

    :returns: 
    :rtype: bool

    """

    jog_mode_signal = Signal(bool)             # jog mode = true

    linear_units = StatusItem('linear_units', float,
                                to_str = {  0.0: "N/A",
                                            1.0: "mm",
                                            1/25.4: "in"}.get)
    """Status of linear units

    * N/A
    * mm
    * in

    To return the string in a status label::

        status:linear_units?text

    :returns: 
    :rtype: int, str

    """

    angular_units = StatusItem('angular_units', float)
    """Status of angular units

    :returns: angular units
    :rtype: float

    """

    # Tool
    tool_in_spindle = StatusItem('tool_in_spindle', int)       # current tool number
    """Status of tool in spindle

    :returns: current tool number
    :rtype: int

    """

    pocket_prepped = StatusItem('pocket_prepped', int)        # Tx command completed, and this pocket is prepared
    """Status of pocket prepped

    :returns: Tx command completed, and this pocket is prepared
    :rtype: int

    """

    tool_table = StatusItem('tool_table', tuple)          # list of tool entries
    """Status of tool table

    :returns: list of tool entries
    :rtype: tuple

    """

    tool_data = StatusItem('tool_in_spindle', dict)
    """Status of tool data

    :returns: ??
    :rtype: dict

    """

    spindles = StatusItem('spindles', int)
    """Status of number of spindles

    :returns: number of spindles configured
    :rtype: int

    """

    axes = StatusItem('axes', int)
    """Status of axes

    :returns: number of axes configured
    :rtype: int

    """

    joints = StatusItem('joints', int)
    """Status of joints

    :returns: number of joints configured
    :rtype: int

    """

    # Extended status signals
    axis_positions = Signal(tuple)      # ABS, REL and DTG axis values
    joint_positions = Signal(tuple)     # joint pos respecting INI settings
    file_loaded = Signal(str)           # file loaded

    # interpreter settings
    feed = Signal(float)                # Current requested feed
    speed = Signal(float)               # Current requested speed

    on = Signal(bool)
    moving = Signal(bool)
    all_homed = Signal(bool)

    # Gcode Backplot
    backplot_line_selected = Signal(int)
    backplot_loading_started = Signal()
    backplot_loading_progress = Signal(int)
    backplot_loading_finished = Signal()
    backplot_gcode_error = Signal(str)
    reload_backplot = Signal()

    recent_files_changed = Signal(tuple)

    # Emitted when the UI is loaded
    init_ui = Signal()

    # Emitted on app shutdown
    on_shutown = Signal()

    def __init__(self, cycle_time=75):
        super(Status, self).__init__()

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
            STAT.poll()
        except:
            pass

        excluded_items = ['axis', 'joint', 'spindle',
            'acceleration', 'max_acceleration', 'kinematics_type', 'axis_mask',
            'cycle_time', 'echo_serial_number', 'id', 'poll', 'command', 'debug']

        self.old = {}
        # initialize the old values dict
        for item in dir(STAT):
            if item.startswith('_') or item in excluded_items:
                continue
            self.old[item] = getattr(STAT, item)

        # These signals should all cause position updates
        self.position.onValueChanged(self.updateAxisPositions)
        self.g5x_offset.onValueChanged(self.updateAxisPositions)
        self.g92_offset.onValueChanged(self.updateAxisPositions)
        self.tool_offset.onValueChanged(self.updateAxisPositions)
        self.joint_position.onValueChanged(self.updateJointPositions)

        self.homed.onValueChanged(self._allHomed)

        self.task_state.onValueChanged(lambda v: self.on.emit(v == linuxcnc.STATE_ON))

        # File
        self.file.onValueChanged(self.updateFileLoaded)

        # feed and speed signals
        self.settings.onValueChanged(lambda s: self.feed.emit(s[1]))
        self.settings.onValueChanged(lambda s: self.feed.emit(s[2]))

        # Initialize Joint status class
        self.joint = tuple(JointStatus(STAT.joint[i], i) for i in range(9))  #range(INFO.NUM_JOINTS))

        # Initialize Spindle status classes
        self.spindle = tuple(SpindleStatus(STAT.spindle[i], i) for i in range(8))  # range(NUM_SPINDLES))

        # Initialize Error status class
        self.error = _Error()

        # Set up the periodic update timer
        self.timer = QTimer()
        self._cycle_time = cycle_time
        self.timer.timeout.connect(self._periodic)

    def initialise(self):
        """Start the periodic update timer."""
        LOG.debug("Starting periodic updates with {}ms cycle time.".format(self._cycle_time))
        self.timer.start(self._cycle_time)

    def terminate(self):
        """Save persistent settings on terminate."""
        self.on_shutown.emit()
        PREFS.setPref("STATUS", "RECENT_FILES", self.recent_files)
        PREFS.setPref("STATUS", "MAX_RECENT_FILES", self.max_recent_files)

    def _periodic(self):
        # s = time.time()
        try:
            STAT.poll()
        except Exception as e:
            LOG.warning("Status polling failed, is LinuxCNC running?", exc_info=e)
            self.timer.stop()
            return

        for key, old_value in self.old.iteritems():
            new_value = getattr(STAT, key)
            if old_value != new_value:

                # update the status item
                getattr(self, key)._update(new_value)

                # update old values dict
                self.old[key] = new_value

        # joint status updates
        for jnum, joint in enumerate(self.joint):
            joint._update(STAT.joint[jnum])

        # spindle status updates
        for snum, spindle in enumerate(self.spindle):
            spindle._update(STAT.spindle[snum])

        self.error._periodic()
        # print time.time() - s

    def forceUpdate(self):
        """Force update of all status items and emit all signals."""
        STAT.poll()
        for key, value in self.old.iteritems():
            getattr(self, key)._update(value)

        # joint status updates
        for jnum, joint in enumerate(self.joint):
            joint._update(STAT.joint[jnum])

        # spindle status updates
        for snum, spindle in enumerate(self.spindle):
            spindle._update(STAT.spindle[snum])

    # ===========================  Helper Functions  ==========================

    def setReportActualPosition(self, report_actual):
        """
        .. todo

            This needed to be updated for the new StatusItems
        """
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

        self.axis_positions.emit(tuple([pos, tuple(rel), tuple(dtg)]))

    def updateJointPositions(self, pos=None):
        # To allow forced updates, mostly for use by QtDesigner methods
        if pos is None:
            if self._report_actual_position:
                pos = STAT.joint_actual_position
            else:
                pos = STAT.joint_position
        self.joint_positions.emit(pos)

    def updateFileLoaded(self, file):
        if STAT.interp_state == linuxcnc.INTERP_IDLE \
                and STAT.call_level == 0:
            self.file_loaded.emit(file)

    def _allHomed(self):
        self.all_homed.emit(self.allHomed())

    def allHomed(self):
        '''Returns TRUE if all joints are homed.'''
        if self.no_force_homing:
            return True
        for jnum in range(STAT.joints):
            if not STAT.joint[jnum]['homed']:
                return False
        return True


# ==============================================================================
# Joint status class
# ==============================================================================

class JointStatusItem(StatusItem):
    def __init__(self, jnum, item='', typ=None, to_str=str, description=''):
        self.jnum = jnum
        super(JointStatusItem, self).__init__(item, typ, to_str, description)

    @property
    def value(self):
        return self.typ(STAT.joint[self.jnum][self.item])


class JointStatus(QObject):
    """Joint status class.
        An instance of this class is created for each joint.
    """

    def __init__(self, jstat, jnum):
        super(JointStatus, self).__init__()

        self.jstat = jstat
        self.jnum = jnum

        # `linuxcnc.stat.join[n]` attribute signals
        self.jointType = JointStatusItem(jnum, 'jointType', int)               # reflects [JOINT_n]TYPE
        self.backlash = JointStatusItem(jnum, 'backlash', float)               # backlash in machine units
        self.enabled = JointStatusItem(jnum, 'enabled', bool)                  # enabled flag
        self.fault = JointStatusItem(jnum, 'fault', bool)                      # active fault flag
        self.ferror_current = JointStatusItem(jnum, 'ferror_current', float)   # current following error
        self.ferror_highmark = JointStatusItem(jnum, 'ferror_highmark', float) # magnitude of max following error
        self.homed = JointStatusItem(jnum, 'homed', bool)                      # homed flag
        self.homing =JointStatusItem(jnum, 'homing', bool)                     # currently homing flag
        self.inpos = JointStatusItem(jnum, 'inpos', bool)                      # in position flag
        self.input = JointStatusItem(jnum, 'input', float)                      # current input position
        self.max_ferror = JointStatusItem(jnum, 'max_ferror', bool)            # reflects [JOINT_n]FERROR
        self.max_hard_limit = JointStatusItem(jnum, 'max_hard_limit', bool)    # max hard limit exceeded flag
        self.max_soft_limit = JointStatusItem(jnum, 'max_soft_limit', bool)    # max soft limit exceeded flag
        self.min_hard_limit = JointStatusItem(jnum, 'min_hard_limit', bool)    # min hard limit exceeded flag
        self.min_soft_limit = JointStatusItem(jnum, 'min_soft_limit', bool)    # max soft limit exceeded flag
        self.output = JointStatusItem(jnum, 'output', float)                   # commanded output position
        self.override_limits = JointStatusItem(jnum, 'override_limits', bool)  # override limits flag
        self.velocity = JointStatusItem(jnum, 'velocity', float)               # current velocity

        self.units = JointStatusItem(jnum, 'units', float)
        self.min_ferror= JointStatusItem(jnum, 'min_ferror', float)
        self.max_position_limit = JointStatusItem(jnum, 'max_position_limit', float)
        self.min_position_limit = JointStatusItem(jnum, 'min_position_limit', float)


    def _update(self, jstat):
        """Periodic joint item updates."""

        changed_items = tuple(set(jstat.items()) - set(self.jstat.items()))
        for item in changed_items:
            LOG.debug('JOINT_{0} {1}: {2}'.format(self.jnum, item[0], item[1]))
            getattr(self, item[0])._update(item[1])

        self.jstat.update(jstat)


#==============================================================================
# Spindle status class
#==============================================================================

class SpindleStatusItem(StatusItem):
    def __init__(self, snum, item='', typ=None, to_str=str, description=''):
        self.snum = snum
        super(SpindleStatusItem, self).__init__(item, typ, to_str, description)

    @property
    def value(self):
        return self.typ(STAT.spindle[self.snum][self.item])

class SpindleStatus(QObject):
    """Spindle status class.
        An instance of this class is created for each spindle.
    """

    def __init__(self, status, snum):
        super(SpindleStatus, self).__init__()

        self.snum = snum
        self.status = status

        # `linuxcnc.stat.spindle[n]` attribute signals
        self.brake = SpindleStatusItem(snum, 'brake', bool)                 # value of the spindle brake flag
        self.direction = SpindleStatusItem(snum, 'direction', int)          # spindle rotational, forward=1, reverse=-1
        self.enabled = SpindleStatusItem(snum, 'enabled', bool)             # value of the spindle enabled flag
        self.override_enabled = SpindleStatusItem(snum, 'override_enabled', bool)# spindle override enabled flag
        self.override = SpindleStatusItem(snum, 'override', float)               # spindle override value, 0-1
        self.speed = SpindleStatusItem(snum, 'speed', float)                # spindle speed
        self.increasing = SpindleStatusItem(snum, 'increasing', bool)       # spindle speed increasing flag, unclear
        self.orient_state = SpindleStatusItem(snum, 'orient_state', int)    # orient state
        self.orient_fault = SpindleStatusItem(snum, 'orient_fault', bool)   # orient fault
        self.homed = SpindleStatusItem(snum, 'homed', bool)                 # not implemented

    def _update(self, new_status):
        """Periodic spindle item updates."""

        changed_items = tuple(set(new_status.items()) - set(self.status.items()))
        for item in changed_items:
            LOG.debug('SPINDLE_{0} {1}: {2}'.format(self.snum, item[0], item[1]))
            getattr(self, item[0])._update(item[1])

        self.status = new_status

#==============================================================================
# Error status class
#==============================================================================

# ToDo: Move error and message handling into its own data plugin
class _Error(QObject):

    error = linuxcnc.error_channel()

    new_error = Signal(str)
    new_message = Signal(str)

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
            LOG.error(msg)
        elif kind in [linuxcnc.NML_TEXT, linuxcnc.OPERATOR_TEXT,
            linuxcnc.NML_DISPLAY, linuxcnc.OPERATOR_DISPLAY]:
            self.new_message.emit(msg)
            LOG.info(msg)
        else:
            # notifications.show_error("UNKNOWN ERROR!", msg)
            LOG.error(msg)
