#!/usr/bin/env python
# coding: utf-8

import linuxcnc

# Set up logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.utilities.info import Info
from QtPyVCP.utilities.status import Status
INFO = Info()
STATUS = Status()
STAT = STATUS.stat

CMD = linuxcnc.command()

from QtPyVCP.actions.base_actions import setTaskMode

def _spindle_ok(speed=None, spindle=0, widget=None):
    if STAT.task_state != linuxcnc.STATE_ON:
        ok = False
        msg = "Can't run spindle until machine it ON"
    elif STAT.task_mode == linuxcnc.MODE_AUTO:
        ok = False
        msg = "Machine must be in Manuel mode"
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
    STATUS.on.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.task_mode.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))


# Spindle FORWARD
def forward(speed=None, spindle=0):
    if speed is None:
        speed = getSpeed()
    CMD.spindle(linuxcnc.SPINDLE_FORWARD, speed, spindle)

def _spindle_forward_bindOk(speed=None, spindle=0, widget=None):
    widget.setCheckable(True)
    STATUS.on.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.task_mode.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.spindle[spindle].direction.connect(lambda d: widget.setChecked(d == 1))

forward.ok = _spindle_ok
forward.bindOk = _spindle_forward_bindOk


# Spindle REVERSE
def reverse(speed=None, spindle=0):
    if speed is None:
        speed = getSpeed()
    CMD.spindle(linuxcnc.SPINDLE_REVERSE, speed, spindle)

def _spindle_reverse_bindOk(speed=None, spindle=0, widget=None):
    widget.setCheckable(True)
    STATUS.on.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.task_mode.connect(lambda: _spindle_ok(spindle=spindle, widget=widget))
    STATUS.spindle[spindle].direction.connect(lambda d: widget.setChecked(d == -1))

reverse.ok = _spindle_ok
reverse.bindOk = _spindle_reverse_bindOk


# Spindle OFF
def off(spindle=0):
    CMD.spindle(linuxcnc.SPINDLE_OFF, spindle)

off.ok = _spindle_ok
off.bindOk = _spindle_bindOk


# Spindle FASTER
def faster(spindle=0):
    """Increase spindle speed by 100rpm"""
    CMD.spindle(linuxcnc.SPINDLE_INCREASE)

faster.ok = _spindle_ok
faster.bindOk = _spindle_bindOk


# Spindle SLOWER
def slower(spindle=0):
    """Decreases spindle speed by 100rpm"""
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
    raw_speed = STAT.settings[2]
    if raw_speed == 0:
        raw_speed = abs(INFO.defaultSpindleSpeed())

    if STAT.spindle[spindle]['override_enabled']:
        return raw_speed * STAT.spindle[spindle]['override']

    return raw_speed


class override:
    @staticmethod
    def enable(spindle=0):
        CMD.set_spindle_override(1, spindle)

    @staticmethod
    def disable(spindle=0):
        CMD.set_spindle_override(0, spindle)

    @staticmethod
    def toggle_enable(spindle=0):
        if STAT.spindle[spindle]['override_enabled']:
            override.disable()
        else:
            override.enable()

    @staticmethod
    def set(value, spindle=0):
        CMD.spindleoverride(float(value) / 100, spindle)

    @staticmethod
    def reset(spindle=0):
        CMD.spindleoverride(1.0, spindle)

def _enable_ok(spindle=0, widget=None):
    if STAT.task_state == linuxcnc.STATE_ON \
        and STAT.interp_state == linuxcnc.INTERP_IDLE:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be ON and IDLE to enable/disable spindle override"

    _spindle_override_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _enable_bindOk(spindle=0, widget=None):
    STATUS.task_state.connect(lambda: _enable_ok(widget))
    STATUS.interp_state.connect(lambda: _enable_ok(widget))
    STATUS.spindle[spindle].override_enabled.connect(widget.setChecked)

def _spindle_override_ok(value=100, spindle=0, widget=None):
    if STAT.task_state == linuxcnc.STATE_ON and STAT.spindle[0]['override_enabled'] == 1:
        ok = True
        msg = ""
    elif STAT.task_state != linuxcnc.STATE_ON:
        ok = False
        msg = "Machine must be ON to set spindle override"
    elif STAT.spindle[spindle]['override_enabled'] == 0:
        ok = False
        msg = "Spindle override is not enabled"
    else:
        ok = False
        msg = "Spindle override can not be changed"

    _spindle_override_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _spindle_override_bindOk(value=100, spindle=0, widget=None):

    # This will work for any widget
    STATUS.task_state.connect(lambda: _spindle_override_ok(widget=widget))
    STATUS.spindle[spindle].override_enabled.connect(lambda: _spindle_override_ok(widget=widget))

    try:
        # these will only work for QSlider or QSpinBox
        widget.setMinimum(INFO.minSpindleOverride() * 100)
        widget.setMaximum(INFO.maxSpindleOverride() * 100)
        widget.setValue(100)
        override.set(100)

        STATUS.spindle[spindle].override.connect(lambda v: widget.setValue(v * 100))
    except AttributeError:
        pass
    except:
        LOG.exception('Error in spindle.override bindOk')

override.set.ok = override.reset.ok = _spindle_override_ok
override.set.bindOk = override.reset.bindOk = _spindle_override_bindOk
override.enable.ok = override.disable.ok = override.toggle_enable.ok = _enable_ok
override.enable.bindOk = override.disable.bindOk = override.toggle_enable.bindOk = _enable_bindOk

class brake:
    @staticmethod
    def on():
        CMD.brake(linuxcnc.BRAKE_ENGAGE)

    @staticmethod
    def off():
        CMD.brake(linuxcnc.BRAKE_RELEASE)

    @staticmethod
    def toggle():
        if brake.it_on():
            brake.off()
        else:
            brake.on()

    @staticmethod
    def is_on():
        return STAT.spindle_brake == linuxcnc.BRAKE_ENGAGE
