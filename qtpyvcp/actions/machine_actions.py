#!/usr/bin/env python
# coding: utf-8

import sys
import time
import linuxcnc
from qtpy.QtWidgets import QComboBox

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.actions.base_actions import setTaskMode
from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')
STAT = STATUS.stat

from qtpyvcp.utilities.info import Info
INFO = Info()
CMD = linuxcnc.command()


# -------------------------------------------------------------------------
# E-STOP action
# -------------------------------------------------------------------------
class estop:
    """E-Stop action group"""
    @staticmethod
    def activate():
        """Set E-Stop active"""
        LOG.debug("Setting state red<ESTOP>")
        CMD.state(linuxcnc.STATE_ESTOP)

    @staticmethod
    def reset():
        """Resets E-Stop"""
        LOG.debug("Setting state green<ESTOP_RESET>")
        CMD.state(linuxcnc.STATE_ESTOP_RESET)

    @staticmethod
    def toggle():
        """Toggles E-Stop state"""
        if estop.is_activated():
            estop.reset()
        else:
            estop.activate()

    @staticmethod
    def is_activated():
        """Checks if E_Stop is activated.

        Returns:
            bool : True if E-Stop is active, else False.
        """
        return bool(STAT.estop)

def _estop_ok(widget=None):
    # E-Stop is ALWAYS ok, but provide this method for consistency
    _estop_ok.msg = ""
    return True

def _estop_bindOk(widget):
    widget.setChecked(STAT.estop != linuxcnc.STATE_ESTOP)
    STATUS.estop.onValueChanged(lambda v: widget.setChecked(not v))

estop.activate.ok = estop.reset.ok = estop.toggle.ok = _estop_ok
estop.activate.bindOk = estop.reset.bindOk = estop.toggle.bindOk = _estop_bindOk

# -------------------------------------------------------------------------
# POWER action
# -------------------------------------------------------------------------
class power:
    """Power action group"""
    @staticmethod
    def on():
        """Turns machine power On"""
        LOG.debug("Setting state green<ON>")
        CMD.state(linuxcnc.STATE_ON)

    @staticmethod
    def off():
        """Turns machine power Off"""
        LOG.debug("Setting state red<OFF>")
        CMD.state(linuxcnc.STATE_OFF)

    @staticmethod
    def toggle():
        """Toggles machine power On/Off"""
        if power.is_on():
            power.off()
        else:
            power.on()

    @staticmethod
    def is_on():
        """Checks if power is on.

        Returns:
            bool : True if power is on, else False.
        """
        return STAT.task_state == linuxcnc.STATE_ON

def _power_ok(widget=None):
    if STAT.task_state == linuxcnc.STATE_ESTOP_RESET:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Can't turn machine ON until out of E-Stop"

    _power_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _power_bindOk(widget):
    _power_ok(widget)
    widget.setChecked(STAT.task_state == linuxcnc.STATE_ON)
    STATUS.estop.onValueChanged(lambda: _power_ok(widget))
    STATUS.on.connect(lambda v: widget.setChecked(v))

power.on.ok = power.off.ok = power.toggle.ok = _power_ok
power.on.bindOk = power.off.bindOk = power.toggle.bindOk = _power_bindOk

# -------------------------------------------------------------------------
# MDI action
# -------------------------------------------------------------------------

PREVIOUS_MODE = None

def _resetMode(interp_state):
    global PREVIOUS_MODE
    if  PREVIOUS_MODE is not None and interp_state == linuxcnc.INTERP_IDLE:
        if setTaskMode(PREVIOUS_MODE):
            LOG.debug("Successfully reset task_mode after MDI")
        PREVIOUS_MODE = None

STATUS.interp_state.onValueChanged(_resetMode)

