import os
import linuxcnc
from PySide6.QtWidgets import QComboBox

from qtpyvcp.utilities.settings import setting

# Set up logging
from qtpyvcp.utilities import logger
from abc import abstractstaticmethod
LOG = logger.getLogger(__name__)

from qtpyvcp.actions.base_actions import setTaskMode
from qtpyvcp.plugins import getPlugin
IN_DESIGNER = os.getenv('DESIGNER', False)
if not IN_DESIGNER:
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
        """Set E-Stop active

        ActionButton syntax::

            machine.estop.activate
        """
        LOG.debug("Setting state red<ESTOP>")
        CMD.state(linuxcnc.STATE_ESTOP)

    @staticmethod
    def reset():
        """Resets E-Stop

        ActionButton syntax::

            machine.estop.reset
        """
        LOG.debug("Setting state green<ESTOP_RESET>")
        CMD.state(linuxcnc.STATE_ESTOP_RESET)

    @staticmethod
    def toggle():
        """Toggles E-Stop state

        ActionButton syntax::

            machine.estop.toggle
        """

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
        """Turns machine power On

        ActionButton syntax::

            machine.power.on
        """
        LOG.debug("Setting state green<ON>")
        CMD.state(linuxcnc.STATE_ON)

    @staticmethod
    def off():
        """Turns machine power Off

        ActionButton syntax::

            machine.power.off
        """
        LOG.debug("Setting state red<OFF>")
        CMD.state(linuxcnc.STATE_OFF)

    @staticmethod
    def toggle():
        """Toggles machine power On/Off

        ActionButton syntax::

            machine.power.toggle
        """
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
    STATUS.on.notify(lambda v: widget.setChecked(v))

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

if not IN_DESIGNER:
    STATUS.interp_state.onValueChanged(_resetMode)

