#!/usr/bin/env python
# coding: utf-8

import linuxcnc

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')
STAT = STATUS.stat
INFO = Info()

SPINDLES = range(INFO.spindles())
DEFAULT_SPEED = INFO.defaultSpindleSpeed()

CMD = linuxcnc.command()

from qtpyvcp.actions.base_actions import setTaskMode


def _spindle_exists(spindle):
    if spindle in SPINDLES:
        return True
    return False

def _spindle_ok(speed=None, spindle=0, widget=None):
    if spindle not in SPINDLES:
            ok = False
            msg = "No spindle No. {}".format(spindle)
    elif STAT.task_state != linuxcnc.STATE_ON:
        ok = False
        msg = "Power must be ON"
    elif STAT.task_mode == linuxcnc.MODE_AUTO:
        ok = False
        msg = "Mode must be MAN or MDI"
    else:
        ok = True
        msg = ""

    _spindle_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _spindle_bindOk(speed=None, spindle=0, widget=None):
    if not _spindle_exists(spindle):
        return
    STATUS.on.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.task_mode.onValueChanged(lambda: _spindle_ok(spindle=spindle, widget=widget))


def forward(speed=None, spindle=0):
    """Turn a spindle ON in the *FORWARD* direction.

    Args:
        speed (float, optional) : The requested speed to spin the spindle at.
            If ``speed`` is not specified the current interpreter speed setting
            (as set by the last S word) is used, taking into account the
            value of the spindle override if it is enabled.
        spindle (int, optional) : The number of the spindle to turn ON. If
            ``spindle`` is not specified spindle 0 is assumed.
    """
    if speed is None:
        speed = getSpeed()
    CMD.spindle(linuxcnc.SPINDLE_FORWARD, speed, spindle)