def issue_mdi(command, reset=True):
    """Issue an MDI command.

        An MDI command can be issued any time the machine is homed (if not
        NOT_FORCE_HOMING in the INI) and the interpreter is IDLE.  The task
        mode will automatically be switched to MDI prior to issuing the command
        and will be returned to the previous mode when the interpreter becomes IDLE.

    Args:
        command (str) : A valid RS274 gcode command string.
        rest (bool, optional): Whether to reset the Task Mode to the state
            the machine was in prior to issuing the MDI command.

    """
    if reset:
        # save the previous mode
        global PREVIOUS_MODE
        PREVIOUS_MODE = STAT.task_mode
        # Force `interp_state` update on next status cycle. This is needed because
        # some commands might take less than `cycle_time` (50ms) to complete,
        # so status would not even notice that the interp_state had changed and the
        # reset mode method would not be called.
        STATUS.old['interp_state'] = -1

    if setTaskMode(linuxcnc.MODE_MDI):
        LOG.info("Issuind MDI command: {}".format(command))
        CMD.mdi(command)
    else:
        LOG.error("Failed to issue MDI command: {}".format(command))

def _issue_mdi_ok(mdi_cmd='', widget=None):
    if STAT.task_state == linuxcnc.STATE_ON \
        and STATUS.allHomed() \
        and STAT.interp_state == linuxcnc.INTERP_IDLE:

        ok = True
        msg = ""

    else:
        ok = False
        msg = "Can't issue MDI unless machine is ON, HOMED and IDLE"

    _issue_mdi_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _issue_mdi_bindOk(mdi_cmd='', widget=None):
    STATUS.task_state.onValueChanged(lambda: _issue_mdi_ok(mdi_cmd=mdi_cmd, widget=widget))
    STATUS.interp_state.onValueChanged(lambda: _issue_mdi_ok(mdi_cmd=mdi_cmd, widget=widget))
    STATUS.homed.onValueChanged(lambda: _issue_mdi_ok(mdi_cmd=mdi_cmd, widget=widget))

issue_mdi.ok = _issue_mdi_ok
issue_mdi.bindOk = _issue_mdi_bindOk

# -------------------------------------------------------------------------
# WORK COORDINATES action
# -------------------------------------------------------------------------

def set_work_coord(coord):
    issue_mdi(coord)

def _set_work_coord_bindOk(coord='', widget=None):
    coord = coord.upper()
    _issue_mdi_bindOk(coord, widget=widget)
    if isinstance(widget, QComboBox):
        widget.setCurrentText(coord)
        widget.setCurrentText(STATUS.g5x_index.to_str(STATUS.g5x_index.value))
        STATUS.g5x_index.onValueChanged(lambda wc: widget.setCurrentText(STATUS.g5x_index.to_str(wc)))
    else:
        widget.setCheckable(True)
        widget.setChecked(STATUS.g5x_index.to_str(STATUS.g5x_index.value) == coord)
        STATUS.g5x_index.onValueChanged(lambda wc: widget.setChecked(STATUS.g5x_index.to_str(wc) == coord))

set_work_coord.ok = _issue_mdi_ok
set_work_coord.bindOk = _set_work_coord_bindOk

# -------------------------------------------------------------------------
# FEED HOLD action
# -------------------------------------------------------------------------
class feedhold:

    # FIXME: Not sure what feedhold does, or how to turn it ON/OFF, if it even can be.

    @staticmethod
    def enable():
        LOG.info("Setting feedhold ENABLED")
        CMD.set_feed_hold(1)

    @staticmethod
    def disable():
        LOG.info("Setting feedhold DISABLED")
        CMD.set_feed_hold(0)

    @staticmethod
    def toggle_enable():
        if STAT.feed_hold_enabled:
            feedhold.disable()
        else:
            feedhold.enable()

    @staticmethod
    def on():
        pass

    @staticmethod
    def off():
        pass

    @staticmethod
    def toggle():
        pass

def _feed_hold_ok(widget=None):
    return True

def _feed_hold_bindOk(widget):
    pass

feedhold.enable.ok = feedhold.disable.ok = feedhold.toggle_enable.ok = _feed_hold_ok
feedhold.enable.bindOk = feedhold.disable.bindOk = feedhold.toggle_enable.bindOk = _feed_hold_bindOk

# -------------------------------------------------------------------------
# FEED OVERRIDE actions
# -------------------------------------------------------------------------

class feed_override:
    @staticmethod
    def enable():
        CMD.set_feed_override(True)

    @staticmethod
    def disable():
        CMD.set_feed_override(False)

    @staticmethod
    def toggle_enable():
        if STAT.feed_override_enabled:
            feed_override.disable()
        else:
            feed_override.enable()

    @staticmethod
    def set(value):
        CMD.feedrate(float(value) / 100)

    @staticmethod
    def reset():
        CMD.feedrate(1.0)

