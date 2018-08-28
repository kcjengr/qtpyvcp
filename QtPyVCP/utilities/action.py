#!/usr/bin/env python
# coding: utf-8

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

# Description:
#   Collection of linuxcnc.command convenience functions.
#   Incomplete

import time
import linuxcnc

from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtWidgets import QAction, QPushButton

# Set up logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.utilities.info import Info
from QtPyVCP.utilities.status import Status
INFO = Info()
STATUS = Status()
STAT = STATUS.stat

CMD = linuxcnc.command()


class Action(object):
    """Ensures only one instance of StatusPoller exists per python interpretor.
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = _Action()
        return cls._instance

class _Action(object):
    """docstring for _Action"""
    def __init__(self):
        super(_Action, self).__init__()

        self.cmd = linuxcnc.command()
        self.stat = linuxcnc.stat()

        self.coordinates = INFO.getCoordinates()

        self.tmp = None

    def safePoll(self):
        try:
            self.stat.poll()
        except:
            pass

    def loadProgram(self, fname, add_to_recents=True):
        setTaskMode(linuxcnc.MODE_AUTO)
        filter_prog = INFO.getFilterProgram(fname)
        if not filter_prog:
            CMD.program_open(fname.encode('utf-8'))
        else:
            self.open_filter_program(fname, filter_prog)

        if add_to_recents:
            self.addToRecentFiles(fname)

    def addToRecentFiles(self, fname):
        if fname in STATUS.recent_files:
            STATUS.recent_files.remove(fname)
        STATUS.recent_files.insert(0, fname)
        STATUS.recent_files = STATUS.recent_files[:STATUS.max_recent_files]

        # if len(STATUS.recent_files) > STATUS.max_recent_files:
        #     STATUS.recent_files.pop()
        STATUS.recent_files_changed.emit(tuple(STATUS.recent_files))

    def runProgram(self, start_line=0):
        if setTaskMode(linuxcnc.MODE_AUTO):
            self.cmd.auto(linuxcnc.AUTO_RUN, start_line)

    def issueMDI(self, command):
        if setTaskMode(linuxcnc.MODE_MDI):
            self.cmd.mdi(command)
        else:
            LOG.error("Can't issue MDI, machine must be ON, HOMED and IDLE")


    #==========================================================================
    #  Helper functions
    #==========================================================================


    def open_filter_program(self,fname, flt):
        if not self.tmp:
            self._mktemp()
        tmp = os.path.join(self.tmp, os.path.basename(fname))
        print 'temp',tmp
        flt = FilterProgram(flt, fname, tmp, lambda r: r or self._load_filter_result(tmp))

    def _load_filter_result(self, fname):
        if fname:
            self.cmd.program_open(fname)

    def _mktemp(self):
        if self.tmp:
            return
        self.tmp = tempfile.mkdtemp(prefix='emcflt-', suffix='.d')
        atexit.register(lambda: shutil.rmtree(self.tmp))


def setTaskMode(new_mode):
    """Sets task mode, if possible

    Args:
        new_mode (int): linuxcnc.MODE_MANUAL, MODE_MDI or MODE_AUTO

    Returns:
        bool: TRUE if successful
    """
    if isRunning():
        LOG.error("Can't set mode while machine is running")
        return False
    else:
        CMD.mode(new_mode)
        CMD.wait_complete()
        return True

def isRunning():
    """Returns TRUE if machine is moving due to MDI, program execution, etc."""
    if STAT.state == linuxcnc.RCS_EXEC:
        return True
    else:
        return STAT.task_mode == linuxcnc.MODE_AUTO \
            and STAT.interp_state != linuxcnc.INTERP_IDLE


#==========================================================================
#  Boolean action classes
#==========================================================================

class _BoolAction(object):
    """Base boolean action class"""
    def __init__(self, widget, action_type):
        self.widget = widget
        self.action_type = action_type.upper()

        if self.widget is not None:
            if isinstance(self.widget, QAction):
                sig = self.widget.triggered
            else:
                sig = self.widget.clicked
            sig.connect(getattr(self, self.action_type))

    @classmethod
    def ON(cls):
        pass

    @classmethod
    def OFF(cls):
        pass

    @classmethod
    def TOGGLE(cls):
        if cls.state:
            cls.OFF()
        else:
            cls.ON()

    def setEnabled(self, enabled):
        if self.widget is not None:
            self.widget.setEnabled(enabled)

    def setState(self, state):
        if self.widget is not None:
            self.widget.setChecked(state)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.widget.clicked.disconnect(getattr(self, self.action_type))


class EmergencyStop(_BoolAction):

    action_id = 0
    action_text = "E-Stop"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(EmergencyStop, self).__init__(widget, action_type)
        STATUS.estop.connect(lambda v: self.setState(not v))

    @classmethod
    def ON(cls):
        LOG.debug("Setting state red<ESTOP>")
        CMD.state(linuxcnc.STATE_ESTOP)

    @classmethod
    def OFF(cls):
        LOG.debug("Setting state green<ESTOP_RESET>")
        CMD.state(linuxcnc.STATE_ESTOP_RESET)

    @classmethod
    def TOGGLE(cls):
        if STAT.estop:
            cls.OFF()
        else:
            cls.ON()

class MachinePower(_BoolAction):

    action_id = 1
    action_text = "Power"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(MachinePower, self).__init__(widget, action_type)
        STATUS.estop.connect(lambda v: self.setEnabled(not v))
        STATUS.task_state.connect(lambda s: self.setState(s == linuxcnc.STATE_ON))
        self.setEnabled(False)

    @classmethod
    def ON(cls):
        if STAT.task_state == linuxcnc.STATE_ESTOP_RESET:
            LOG.debug("Setting state green<ON>")
            CMD.state(linuxcnc.STATE_ON)
            CMD.wait_complete()
        elif STAT.task_state == linuxcnc.STATE_ESTOP:
            LOG.warn("Can't turn machine green<ON> until out of red<E-Stop>")

    @classmethod
    def OFF(cls):
        if STAT.task_state == linuxcnc.STATE_ON:
            LOG.debug("Setting state red<OFF>")
            CMD.state(linuxcnc.STATE_OFF)
            CMD.wait_complete()

    @classmethod
    def TOGGLE(cls):
        if STATUS.stat.task_state == linuxcnc.STATE_ON:
            cls.OFF()
        else:
            cls.ON()

class Mist(_BoolAction):

    action_id = 2
    action_text = "Mist"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(Mist, self).__init__(widget, action_type)

        self.widget.setEnabled(STAT.state == linuxcnc.STATE_ON)
        self.widget.setChecked(STAT.mist == linuxcnc.MIST_ON)

        STATUS.on.connect(lambda v: self.setEnabled(v))
        STATUS.mist.connect(lambda s: self.setState(s == linuxcnc.MIST_ON))

    @classmethod
    def ON(cls):
        if STAT.task_state == linuxcnc.STATE_ON:
            LOG.debug("Setting mist green<ON>")
            CMD.mist(linuxcnc.MIST_ON)
            CMD.wait_complete()
        elif STAT.task_state == linuxcnc.STATE_ESTOP:
            LOG.warn("Can't turn mist green<ON> with machine red<OFF>")

    @classmethod
    def OFF(cls):
        LOG.debug("Setting mist red<OFF>")
        CMD.mist(linuxcnc.MIST_OFF)
        CMD.wait_complete()

    @classmethod
    def TOGGLE(cls):
        if STATUS.stat.mist == linuxcnc.MIST_ON:
            cls.OFF()
        else:
            cls.ON()

class Flood(_BoolAction):

    action_id = 3
    action_text = "Flood"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(Flood, self).__init__(widget, action_type)

        self.widget.setEnabled(STAT.state == linuxcnc.STATE_ON)
        self.widget.setChecked(STAT.flood == linuxcnc.FLOOD_ON)

        STATUS.on.connect(lambda v: self.setEnabled(v))
        STATUS.flood.connect(lambda s: self.setState(s == linuxcnc.FLOOD_ON))

    @classmethod
    def ON(cls):
        if STAT.task_state == linuxcnc.STATE_ON:
            LOG.debug("Setting flood green<ON>")
            CMD.flood(linuxcnc.FLOOD_ON)
            CMD.wait_complete()
        elif STATUS.stat.task_state == linuxcnc.STATE_ESTOP:
            LOG.warn("Can't turn flood green<ON> with machine red<OFF>")

    @classmethod
    def OFF(cls):
        LOG.debug("Setting flood red<OFF>")
        CMD.flood(linuxcnc.FLOOD_OFF)
        CMD.wait_complete()

    @classmethod
    def TOGGLE(cls):
        if STAT.flood == linuxcnc.FLOOD_ON:
            cls.OFF()
        else:
            cls.ON()

class BlockDelete(_BoolAction):

    action_id = 4
    action_text = "Block Del"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(BlockDelete, self).__init__(widget, action_type)

        self.widget.setEnabled(STAT.state == linuxcnc.STATE_ON)
        self.widget.setChecked(STAT.block_delete)

        STATUS.on.connect(lambda v: self.setEnabled(v))
        STATUS.block_delete.connect(lambda s: self.setState(s))

    @classmethod
    def ON(cls):
        if STAT.task_state == linuxcnc.STATE_ON:
            LOG.debug("Setting block delete green<ACTIVE>")
            CMD.set_block_delete(True)
            CMD.wait_complete()

    @classmethod
    def OFF(cls):
        LOG.debug("Setting block delete red<INACTIVE>")
        CMD.set_block_delete(False)
        CMD.wait_complete()

    @classmethod
    def TOGGLE(cls):
        if STAT.block_delete == True:
            cls.OFF()
        else:
            cls.ON()

class JogMode(_BoolAction):

    action_id = 8
    action_text = "Jog"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(JogMode, self).__init__(widget, action_type)

        self.widget.setEnabled(STAT.state == linuxcnc.STATE_ON)
        self.widget.setChecked(STATUS.jog_mode)

        STATUS.on.connect(lambda v: self.setEnabled(v))
        STATUS.jog_mode_signal.connect(lambda s: self.setState(s))

    @classmethod
    def ON(cls):
        LOG.debug("Jog Mode green<Jog>")
        STATUS.setJogMode(True)

    @classmethod
    def OFF(cls):
        LOG.debug("Jog Mode red<Step>")
        STATUS.setJogMode(False)

    @classmethod
    def TOGGLE(cls):
        if STATUS.jog_mode == True:
            cls.OFF()
        else:
            cls.ON()

class StepMode(_BoolAction):

    action_id = 9
    action_text = "Step"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(StepMode, self).__init__(widget, action_type)

        self.widget.setEnabled(STAT.state == linuxcnc.STATE_ON)
        self.widget.setChecked(not STATUS.jog_mode)

        STATUS.on.connect(lambda v: self.setEnabled(v))
        STATUS.jog_mode_signal.connect(lambda s: self.setState(not s))

    @classmethod
    def ON(cls):
        LOG.debug("Step Mode green<Step>")
        STATUS.setJogMode(False)

    @classmethod
    def OFF(cls):
        LOG.debug("Step Mode red<Jog>")
        STATUS.setJogMode(True)

    @classmethod
    def TOGGLE(cls):
        if STATUS.jog_mode == False:
            cls.OFF()
        else:
            cls.ON()

class OptionalStop(_BoolAction):

    action_id = 5
    action_text = "Opt Stop"

    def __init__(self, widget=None, action_type='TOGGLE'):
        super(OptionalStop, self).__init__(widget, action_type)

        self.widget.setEnabled(STAT.state == linuxcnc.STATE_ON)
        self.widget.setChecked(STAT.optional_stop)

        STATUS.on.connect(lambda v: self.setEnabled(v))
        STATUS.optional_stop.connect(lambda s: self.setState(s))

    @classmethod
    def ON(cls):
        if STAT.task_state == linuxcnc.STATE_ON:
            LOG.debug("Setting optional stop green<ACTIVE>")
            CMD.set_optional_stop(True)
            CMD.wait_complete()

    @classmethod
    def Off(cls):
        LOG.debug("Setting optional stop red<INACTIVE>")
        CMD.set_optional_stop(False)
        CMD.wait_complete()

    @classmethod
    def TOGGLE(cls):
        if STAT.optional_stop == True:
            cls.OFF()
        else:
            cls.ON()


#==============================================================================
#  Axis/Joint actions
#==============================================================================

class _JointAction(object):

    def __init__(self, widget, method):
        self.widget = widget

        if self.widget is not None and method is not None:
            if isinstance(self.widget, QAction):
                sig = self.widget.triggered
            else:
                sig = self.widget.clicked
            try:
                sig.connect(getattr(self, 'btn_' + method))
            except:
                LOG.error("Failed to initialize action.", exc_info=True)


def getAxisLetter(axis):
    """Takes an axis letter or number and returns the axis letter"""
    if isinstance(axis, int):
        return ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w', 'all'][axis]
    return axis.lower()

def getAxisNumber(axis):
    if isinstance(axis, str):
        return ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w', 'all'].index(axis.lower())
    return axis

#==============================================================================
# Homing action
#==============================================================================

def homeJoint(jnum):
    setTaskMode(linuxcnc.MODE_MANUAL)
    CMD.teleop_enable(False)
    CMD.home(jnum)

def unhomeJoint(jnum):
    setTaskMode(linuxcnc.MODE_MANUAL)
    CMD.teleop_enable(False)
    CMD.unhome(jnum)


class Home(_JointAction):

    action_id = 6
    action_text = "Home"

    def __init__(self, widget, method='homeAxis', axis='x', direction=0):
        super(Home, self).__init__(widget, method)

        self._axis = getAxisLetter(axis)
        if self._axis == 'all':
            self._joint = -1
        else:
            self._joint = INFO.ALETTER_JNUM_DICT.get(self._axis)

        if self._joint is None:
            # the machine does not have a joint with this number
            self.widget.setEnabled(False)
            self.widget.setToolTip("{} axis not configured".format(self._axis.upper()))
            # TODO: might consider hiding the widget instead of disabling it
            # self.widget.hide()
            return

        self._homed = False

        STATUS.on.connect(lambda s: self.widget.setEnabled(s))
        STATUS.executing.connect(lambda s: self.wigget.setEnabled(not s))

        if method is not None:
            STATUS.joint.homed.connect(self.onHomed)
            STATUS.all_homed.connect(lambda v: self.onHomed(-1, v))

    def btn_homeAxis(self, checked):
        if self._homed:
            self.__class__.unhomeAxis(self._axis)
        else:
            self.__class__.homeAxis(self._axis)

    def btn_homeAll(self, checked):
        if self._homed:
            self.__class__.unhomeAll()
        else:
            self.__class__.homeAll()

    def onHomed(self, jnum, homed):
        if jnum == self._joint:
            self._homed = homed
            if homed:
                self.widget.setText('Unhome &{}'.format(self._axis.capitalize()))
            else:
                self.widget.setText('Home &{}'.format(self._axis.capitalize()))

    @classmethod
    def homeAll(cls):
        LOG.info('Homing All')
        homeJoint(-1)

    @classmethod
    def homeAxis(cls, axis=None):
        axis = getAxisLetter(axis)
        if axis.lower() == 'all':
            cls.homeAll()
            return
        jnum = INFO.COORDINATES.index(axis)
        LOG.info('Homing Axis: {}'.format(axis.upper()))
        homeJoint(jnum)

    @classmethod
    def homeJoint(cls, jnum=0):
        LOG.info('Homing Joint: {}'.format(jnum))
        homeJoint(jnum)

    @classmethod
    def unhomeAll(cls):
        LOG.info('unoming All')
        unhomeJoint(-1)

    @classmethod
    def unhomeAxis(cls, axis=None):
        axis = getAxisLetter(axis)
        if axis.lower() == 'all':
            cls.unhomeAll()
            return
        jnum = INFO.COORDINATES.index(axis)
        LOG.info('Unhoming Axis: {}'.format(axis.upper()))
        unhomeJoint(jnum)

    @classmethod
    def unhomeJoint(cls, jnum=0):
        LOG.info('Unhoming Joint: {}'.format(jnum))
        unhomeJoint(jnum)


class Jogging(object):

    action_id = 7
    action_text = "Jog"

    def __init__(self, widget=None, method='jog', axis=0, direction=0):
        self.widget = widget
        self._axis = axis
        self._direction = direction

        if self.widget is not None and method is not None:
            self.widget.pressed.connect(self.btn_jog)
            self.widget.released.connect(self.btn_stop)

        STATUS.on.connect(lambda s: self.widget.setEnabled(s))
        STATUS.executing.connect(lambda s: self.widget.setEnabled(not s))

    def btn_jog(self):
        self.__class__.autoJog(self._axis, self._direction)

    def btn_stop(self):
        self.__class__.autoJog(self._axis, 0)

    @classmethod
    def autoJog(cls, axis, direction):
        axis = getAxisNumber(axis)
        jog_joint = 0
        if STAT.motion_mode == linuxcnc.TRAJ_MODE_FREE:
            jog_joint = 1
            # CMD.traj_mode(linuxcnc.TRAJ_MODE_FREE)

        if axis in (3,4,5):
            rate = STATUS.angular_jog_velocity / 60
        else:
            rate = STATUS.linear_jog_velocity / 60

        distance = STATUS.jog_increment
        print axis, direction, jog_joint, distance

        if direction == 0:
            CMD.jog(linuxcnc.JOG_STOP, jog_joint, axis)
            return

        if distance == 0:
            CMD.jog(linuxcnc.JOG_CONTINUOUS, jog_joint, axis, direction * rate)
        else:
            CMD.jog(linuxcnc.JOG_INCREMENT, jog_joint, axis, direction * rate, distance)

    @classmethod
    def jog(cls, axis, direction, velocity, distance=0):
        axis = getAxisNumber(axis)
        print axis, direction, velocity, distance
        if direction == 0:
            CMD.jog(linuxcnc.JOG_STOP, cls.jog_joint, axis)
        else:
            if distance == 0:
                CMD.jog(linuxcnc.JOG_CONTINUOUS, cls.jog_joint, axis, direction * velocity)
            else:
                CMD.jog(linuxcnc.JOG_INCREMENT, cls.jog_joint, axis, direction * velocity, distance)

    @classmethod
    def bindKey(cls, axis, key):
        if axis is None and isinstance(cls, Jog):
            axis = cls.axis
        print "axis: ", axis, cls
        CMD.jog(linuxcnc.JOG_STOP, 0, axis)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.widget.pressed.disconnect(getattr(self, self.action_type))
        self.widget.released.disconnect(self.STOP)

action_by_id = {
    0 : EmergencyStop,
    1 : MachinePower,
    2 : Mist,
    3 : Flood,
    4 : BlockDelete,
    5 : OptionalStop,
    6 : Home,
    7 : Jogging,
    8 : JogMode,
    9 : StepMode
}
















# ################################################################
# # Action class
# ################################################################
# class _VCP_Action(object):
#     def __init__(self):
#         self.stat = linuxcnc.stat()
#         self.cmd = linuxcnc.command()
#         self.tmp = None

#     def SET_ESTOP_STATE(self, state):
#         if state:
#             self.cmd.state(linuxcnc.STATE_ESTOP)
#         else:
#             self.cmd.state(linuxcnc.STATE_ESTOP_RESET)

#     def SET_MACHINE_STATE(self, state):
#         if state:
#             self.cmd.state(linuxcnc.STATE_ON)
#         else:
#             self.cmd.state(linuxcnc.STATE_OFF)

#     def SET_MACHINE_HOMING(self, joint):
#         LOG.info('Homing Joint: {}'.format(joint))
#         self.set_task_mode(linuxcnc.MODE_MANUAL)
#         self.cmd.teleop_enable(False)
#         self.cmd.home(joint)

#     def SET_MACHINE_UNHOMED(self, joint):
#         self.set_task_mode(linuxcnc.MODE_MANUAL)
#         self.cmd.teleop_enable(False)
#         #self.cmd.traj_mode(linuxcnc.TRAJ_MODE_FREE)
#         self.cmd.unhome(joint)

#     def SET_AUTO_MODE(self):
#         self.set_task_mode(linuxcnc.MODE_AUTO)

#     def SET_LIMITS_OVERRIDE(self):
#         self.cmd.override_limits()

#     def SET_MDI_MODE(self):
#         self.set_task_mode(linuxcnc.MODE_MDI)

#     def SET_MANUAL_MODE(self):
#         self.set_task_mode(linuxcnc.MODE_MANUAL)

#     def MDI(self, code):
#         self.set_task_mode(linuxcnc.MODE_MDI)
#         self.cmd.mdi('%s'%code)

#     def UPDATE_VAR_FILE(self):
#         self.set_task_mode(linuxcnc.MODE_MANUAL)
#         self.set_task_mode(linuxcnc.MODE_MDI)

#     def OPEN_PROGRAM(self, fname):
#         self.set_task_mode(linuxcnc.MODE_AUTO)
#         flt = INFO.get_filter_program(str(fname))
#         if not flt:
#             self.cmd.program_open(str(fname))
#         else:
#             self.open_filter_program(str(fname), flt)
#         STATUS.emit('reload-display')

#     def SET_AXIS_ORIGIN(self,axis,value):
#         m = "G10 L20 P0 %s%f"%(axis,value)
#         success, prev_mode = self.set_task_mode(linuxcnc.MODE_MDI)
#         self.cmd.mdi(m)
#         self.set_task_mode(premode)
#         STATUS.emit('reload-display')

#     def RUN(self):
#         self.set_task_mode(linuxcnc.MODE_AUTO)
#         self.cmd.auto(linuxcnc.AUTO_RUN,0)

#     def ABORT(self):
#         self.set_task_mode(linuxcnc.MODE_AUTO)
#         self.cmd.abort()

#     def PAUSE(self):
#         if not STATUS.stat.paused:
#             self.cmd.auto(linuxcnc.AUTO_PAUSE)
#         else:
#             LOG.debug('resume')
#             self.cmd.auto(linuxcnc.AUTO_RESUME)

#     def SET_RAPID_RATE(self, rate):
#         self.cmd.rapidrate(rate/100.0)
#     def SET_FEED_RATE(self, rate):
#         self.cmd.feedrate(rate/100.0)
#     def SET_SPINDLE_RATE(self, rate):
#         self.cmd.spindleoverride(rate/100.0)
#     def SET_JOG_RATE(self, rate):
#         STATUS.set_jog_rate(float(rate))
#     def SET_JOG_INCR(self, incr):
#         pass

#     def SET_SPINDLE_ROTATION(self, direction = 1, rpm = 100):
#         self.cmd.spindle(direction,rpm)
#     def SET_SPINDLE_FASTER(self):
#         self.cmd.spindle(linuxcnc.SPINDLE_INCREASE)
#     def SET_SPINDLE_SLOWER(self):
#         self.cmd.spindle(linuxcnc.SPINDLE_DECREASE)
#     def SET_SPINDLE_STOP(self):
#         self.cmd.spindle(linuxcnc.SPINDLE_OFF)

#     def ZERO_G92_OFFSET (self, widget):
#         self.MDI("G92.1")
#         STATUS.emit('reload-display')
#     def ZERO_ROTATIONAL_OFFSET(self, widget):
#         self.MDI("G10 L2 P0 R 0")
#         STATUS.emit('reload-display')

#     def RECORD_CURRENT_MODE(self):
#         mode = STATUS.get_current_mode()
#         self.last_mode = mode
#         return mode

#     def RESTORE_RECORDED_MODE(self):
#         self.set_task_mode(self.last_mode)

#     def DO_JOG(self, axisnum, direction):
#         distance = STATUS.current_jog_distance
#         if axisnum in (3,4,5):
#             rate = STATUS.angular_jog_velocity/60
#         else:
#             rate = STATUS.current_jog_rate/60
#         self.JOG(axisnum, direction, rate, distance)

#     def JOG(self, axisnum, direction, rate, distance=0):
#         jjogmode,j_or_a = STATUS.get_jog_info(axisnum)
#         if direction == 0:
#             self.cmd.jog(linuxcnc.JOG_STOP, jjogmode, j_or_a)
#         else:
#             if distance == 0:
#                 self.cmd.jog(linuxcnc.JOG_CONTINUOUS, jjogmode, j_or_a, direction * rate)
#             else:
#                 self.cmd.jog(linuxcnc.JOG_INCREMENT, jjogmode, j_or_a, direction * rate, distance)

#     def TOGGLE_FLOOD(self):
#         self.cmd.flood(not(STATUS.stat.flood))
#     def SET_FLOOD_ON(self):
#         self.cmd.flood(1)
#     def SET_FLOOD_OFF(self):
#         self.cmd.flood(0)

#     def TOGGLE_MIST(self):
#         self.cmd.mist(not(STATUS.stat.mist))
#     def SET_MIST_ON(self):
#         self.cmd.mist(1)
#     def SET_MIST_OFF(self):
#         self.cmd.mist(0)

#     def RELOAD_TOOLTABLE(self):
#         self.cmd.load_tool_table()

#     def TOGGLE_OPTIONAL_STOP(self):
#         self.cmd.set_optional_stop(not(STATUS.stat.optional_stop))
#     def SET_OPTIONAL_STOP_ON(self):
#         self.cmd.set_optional_stop(True)
#     def SET_OPTIONAL_STOP_OFF(self):
#         self.cmd.set_optional_stop(False)

#     def TOGGLE_BLOCK_DELETE(self):
#         self.cmd.set_block_delete(not(STATUS.stat.block_delete))
#     def SET_BLOCK_DELETE_ON(self):
#         self.cmd.set_block_delete(True)
#     def SET_BLOCK_DELETE_OFF(self):
#         self.cmd.set_block_delete(False)

#     ######################################
#     # Action Helper functions
#     ######################################


#     def set_task_mode(new_mode):
#         """Sets task mode, if possible

