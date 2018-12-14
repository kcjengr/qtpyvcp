#!/usr/bin/env python
# coding: utf-8

import linuxcnc

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')
STAT = STATUS.stat

CMD = linuxcnc.command()

#==============================================================================
# Coolent actions
#==============================================================================

class flood:
    @staticmethod
    def on():
        """Turns Flood coolant ON"""
        LOG.debug("Turning Flood coolant green<ON>")
        CMD.flood(linuxcnc.FLOOD_ON)

    @staticmethod
    def off():
        """Turns Flood coolant OFF"""
        LOG.debug("Turning Flood coolant red<OFF>")
        CMD.flood(linuxcnc.FLOOD_OFF)

    @staticmethod
    def toggle():
        """Toggles Flood coolant ON/OFF"""
        if STAT.flood == linuxcnc.FLOOD_ON:
            flood.off()
        else:
            flood.on()

class mist:
    @staticmethod
    def on():
        """Turns Mist coolant ON"""
        LOG.debug("Turning Mist coolant green<ON>")
        CMD.mist(linuxcnc.MIST_ON)

    @staticmethod
    def off():
        """Turns Mist coolant OFF"""
        LOG.debug("Turning Mist coolant red<OFF>")
        CMD.mist(linuxcnc.MIST_OFF)

    @staticmethod
    def toggle():
        """Toggles Mist coolant ON/OFF"""
        if STAT.mist == linuxcnc.MIST_ON:
            mist.off()
        else:
            mist.on()

def _coolant_ok(widget=None):
    """Checks if it is OK to turn coolant ON.

    Args:
        widget (QWidget, optional) : Widget to enable/disable according to result.

    Atributes:
        msg (string) : The reason the action is not permitted, or empty if permitted.

    Retuns:
        bool : True if OK, else False.
    """
    if STAT.task_state == linuxcnc.STATE_ON:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Can't turn on coolant when machine is not ON"

    _coolant_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _flood_bindOk(widget):
    _coolant_ok(widget)
    widget.setChecked(STAT.flood == linuxcnc.FLOOD_ON)
    STATUS.task_state.onValueChanged(lambda: _coolant_ok(widget))
    STATUS.flood.onValueChanged(lambda s: widget.setChecked(s == linuxcnc.FLOOD_ON))

def _mist_bindOk(widget):
    _coolant_ok(widget)
    widget.setChecked(STAT.mist == linuxcnc.MIST_ON)
    STATUS.task_state.onValueChanged(lambda: _coolant_ok(widget))
    STATUS.mist.onValueChanged(lambda s: widget.setChecked(s == linuxcnc.MIST_ON))

flood.on.ok = flood.off.ok = flood.toggle.ok = _coolant_ok
flood.on.bindOk = flood.off.bindOk = flood.toggle.bindOk = _flood_bindOk

mist.on.ok = mist.off.ok = mist.toggle.ok = _coolant_ok
mist.on.bindOk = mist.off.bindOk = mist.toggle.bindOk = _mist_bindOk