def _feed_override_enable_ok(widget=None):
    if STAT.task_state == linuxcnc.STATE_ON \
        and STAT.interp_state == linuxcnc.INTERP_IDLE:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be ON and IDLE to enable/disable feed override"

    _feed_override_enable_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _feed_override_enable_bindOk(widget):
    STATUS.task_state.onValueChanged(lambda: _feed_override_enable_ok(widget))
    STATUS.interp_state.onValueChanged(lambda: _feed_override_enable_ok(widget))
    STATUS.feed_override_enabled.onValueChanged(widget.setChecked)

def _feed_override_ok(value=100, widget=None):
    if STAT.task_state == linuxcnc.STATE_ON and STAT.feed_override_enabled == 1:
        ok = True
        msg = ""
    elif STAT.task_state != linuxcnc.STATE_ON:
        ok = False
        msg = "Machine must be ON to set feed override"
    elif STAT.feed_override_enabled == 0:
        ok = False
        msg = "Feed override is not enabled"
    else:
        ok = False
        msg = "Feed override can not be changed"

    _feed_override_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _feed_override_bindOk(value=100, widget=None):

    # This will work for any widget
    STATUS.task_state.onValueChanged(lambda: _feed_override_ok(widget=widget))
    STATUS.feed_override_enabled.onValueChanged(lambda: _feed_override_ok(widget=widget))

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(0)
        widget.setMaximum(INFO.maxFeedOverride() * 100)
        widget.setValue(100)
        feed_override.set(100)

        STATUS.feedrate.onValueChanged(lambda v: widget.setValue(v * 100))
    except AttributeError:
        pass
    except:
        LOG.exception('Error in feed_override bindOk')

feed_override.set.ok = feed_override.reset.ok = _feed_override_ok
feed_override.set.bindOk = feed_override.reset.bindOk = _feed_override_bindOk
feed_override.enable.ok = feed_override.disable.ok = feed_override.toggle_enable.ok = _feed_override_enable_ok
feed_override.enable.bindOk = feed_override.disable.bindOk = feed_override.toggle_enable.bindOk = _feed_override_enable_bindOk

# -------------------------------------------------------------------------
# RAPID OVERRIDE actions
# -------------------------------------------------------------------------

class rapid_override:
    @staticmethod
    def set(value):
        CMD.rapidrate(float(value) / 100)

    @staticmethod
    def reset():
        CMD.rapidrate(1.0)

def _rapid_override_ok(value=100, widget=None):
    if STAT.task_state == linuxcnc.STATE_ON:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be ON to set rapid override"

    _rapid_override_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _rapid_override_bindOk(value=100, widget=None):

    # This will work for any widget
    STATUS.task_state.onValueChanged(lambda: _rapid_override_ok(widget=widget))

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(0)
        widget.setMaximum(100)
        widget.setValue(100)
        rapid_override.set(100)

        STATUS.rapidrate.onValueChanged(lambda v: widget.setValue(v * 100))
    except AttributeError:
        pass
    except:
        LOG.exception('Error in rapid_override bindOk')

rapid_override.set.ok = rapid_override.reset.ok = _rapid_override_ok
rapid_override.set.bindOk = rapid_override.reset.bindOk = _rapid_override_bindOk

# -------------------------------------------------------------------------
# MAX VEL OVERRIDE actions
# -------------------------------------------------------------------------

class max_velocity:
    @staticmethod
    def set(value):
        CMD.maxvel(float(value) / 60)

    @staticmethod
    def reset():
        CMD.maxvel(INFO.maxVelocity() / 60)

def _max_velocity_ok(value=100, widget=None):
    if STAT.task_state == linuxcnc.STATE_ON:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be ON to set max velocity"

    _max_velocity_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _max_velocity_bindOk(value=100, widget=None):

    # This will work for any widget
    STATUS.task_state.onValueChanged(lambda: _max_velocity_ok(widget=widget))

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(0)
        widget.setMaximum(INFO.maxVelocity())
        widget.setValue(INFO.maxVelocity())

        STATUS.max_velocity.onValueChanged(lambda v: widget.setValue(v * 60))
    except AttributeError:
        pass
    except:
        LOG.exception('Error in max_velocity bindOk')