#         Args:
#             new_mode (int): linuxcnc.MODE_MANUAL, MODE_MDI or MODE_AUTO

#         Returns:
#             tuple: (success, previous_mode)
#         """
#         if is_running():
#             LOG.error("Can't set mode while machine is running")
#             return (False, current_mode)
#         current_mode = self.stat.task_mode
#         if current_mode == new_mode:
#             return (True, current_mode)
#         else:
#             self.cmd.mode(new_mode)
#             self.cmd.wait_complete()
#             return (True, current_mode)

#     def is_running(self):
#         """Returns TRUE if machine is moving due to MDI, program execution, etc."""
#         self.stat.poll()
#         if stat.state == linuxcnc.RCS_EXEC:
#             return True
#         else:
#             return stat.task_mode == linuxcnc.MODE_AUTO \
#                 and stat.interp_state != linuxcnc.INTERP_IDLE

#     def open_filter_program(self,fname, flt):
#         if not self.tmp:
#             self._mktemp()
#         tmp = os.path.join(self.tmp, os.path.basename(fname))
#         print 'temp',tmp
#         flt = FilterProgram(flt, fname, tmp, lambda r: r or self._load_filter_result(tmp))

#     def _load_filter_result(self, fname):
#         if fname:
#             self.cmd.program_open(fname)