def issue_mdi(command, reset=True):
    """Issue an MDI command.

        An MDI command can be issued any time the machine is homed (if not
        NO_FORCE_HOMING in the INI) and the interpreter is IDLE.  The task
        mode will automatically be switched to MDI prior to issuing the command
        and will be returned to the previous mode when the interpreter becomes IDLE.

        ActionButton syntax to issue G0 X5:
        ::

            machine.issue_mdi:G0X5

        It is simpler to use the MDIButton, examples in the Widgets section.

    Args:
        command (str) : A valid RS274 gcode command string. Multiple MDI commands
            can be separated with a ``;`` and will be issued sequentially.
        reset (bool, optional): Whether to reset the Task Mode to the state
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
        # issue multiple MDI commands separated by ';'
        for cmd in command.strip().split(';'):
            LOG.info("Issuing MDI command: %s", cmd)
            CMD.mdi(cmd)
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
    _issue_mdi_ok(mdi_cmd=mdi_cmd, widget=widget)
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
        widget.setCurrentText(STATUS.g5x_index.getString())
        STATUS.g5x_index.notify(lambda g5x: widget.setCurrentText(g5x), 'string')
    else:
        widget.setCheckable(True)
        widget.setChecked(STATUS.g5x_index.getString() == coord)
        STATUS.g5x_index.notify(lambda g5x: widget.setChecked(g5x == coord), 'string')

set_work_coord.ok = _issue_mdi_ok
set_work_coord.bindOk = _set_work_coord_bindOk

# -------------------------------------------------------------------------
# FEED HOLD action
# -------------------------------------------------------------------------
class feedhold:
    """Feed Hold action Group"""

    # FIXME: Not sure what feedhold does, or how to turn it ON/OFF, if it even can be.

    @staticmethod
    def enable():
        """Enables Feed Hold"""
        LOG.info("Setting feedhold ENABLED")
        CMD.set_feed_hold(1)

    @staticmethod
    def disable():
        """Disables Feed Hold"""
        LOG.info("Setting feedhold DISABLED")
        CMD.set_feed_hold(0)

    @staticmethod
    def toggle():
        """Toggles Feed Hold state"""
        if STAT.feed_hold_enabled:
            feedhold.disable()
        else:
            feedhold.enable()

def _feed_hold_ok(widget=None):
    return STAT.task_state == linuxcnc.STATE_ON and STAT.interp_state == linuxcnc.INTERP_IDLE

def _feed_hold_bindOk(widget):
    widget.setEnabled(STAT.task_state == linuxcnc.STATE_ON)
    widget.setChecked(STAT.feed_hold_enabled)
    STATUS.task_state.notify(lambda s: widget.setEnabled(s == linuxcnc.STATE_ON))
    STATUS.feed_hold_enabled.notify(widget.setChecked)

feedhold.enable.ok = feedhold.disable.ok = feedhold.toggle.ok = _feed_hold_ok
feedhold.enable.bindOk = feedhold.disable.bindOk = feedhold.toggle.bindOk = _feed_hold_bindOk

# -------------------------------------------------------------------------
# FEED OVERRIDE actions
# -------------------------------------------------------------------------

class feed_override:
    """Feed Override Group"""
    @staticmethod
    def enable():
        """Feed Override Enable"""
        CMD.set_feed_override(True)

    @staticmethod
    def disable():
        """Feed Override Disable"""
        CMD.set_feed_override(False)

    @staticmethod
    def toggle_enable():
        """Feed Override Enable Toggle"""
        if STAT.feed_override_enabled:
            feed_override.disable()
        else:
            feed_override.enable()

    @staticmethod
    def set(value):
        """Feed Override Set Value"""
        CMD.feedrate(float(value) / 100)

    @staticmethod
    def reset():
        """Feed Override Reset"""
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
        widget.setMaximum(int(INFO.maxFeedOverride() * 100))

        try:
            widget.setSliderPosition(100)
            STATUS.feedrate.onValueChanged(
                lambda v: widget.setSliderPosition(int(v * 100)))

        except AttributeError:
            widget.setValue(100)
            STATUS.feedrate.onValueChanged(
                lambda v: widget.setValue(int(v * 100)))

        feed_override.set(100)

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
    """Rapid Override Group"""
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

        try:
            widget.setSliderPosition(100)
            STATUS.rapidrate.onValueChanged(
                lambda v: widget.setSliderPosition(int(v * 100)))

        except AttributeError:
            STATUS.rapidrate.onValueChanged(
                lambda v: widget.setValue(v * 100))
            widget.setValue(100)

        rapid_override.set(100)

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
    """Max Velocity Group"""
    @staticmethod
    def set(value):
        """Max Velocity Override Set Value"""
        CMD.maxvel(float(value) / 60)

    @staticmethod
    def reset():
        """Max Velocity Override Reset Value"""
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
        widget.setMaximum(int(INFO.maxVelocity()))

        try:
            widget.setSliderPosition(int(INFO.maxVelocity()))
            STATUS.max_velocity.onValueChanged(
                lambda v: widget.setSliderPosition(int(v * 60)))

        except AttributeError:
            widget.setValue(INFO.maxVelocity())
            STATUS.max_velocity.onValueChanged(
                lambda v: widget.setValue(v * 60))

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
    """Mode action group"""
    @staticmethod
    def manual():
        """Change mode to Manual

        ActionButton syntax:
        ::

            machine.mode.manual

        """
        setTaskMode(linuxcnc.MODE_MANUAL)

    @staticmethod
    def auto():
        """Change mode to Auto

        ActionButton syntax:
        ::

            machine.mode.auto

        """
        setTaskMode(linuxcnc.MODE_AUTO)

    @staticmethod
    def mdi():
        """Change mode to MDI

        ActionButton syntax:
        ::

            machine.mode.mdi

        """
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
        """Homes all axes

        ActionButton syntax::

            machine.home.all
        """
        LOG.info("Homing all axes")
        _home_joint(-1)

    @staticmethod
    def axis(axis):
        """Home a specific axis

        Args:
            axis (int | str) : one of (xyzabcuvw or 012345678)

        ActionButton syntax to home the X axis::

            machine.home.axis:x
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
        """Home a specific joint

        Args:
            jnum (int) : one of (012345678)

        ActionButton syntax to home joint 0::

            machine.home.joint:0
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
    STATUS.on.notify(lambda: _home_ok(widget=widget))
    STATUS.homed.notify(lambda: _home_ok(widget=widget))

home.all.ok = _home_ok
home.all.bindOk = _home_all_bindOk

def _home_joint_bindOk(jnum, widget):
    STATUS.on.notify(lambda: _home_ok(jnum, widget=widget))
    STATUS.homed.notify(lambda: _home_ok(jnum, widget=widget))

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
    STATUS.on.notify(lambda: _home_ok(jnum, widget=widget))

home.axis.ok = _home_ok
home.axis.bindOk = _home_axis_bindOk


class unhome:
    """Unhoming actions group"""
    @staticmethod
    def all():
        """Unhome all the axes

        ActionButton syntax::

            machine.unhome.all
        """
        LOG.info("Unhoming all Axes")
        _unhome_joint(-1)

    @staticmethod
    def axis(axis):
        """Unhome a specific axis

        Args:
            axis (int | str) : one of (xyzabcuvw or 012345678)

        ActionButton syntax to unhome the X axis::

            machine.unhome.axis:x
        """
        axis = getAxisLetter(axis)
        if axis.lower() == 'all': # not sure what this is copied from home
            unhome.all()
            return
        #jnum = INFO.COORDINATES.index(axis)
        for ax in INFO.ALETTER_JNUM_DICT:
            #LOG.info('Unhoming Axis: {}'.format(axis.upper()))
            if axis == ax[0]:
                LOG.info('Unhoming Axis: {}'.format(ax.upper()))
                _unhome_joint(INFO.ALETTER_JNUM_DICT[ax])

    @staticmethod
    def joint(jnum):
        """Unhome a specific joint

        Args:
            jnum (int) : The number of the joint to home.

        ActionButton syntax to unhome the joint 0::

            machine.unhome.joint:0
        """
        LOG.info("Unhoming joint: {}".format(jnum))
        _unhome_joint(jnum)

def _home_joint(jnum):
    setTaskMode(linuxcnc.MODE_MANUAL)
    CMD.teleop_enable(False)
    CMD.home(jnum)

def _unhome_joint(jnum):
    setTaskMode(linuxcnc.MODE_MANUAL)
    CMD.teleop_enable(False)
    CMD.unhome(jnum)

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
    mgs = None
    for anum in INFO.AXIS_NUMBER_LIST:
        if STAT.limit[anum] != 0:
            aaxis = getAxisLetter(anum)
            aletter = INFO.COORDINATES.index(aaxis)
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

DEFAULT_JOG_SPEED = INFO.getJogVelocity()
MAX_JOG_SPEED = INFO.getMaxJogVelocity()
DEFAULT_JOG_ANGULAR_SPEED = INFO.getJogAngularVelocity()
MAX_JOG_ANGULAR_SPEED = INFO.getMaxJogAngularVelocity()

@setting('machine.jog.linear-speed',
         default_value=DEFAULT_JOG_SPEED,
         min_value=0,
         max_value=MAX_JOG_SPEED,
         persistent=True)
def jog_linear_speed(obj):
    return obj.value

@jog_linear_speed.setter
def jog_linear_speed(obj, value):

    obj.value = obj.clampValue(value)
    jog_linear_speed.signal.emit(obj.value)
    LOG.debug("Setting jog linear speed: %4.1f", obj.value)

    percentage = int(obj.value * 100 / MAX_JOG_SPEED)
    jog_linear_speed_percentage.value = percentage
    jog_linear_speed_percentage.signal.emit(percentage)


@setting('machine.jog.linear-speed-percentage',
         default_value=int(DEFAULT_JOG_SPEED * 100 / MAX_JOG_SPEED),
         min_value=0,
         max_value=100,
         persistent=False)
def jog_linear_speed_percentage(obj):
    return obj.value

@jog_linear_speed_percentage.setter
def jog_linear_speed_percentage(obj, percentage):
    LOG.debug("Setting jog linear speed percentage: %d", percentage)
    jog_linear_speed.setValue(float(MAX_JOG_SPEED * percentage / 100))


@setting('machine.jog.angular-speed',
         default_value=DEFAULT_JOG_ANGULAR_SPEED,
         min_value=0,
         max_value=MAX_JOG_ANGULAR_SPEED,
         persistent=True)
def jog_angular_speed(obj):
    return obj.value

@jog_angular_speed.setter
def jog_angular_speed(obj, value):
    obj.value = obj.clampValue(value)
    jog_angular_speed.signal.emit(obj.value)
    LOG.debug("Setting Jog Angular Speed: %d", value)

    percentage = int(obj.value * 100 / MAX_JOG_ANGULAR_SPEED)
    jog_angular_speed_percentage.value = percentage
    jog_angular_speed_percentage.signal.emit(percentage)

@setting('machine.jog.angular-speed-percentage',
         default_value=int(DEFAULT_JOG_ANGULAR_SPEED * 100 / MAX_JOG_ANGULAR_SPEED),
         min_value=0,
         max_value=100,
         persistent=False)
def jog_angular_speed_percentage(obj):
    return obj.value

@jog_angular_speed_percentage.setter
def jog_angular_speed_percentage(obj, percentage):
    LOG.debug("Setting jog angular speed percentage: %d", percentage)
    jog_angular_speed.setValue(float(MAX_JOG_ANGULAR_SPEED * percentage / 100))


@setting('machine.jog.mode-incremental', default_value=True)
def jog_mode_incremental(obj):
    return obj.value

@jog_mode_incremental.setter
def jog_mode_incremental(obj, value):
    LOG.debug("Setting jog mode incremental: %s", value)
    obj.value = value


def fromInternalLinearUnits(v, unit=None):
    if unit is None:
        unit = STAT.linear_units
    lu = (unit or 1) * 25.4
    return v * lu

def parseJogIncrement(jogincr):
    scale = 1
    if isinstance(jogincr, str):
        jogincr = jogincr.lower()
        if jogincr.endswith("mm"):
            scale = fromInternalLinearUnits(1 / 25.4)
        elif jogincr.endswith("cm"):
            scale = fromInternalLinearUnits(10 / 25.4)
        elif jogincr.endswith("um"):
            scale = fromInternalLinearUnits(.001 / 25.4)
        elif jogincr.endswith("in") or jogincr.endswith("inch") or jogincr.endswith('"'):
            scale = fromInternalLinearUnits(1.)
        elif jogincr.endswith("mil"):
            scale = fromInternalLinearUnits(.001)
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

@setting('machine.jog.increment', parseJogIncrement(INFO.getIncrements()[0]))
def jog_increment(obj):
    """Linear jog increment.

    Args:
        jogincr (str, int, float) : The desired jog increment. Can be passed
            as a string including an optional units specifier. Valid unit
            specifiers include ``mm``, ``cm``, ``um``, ``in``, ``inch``, ``"``,
            and ``mil``.
    """
    return obj.value

@jog_increment.setter
def jog_increment(obj, jogincr):
    value = parseJogIncrement(jogincr)
    LOG.debug('Setting jog increment: %s (%2.4f)', jogincr, value)
    obj.value = value
    obj.signal.emit(value)


class jog:
    """Jog Actions Group"""

    max_linear_speed = INFO.getMaxJogVelocity()
    max_angular_speed = INFO.getMaxJogAngularVelocity()
    angular_speed = INFO.getJogAngularVelocity()
    continuous = False
    increment = INFO.getIncrements()[0]

    @staticmethod
    def axis(axis, direction=0, speed=None, distance=None):
        """Jog an axis.

        Action Button Syntax to jog the X axis in the positive direction::

            machine.jog.axis:x,pos

        Args:
            axis (str | int) : Either the letter or number of the axis to jog.
            direction (str | int) : pos or +1 for positive, neg or -1 for negative.
            speed (float, optional) : Desired jog vel in machine_units/s.
            distance (float, optional) : Desired jog distance, continuous if 0.00.
        """

        # check if it even makes sense to try to jog
        if STAT.task_state != linuxcnc.STATE_ON or STAT.task_mode != linuxcnc.MODE_MANUAL:
            return

        if isinstance(direction, str):
            direction = {'neg': -1, 'pos': 1}.get(direction.lower(), 0)

        axis = getAxisNumber(axis)

        # must be in teleoperating mode to jog.
        if STAT.motion_mode != linuxcnc.TRAJ_MODE_TELEOP:
            CMD.teleop_enable(1)

        if speed == 0 or direction == 0:
            CMD.jog(linuxcnc.JOG_STOP, 0, axis)

        else:

            if speed is None:
                if axis in (3, 4, 5):
                    speed = jog_angular_speed.value / 60.0
                else:
                    speed = jog_linear_speed.value / 60.0

            if distance is None:
                if jog_mode_incremental.value:
                    distance = jog_increment.value
                else:
                    distance = 0

            velocity = float(speed) * direction

            if distance == 0:
                CMD.jog(linuxcnc.JOG_CONTINUOUS, 0, axis, velocity)
            else:
                CMD.jog(linuxcnc.JOG_INCREMENT, 0, axis, velocity, distance)

    @staticmethod
    def set_jog_continuous(continuous):
        """Set Jog Continuous"""
        if continuous:
            LOG.debug("Setting jog mode to continuous")
        else:
            LOG.debug("Setting jog mode to incremental")
        jog.jog_mode_incremental = continuous

    @staticmethod
    def set_increment(raw_increment):
        """Set Jog Increment"""
        jog_increment.setValue(raw_increment)

    @staticmethod
    def set_linear_speed(speed):
        """Set Jog Linear Speed

        ActionSlider syntax::

            machine.jog.set-linear-speed
        """
        jog_linear_speed.setValue(float(speed))

    @staticmethod
    def set_angular_speed(speed):
        """Set Jog Angular Speed"""
        jog_angular_speed.setValue(float(speed))

    @staticmethod
    def set_linear_speed_percentage(percentage):
        """Set Jog Linear Speed Percentage"""
        jog_linear_speed_percentage.setValue(percentage)

    @staticmethod
    def set_angular_speed_percentage(percentage):
        """Set Jog Angular Speed Percentage"""
        jog_angular_speed_percentage.setValue(percentage)

def _jog_speed_slider_bindOk(widget):

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(0)
        widget.setMaximum(100)
        widget.setValue((jog.linear_speed.getValue() / jog.max_linear_speed) * 100)

        # jog.linear_speed.connect(lambda v: widget.setValue(v * 100))
    except AttributeError:
        pass

def _jog_angular_speed_slider_bindOk(widget):

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(0)
        widget.setMaximum(100)
        widget.setValue((jog.angular_speed.getValue() / jog.max_angular_speed) * 100)

        # jog.linear_speed.connect(lambda v: widget.setValue(v * 100))
    except AttributeError:
        pass


jog.set_linear_speed.ok = jog.set_angular_speed.ok = lambda *a, **k: True
jog.set_linear_speed.bindOk = jog.set_angular_speed.bindOk = lambda *a, **k: True

jog.set_linear_speed_percentage.ok = lambda *a, **k: True
jog.set_linear_speed_percentage.bindOk = _jog_speed_slider_bindOk

jog.set_angular_speed_percentage.ok = lambda *a, **k: True
jog.set_angular_speed_percentage.bindOk = _jog_angular_speed_slider_bindOk


def _jog_axis_ok(axis, direction=0, widget=None):
    axisnum = getAxisNumber(axis)
    jnum = INFO.COORDINATES.index(axis)
    if STAT.task_state == linuxcnc.STATE_ON \
            and STAT.interp_state == linuxcnc.INTERP_IDLE \
            and (STAT.limit[axisnum] == 0 or STAT.joint[jnum]['override_limits']):
        # and STAT.homed[axisnum] == 1 \
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
    """Jog Mode Group"""

    @staticmethod
    def continuous():
        """Set Jog Continuous

        ActionButton syntax::

            machine.jog-mode.continuous
        """
        jog_mode_incremental.setValue(False)


    @staticmethod
    def incremental():
        """Set Jog Incremental

        ActionButton syntax::

            machine.jog-mode.incremental
        """
        jog_mode_incremental.setValue(True)

    @staticmethod
    def toggle():
        """Jog Mode Toggle

        ActionButton syntax::

            machine.jog-mode.toggle
        """
        jog_mode_incremental.setValue(not jog_mode_incremental.value)

jog_mode.incremental.ok = jog_mode.continuous.ok = lambda *a, **kw: True
jog_mode.incremental.bindOk = jog_mode.continuous.bindOk = lambda *a, **kw: True