max_velocity.set.ok = max_velocity.reset.ok = _max_velocity_ok
max_velocity.set.bindOk = max_velocity.reset.bindOk = _max_velocity_bindOk


# -------------------------------------------------------------------------
# set MODE actions
# -------------------------------------------------------------------------
class mode:
    @staticmethod
    def manual():
        setTaskMode(linuxcnc.MODE_MANUAL)

    @staticmethod
    def auto():
        setTaskMode(linuxcnc.MODE_AUTO)

    @staticmethod
    def mdi():
        setTaskMode(linuxcnc.MODE_MDI)

def _mode_ok(widget=None):
    if STAT.task_state == linuxcnc.STATE_ON and STAT.interp_state == linuxcnc.INTERP_IDLE:
        ok = True
        msg = ""

    else:
        ok = False
        msg = "Can't set mode when not ON and IDLE"

    _mode_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _manual_bindOk(widget):
    widget.setChecked(STAT.task_mode == linuxcnc.MODE_MANUAL)
    STATUS.task_state.onValueChanged(lambda: _mode_ok(widget))
    STATUS.interp_state.onValueChanged(lambda: _mode_ok(widget))
    STATUS.task_mode.onValueChanged(lambda m: widget.setChecked(m == linuxcnc.MODE_MANUAL))

mode.manual.ok = _mode_ok
mode.manual.bindOk = _manual_bindOk

def _auto_bindOk(widget):
    widget.setChecked(STAT.task_mode == linuxcnc.MODE_AUTO)
    STATUS.task_state.onValueChanged(lambda: _mode_ok(widget))
    STATUS.interp_state.onValueChanged(lambda: _mode_ok(widget))
    STATUS.task_mode.onValueChanged(lambda m: widget.setChecked(m == linuxcnc.MODE_AUTO))

mode.auto.ok = _mode_ok
mode.auto.bindOk = _auto_bindOk

def _mdi_bindOk(widget):
    widget.setChecked(STAT.task_mode == linuxcnc.MODE_MDI)
    STATUS.task_state.onValueChanged(lambda: _mode_ok(widget))
    STATUS.interp_state.onValueChanged(lambda: _mode_ok(widget))
    STATUS.task_mode.onValueChanged(lambda m: widget.setChecked(m == linuxcnc.MODE_MDI))

mode.mdi.ok = _mode_ok
mode.mdi.bindOk = _mdi_bindOk

# -------------------------------------------------------------------------
# HOME actions
# -------------------------------------------------------------------------
class home:
    """Homing actions group"""
    @staticmethod
    def all():
        """Homes all axes."""
        LOG.info("Homing all axes")
        _home_joint(-1)

    @staticmethod
    def axis(axis):
        """Home a specific axis.

        Args:
            axis (int | str) : Either the axis letter or number to home.
        """
        axis = getAxisLetter(axis)
        if axis.lower() == 'all':
            home.all()
            return
        jnum = INFO.COORDINATES.index(axis)
        LOG.info('Homing Axis: {}'.format(axis.upper()))
        _home_joint(jnum)

    @staticmethod
    def joint(jnum):
        """Home a specific joint.

        Args:
            jnum (int) : The number of the joint to home.
        """
        LOG.info("Homing joint: {}".format(jnum))
        _home_joint(jnum)

def _home_ok(jnum=-1, widget=None):
    # TODO: Check if homing a specific joint is OK
    if power.is_on(): # and not STAT.homed[jnum]:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be on to home"

    _home_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _home_all_bindOk(widget):
    STATUS.on.connect(lambda: _home_ok(widget=widget))
    STATUS.homed.onValueChanged(lambda: _home_ok(widget=widget))

home.all.ok = _home_ok
home.all.bindOk = _home_all_bindOk

def _home_joint_bindOk(jnum, widget):
    STATUS.on.connect(lambda: _home_ok(jnum, widget=widget))
    STATUS.homed.onValueChanged(lambda: _home_ok(jnum, widget=widget))

home.joint.ok = _home_ok
home.joint.bindOk = _home_joint_bindOk