#     def _mktemp(self):
#         if self.tmp:
#             return
#         self.tmp = tempfile.mkdtemp(prefix='emcflt-', suffix='.d')
#         atexit.register(lambda: shutil.rmtree(self.tmp))

########################################################################
# Filter Class
########################################################################
import os, sys, time, select, re
import tempfile, atexit, shutil

# slightly reworked code from gladevcp
# loads a filter program and collects the result
progress_re = re.compile("^FILTER_PROGRESS=(\\d*)$")
class FilterProgram:
    def __init__(self, program_filter, infilename, outfilename, callback=None):
        import subprocess
        outfile = open(outfilename, "w")
        infilename_q = infilename.replace("'", "'\\''")
        env = dict(os.environ)
        env['AXIS_PROGRESS_BAR'] = '1'
        p = subprocess.Popen(["sh", "-c", "%s '%s'" % (program_filter, infilename_q)],
                              stdin=subprocess.PIPE,
                              stdout=outfile,
                              stderr=subprocess.PIPE,
                              env=env)
        p.stdin.close()  # No input for you
        self.p = p
        self.stderr_text = []
        self.program_filter = program_filter
        self.callback = callback
        self.gid = STATUS.connect('periodic', self.update)
        #progress = Progress(1, 100)
        #progress.set_text(_("Filtering..."))

    def update(self, w):
        if self.p.poll() is not None:
            self.finish()
            STATUS.disconnect(self.gid)
            return False

        r,w,x = select.select([self.p.stderr], [], [], 0)
        if not r:
            return True
        stderr_line = self.p.stderr.readline()
        m = progress_re.match(stderr_line)
        if m:
            pass #progress.update(int(m.group(1)), 1)
        else:
            self.stderr_text.append(stderr_line)
            sys.stderr.write(stderr_line)
        return True

    def finish(self):
        # .. might be something left on stderr
        for line in self.p.stderr:
            m = progress_re.match(line)
            if not m:
                self.stderr_text.append(line)
                sys.stderr.write(line)
        r = self.p.returncode
        if r:
            self.error(r, "".join(self.stderr_text))
        if self.callback:
            self.callback(r)

    def error(self, exitcode, stderr):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                _("The program %(program)r exited with code %(code)d.  "
                "Any error messages it produced are shown below:")
                    % {'program': self.program_filter, 'code': exitcode})
        diaLOG.format_secondary_text(stderr)
        diaLOG.run()
        diaLOG.destroy()