def _spindle_forward_bindOk(speed=None, spindle=0, widget=None):
    if not _spindle_exists(spindle):
        return
    widget.setCheckable(True)
    STATUS.on.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.task_mode.onValueChanged(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.spindle[spindle].direction.onValueChanged(lambda d: widget.setChecked(d == 1))

forward.ok = _spindle_ok
forward.bindOk = _spindle_forward_bindOk


def reverse(speed=None, spindle=0):
    """Turn a spindle ON in the *REVERSE* direction.

    Args:
        speed (float, optional) : The requested speed to spin the spindle at.
            If ``speed`` is not specified the current interpreter speed setting
            (as set by the last S word) is used, taking into account the
            value of the spindle override if it is enabled.
        spindle (int, optional) : The number of the spindle to turn ON. If
            ``spindle`` is not specified spindle 0 is assumed.
    """
    if speed is None:
        speed = getSpeed()
    CMD.spindle(linuxcnc.SPINDLE_REVERSE, speed, spindle)

def _spindle_reverse_bindOk(speed=None, spindle=0, widget=None):
    if not _spindle_exists(spindle):
        return
    widget.setCheckable(True)
    STATUS.on.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.task_mode.onValueChanged(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.spindle[spindle].direction.onValueChanged(lambda d: widget.setChecked(d == -1))

reverse.ok = _spindle_ok
reverse.bindOk = _spindle_reverse_bindOk


def off(spindle=0):
    """Turn a spindle OFF.

    Args:
        spindle (int, optional) : The number of the spindle to turn OFF. If
            ``spindle`` is not specified spindle 0 is assumed.
    """
    CMD.spindle(linuxcnc.SPINDLE_OFF, spindle)

off.ok = _spindle_ok
off.bindOk = _spindle_bindOk


def faster(spindle=0):
    """Increase spindle speed by 100rpm.

    Args:
        spindle (int, optional) : The number of the spindle to increase the
            speed of. If ``spindle`` is not specified spindle 0 is assumed.
    """
    CMD.spindle(linuxcnc.SPINDLE_INCREASE)

faster.ok = _spindle_ok
faster.bindOk = _spindle_bindOk


def slower(spindle=0):
    """Decrease spindle speed by 100rpm.

    Args:
        spindle (int, optional) : The number of the spindle to decrease the
            speed of. If ``spindle`` is not specified spindle 0 is assumed.
    """
    CMD.spindle(linuxcnc.SPINDLE_DECREASE)

slower.ok = _spindle_ok
slower.bindOk = _spindle_bindOk


# Spindle CONSTANT
def constant(spindle=0):
    """Unclear"""
    CMD.spindle(linuxcnc.SPINDLE_CONSTANT)

constant.ok = _spindle_ok
constant.bindOk = _spindle_bindOk


def getSpeed(spindle=0):
    """Gets the interpreter's speed setting for the specified spindle.

    Args:
        spindle (int, optional) : The number of the spindle to get the speed
            of. If ``spindle`` is not specified spindle 0 is assumed.

    Returns:
        float: The interpreter speed setting, with any override applied if
        override enabled.
    """
    raw_speed = STAT.settings[2]
    if raw_speed == 0:
        raw_speed = abs(DEFAULT_SPEED)

    if STAT.spindle[spindle]['override_enabled']:
        return raw_speed * STAT.spindle[spindle]['override']

    return raw_speed

#==============================================================================
# Spindle Override
#==============================================================================

def override(override, spindle=0):
    """Set spindle override percentage.

    Args:
        override (int) : The desired spindle override in percent.
        spindle (int, optional) : The number of the spindle to apply the
            override to. If ``spindle`` is not specified spindle 0 is assumed.
    """
    CMD.spindleoverride(float(override) / 100, spindle)

def _or_reset(spindle=0):
    CMD.spindleoverride(1.0, spindle)

def _or_enable(spindle=0):
    CMD.set_spindle_override(1, spindle)

def _or_disable(spindle=0):
    CMD.set_spindle_override(0, spindle)

def _or_toggle_enable(spindle=0):
    if STAT.spindle[spindle]['override_enabled']:
        override.disable()
    else:
        override.enable()

override.reset = _or_reset
override.enable = _or_enable
override.disable = _or_disable
override.toggle_enable = _or_toggle_enable

def _or_ok(value=100, spindle=0, widget=None):
    if spindle not in SPINDLES:
            ok = False
            msg = "No spindle No. {}".format(spindle)
    elif STAT.task_state != linuxcnc.STATE_ON:
        ok = False
        msg = "Machine must be ON"
    elif STAT.spindle[0]['override_enabled'] != 1:
        ok = False
        msg = "Override not enabled"
    else:
        ok = True
        msg = ""

    _or_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _or_bindOk(value=100, spindle=0, widget=None):
    if not _spindle_exists(spindle):
        return

    # This will work for any widget
    STATUS.task_state.onValueChanged(lambda: _or_ok(widget=widget))
    STATUS.spindle[spindle].override_enabled.onValueChanged(lambda: _or_ok(widget=widget))

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(INFO.minSpindleOverride() * 100)
        widget.setMaximum(INFO.maxSpindleOverride() * 100)
        widget.setValue(100)
        override(100)

        STATUS.spindle[spindle].override.onValueChanged(lambda v: widget.setValue(v * 100))
    except AttributeError:
        pass
    except:
        LOG.exception('Error in spindle.override bindOk')

override.ok = override.reset.ok = _or_ok
override.bindOk = override.reset.bindOk = _or_bindOk

def _or_enable_ok(spindle=0, widget=None):
    if spindle not in SPINDLES:
        ok = False
        msg = "No spindle No. {}".format(spindle)
    elif STAT.task_state != linuxcnc.STATE_ON:
        ok = False
        msg = "Machine must be ON"
    elif STAT.interp_state != linuxcnc.INTERP_IDLE:
        ok = False
        msg = "Machine must be IDLE"
    else:
        ok = True
        msg = ""

    _or_enable_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _or_enable_bindOk(spindle=0, widget=None):
    if not _spindle_exists(spindle):
        return

    STATUS.task_state.onValueChanged(lambda: _or_enable_ok(spindle, widget))
    STATUS.interp_state.onValueChanged(lambda: _or_enable_ok(spindle, widget))
    STATUS.spindle[spindle].override_enabled.onValueChanged(widget.setChecked)

override.enable.ok = override.disable.ok = override.toggle_enable.ok = _or_enable_ok
override.enable.bindOk = override.disable.bindOk = override.toggle_enable.bindOk = _or_enable_bindOk

#==============================================================================
# Spindle Brake
#==============================================================================

class brake:
    """Spindle brake actions class.
    """
    @staticmethod
    def on(spindle=0):
        """Set spindle brake ON.

        Args:
            spindle (int, optional) : The number of the spindle to apply the
                override to. If ``spindle`` is not specified spindle 0 is assumed.
        """
        CMD.brake(linuxcnc.BRAKE_ENGAGE, spindle)

    @staticmethod
    def off(spindle=0):
        """Set spindle brake OFF.

        Args:
            spindle (int, optional) : The number of the spindle to apply the
                override to. If ``spindle`` is not specified spindle 0 is assumed.
        """
        CMD.brake(linuxcnc.BRAKE_RELEASE, spindle)

    @staticmethod
    def toggle(spindle=0):
        """Toggle spindle brake ON/OFF.

        Args:
            spindle (int, optional) : The number of the spindle to apply the
                override to. If ``spindle`` is not specified spindle 0 is assumed.
        """
        if brake.is_on():
            brake.off()
        else:
            brake.on()

    @staticmethod
    def is_on(spindle=0):
        return STAT.spindle[spindle]['brake'] == linuxcnc.BRAKE_ENGAGE

def _brake_is_on(spindle=0):
    return STAT.spindle[spindle]['brake'] == linuxcnc.BRAKE_ENGAGE

def _brake_bind_ok(spindle=0, widget=None):
    if not _spindle_exists(spindle):
        return

    STATUS.on.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.task_mode.onValueChanged(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.spindle[spindle].brake.onValueChanged(widget.setChecked)

brake.on.ok = brake.off.ok = brake.toggle.ok = _spindle_ok
brake.on.bindOk = brake.off.bindOk = brake.toggle.bindOk = _brake_bind_ok