def _home_axis_bindOk(axis, widget):
    aletter = getAxisLetter(axis)
    if aletter not in INFO.AXIS_LETTER_LIST:
        msg = 'Machine has no {} axis'.format(aletter.upper())
        widget.setEnabled(False)
        widget.setToolTip(msg)
        widget.setStatusTip(msg)
        return

    jnum = INFO.AXIS_LETTER_LIST.index(axis)
    STATUS.on.connect(lambda: _home_ok(jnum, widget=widget))

home.axis.ok = _home_ok
home.axis.bindOk = _home_axis_bindOk


class unhome:
    """Unhoming actions group"""
    @staticmethod
    def all():
        pass

    @staticmethod
    def axis(axis):
        pass

    @staticmethod
    def joint(jnum):
        pass

def _home_joint(jnum):
    setTaskMode(linuxcnc.MODE_MANUAL)
    CMD.teleop_enable(False)
    CMD.home(jnum)

def _unhome_joint(jnum):
    setTaskMode(linuxcnc.MODE_MANUAL)
    CMD.teleop_enable(False)
    CMD.home(jnum)

# Homing helper functions

def getAxisLetter(axis):
    """Takes an axis letter or number and returns the axis letter.

    Args:
        axis (int | str) : Either a axis letter or an axis number.

    Returns:
        str : The axis letter, `all` for an input of -1.
    """
    if isinstance(axis, int):
        return ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w', 'all'][axis]
    return axis.lower()

def getAxisNumber(axis):
    """Takes an axis letter or number and returns the axis number.

    Args:
        axis (int | str) : Either a axis letter or an axis number.

    Returns:
        int : The axis number, -1 for an input of `all`.
    """
    if isinstance(axis, str):
        return ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w', 'all'].index(axis.lower())
    return axis


# -------------------------------------------------------------------------
# OVERRIDE LIMITS action
# -------------------------------------------------------------------------
def override_limits():
    LOG.info("Setting override limits")
    CMD.override_limits()

def _override_limits_ok(widget=None):
    ok = False
    for anum in INFO.AXIS_NUMBER_LIST:
        if STAT.limit[anum] != 0:
            aletter = 'XYZABCUVW'.index(anum)
            ok = True
            msg = "Axis {} on limit".format(aletter)

    if not ok:
        msg = "Axis must be on limit to override"

    _override_limits_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _override_limits_bindOk(widget):
    STATUS.limit.onValueChanged(lambda: _override_limits_ok(widget))

override_limits.ok = _override_limits_ok
override_limits.bindOk = _override_limits_bindOk

# -------------------------------------------------------------------------
# JOG actions
# -------------------------------------------------------------------------

class jog:

    max_linear_speed = INFO.getMaxJogVelocity()

    linear_speed = INFO.getJogVelocity()
    angular_speed = INFO.getJogVelocity()
    continuous = False
    increment = INFO.getIncrements()[0]

    @staticmethod
    def axis(axis, direction=0, speed=None, distance=None):
        """Jog an axis.

        Args:
            axis (str | int) : Either the letter or number of the axis to jog.
                direction (str | int) : pos or +1 for positive, neg or -1 for negative.
            speed (float, optional) : Desired jog vel in machine_units/s.
                distance (float, optional) : Desired jog distance, continuous jog if 0.00.
        """

        if isinstance(direction, str):
            direction = {'neg': -1, 'pos': 1}.get(direction.lower(), 0)

        axis = getAxisNumber(axis)

        # must be in teleoperating mode to jog.
        # ToDo: probably need to do some checks to make sure it is OK to jog
        if STAT.motion_mode != linuxcnc.TRAJ_MODE_TELEOP:
            CMD.teleop_enable(1)

        if speed == 0 or direction == 0:
            CMD.jog(linuxcnc.JOG_STOP, 0, axis)

        else:

            if speed is None:
                if axis in (3, 4, 5):
                    speed = jog.angular_speed / 60
                else:
                    speed = jog.linear_speed / 60

            if distance is None:
                distance = jog.increment

            velocity = float(speed) * direction

            if distance == 0:
                CMD.jog(linuxcnc.JOG_CONTINUOUS, 0, axis, velocity)
            else:
                CMD.jog(linuxcnc.JOG_INCREMENT, 0, axis, velocity, distance)

    @staticmethod
    def set_jog_continuous(continuous):
        if continuous:
            LOG.debug("Setting jog mode to continuous")
        else:
            LOG.debug("Setting jog mode to incremental")
        jog.continuous = continuous

    @staticmethod
    def set_increment(raw_increment):
        jog.increment = _parse_jog_increment(raw_increment)

    @staticmethod
    def set_linear_speed(speed):
        jog.linear_speed = float(speed)

    @staticmethod
    def set_angular_speed(speed):
        jog.angular_speed = float(speed)


    @staticmethod
    def set_linear_speed_percentage(percentage):
        jog.set_linear_speed(jog.max_linear_speed * (float(percentage) / 100))


def _jog_speed_slider_bindOk(widget):

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(0)
        widget.setMaximum(100)
        widget.setValue((jog.linear_speed / jog.max_linear_speed) * 100)

        # jog.linear_speed.connect(lambda v: widget.setValue(v * 100))
    except AttributeError:
        pass

jog.set_linear_speed.ok = jog.set_angular_speed.ok = lambda *a, **k: True
jog.set_linear_speed.bindOk = jog.set_angular_speed.bindOk = lambda *a, **k: True

jog.set_linear_speed_percentage.ok = lambda *a, **k: True
jog.set_linear_speed_percentage.bindOk = _jog_speed_slider_bindOk


def _from_internal_linear_unit(v, unit=None):
    if unit is None:
        unit = STAT.linear_units
    lu = (unit or 1) * 25.4
    return v * lu

def _parse_jog_increment(jogincr):
    scale = 1
    if isinstance(jogincr, basestring):
        jogincr = jogincr.lower()
        if jogincr.endswith("mm"):
            scale = _from_internal_linear_unit(1 / 25.4)
        elif jogincr.endswith("cm"):
            scale = _from_internal_linear_unit(10 / 25.4)
        elif jogincr.endswith("um"):
            scale = _from_internal_linear_unit(.001 / 25.4)
        elif jogincr.endswith("in") or jogincr.endswith("inch") or jogincr.endswith('"'):
            scale = _from_internal_linear_unit(1.)
        elif jogincr.endswith("mil"):
            scale = _from_internal_linear_unit(.001)
        else:
            scale = 1
        jogincr = jogincr.rstrip(" inchmuil")
        try:
            if "/" in jogincr:
                p, q = jogincr.split("/")
                jogincr = float(p) / float(q)
            else:
                jogincr = float(jogincr)
        except ValueError:
            jogincr = 0
    return jogincr * scale


def _jog_axis_ok(axis, direction=0, widget=None):
    axisnum = getAxisNumber(axis)
    if STAT.task_state == linuxcnc.STATE_ON \
        and STAT.interp_state == linuxcnc.INTERP_IDLE \
        and STAT.homed[axisnum] == 1 \
        and STAT.limit[axisnum] == 0:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be ON and in IDLE to jog"

    _jog_axis_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok


def _jog_axis_bindOk(axis, direction, widget):
    aletter = getAxisLetter(axis)
    if aletter not in INFO.AXIS_LETTER_LIST:
        msg = 'Machine has no {} axis'.format(aletter.upper())
        widget.setEnabled(False)
        widget.setToolTip(msg)
        widget.setStatusTip(msg)
        return

    STATUS.limit.onValueChanged(lambda: _jog_axis_ok(aletter, direction, widget))
    STATUS.homed.onValueChanged(lambda: _jog_axis_ok(aletter, direction, widget))
    STATUS.task_state.onValueChanged(lambda: _jog_axis_ok(aletter, direction, widget))
    STATUS.interp_state.onValueChanged(lambda: _jog_axis_ok(aletter, direction, widget))

jog.axis.ok = _jog_axis_ok
jog.axis.bindOk = _jog_axis_bindOk


class jog_mode:

    mode = 'continuous'

    @staticmethod
    def continuous():
        LOG.debug("Setting jog mode continuous")
        STATUS.setJogMode(True)

    @staticmethod
    def incremental():
        LOG.debug("Setting jog mode incremental")
        STATUS.setJogMode(False)

    @staticmethod
    def toggle():
        if STATUS.jog_mode == True:
            jog_mode.continuous()
        else:
            jog_mode.incremental()