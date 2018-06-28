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

# Description:
#   Collection of linuxcnc.command convenience functions.
#   Incomplete

import linuxcnc

# Set up logging
from QtPyVCP.utilities import logger
log = logger.getLogger(__name__)
# log.setLevel(logger.INFO) # One of DEBUG, INFO, WARNING, ERROR, CRITICAL

from QtPyVCP.utilities import ini_info

# from qtvcp.core import Status, Info
# INFO = Info()
# STATUS = Status()


class _Action(object):
    """docstring for _Action"""
    def __init__(self):
        super(_Action, self).__init__()

        self.cmd = linuxcnc.command()
        self.stat = linuxcnc.stat()

        self.coordinates = ini_info.get_coordinates()

        self.tmp = None

    def setEmergencyStop(self, state):
        if state:
            log.debug("Setting Estop red<ACTIVE>")
            self.cmd.state(linuxcnc.STATE_ESTOP)
        else:
            log.debug("Setting Estop green<RESET>")
            self.cmd.state(linuxcnc.STATE_ESTOP_RESET)

    def toggleEmergencyStop(self):
        self.stat.poll()
        state = not self.stat.estop
        self.setEmergencyStop(state)

    def setMachinePower(self, state):
        self.stat.poll()
        if self.stat.estop:
            log.warning("Can't set machine green<ON> until machine is out of red<Estop>")
            return
        if state:
            log.debug("Setting machine power green<ON>")
            self.cmd.state(linuxcnc.STATE_ON)
        else:
            log.debug("Setting machine power red<OFF>")
            self.cmd.state(linuxcnc.STATE_OFF)

    def toggleMachinePower(self):
        self.stat.poll()
        state = not self.stat.task_state == linuxcnc.STATE_ON
        self.setMachinePower(state)



    def homeJoint(self, jnum):
        if self.set_task_mode(linuxcnc.MODE_MANUAL):
            log.info('Homing Joint: {}'.format(jnum))
            self.cmd.teleop_enable(False)
            self.cmd.home(jnum)
        else:
            log.error("Can't home joint {}, machine must be ON and IDLE".fomrat(jnum))

    def homeAxis(self, axis_letter):
        jnum = self.coords.index(axis_letter.lower())
        self.homeJoint(jnum)

    def loadProgram(self, fname):
        self.set_task_mode(linuxcnc.MODE_AUTO)
        filter_prog = ini_info.get_filter_program(fname)
        if not filter_prog:
            self.cmd.program_open(fname)
        else:
            self.open_filter_program(fname, filter_prog)

    def runProgram(self, start_line=0):
        if self.set_task_mode(linuxcnc.MODE_AUTO):
            self.cmd.auto(linuxcnc.AUTO_RUN, start_line)

    def issueMDI(self, command):
        if self.set_task_mode(linuxcnc.MODE_MDI):
            self.cmd.mdi(command)
        else:
            log.error("Can't issue MDI, machine must be ON, HOMED and IDLE")


    #==========================================================================
    #  Helper functions
    #==========================================================================

    def set_task_mode(self, new_mode):
        """Sets task mode, if possible

        Args:
            new_mode (int): linuxcnc.MODE_MANUAL, MODE_MDI or MODE_AUTO

        Returns:
            bool: TRUE if successful
        """
        if self.is_running():
            log.error("Can't set mode while machine is running")
            return False
        else:
            self.cmd.mode(new_mode)
            self.cmd.wait_complete()
            return True

    def is_running(self):
        """Returns TRUE if machine is moving due to MDI, program execution, etc."""
        self.stat.poll()
        if self.stat.state == linuxcnc.RCS_EXEC:
            return True
        else:
            return self.stat.task_mode == linuxcnc.MODE_AUTO \
                and self.stat.interp_state != linuxcnc.INTERP_IDLE

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



class Action(object):
    """Ensures only one instance of StatusPoller exists per python interpretor.
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = _Action()
        return cls._instance











################################################################
# Action class
################################################################
class _VCP_Action(object):
    def __init__(self):
        self.stat = linuxcnc.stat()
        self.cmd = linuxcnc.command()
        self.tmp = None

    def SET_ESTOP_STATE(self, state):
        if state:
            self.cmd.state(linuxcnc.STATE_ESTOP)
        else:
            self.cmd.state(linuxcnc.STATE_ESTOP_RESET)

    def SET_MACHINE_STATE(self, state):
        if state:
            self.cmd.state(linuxcnc.STATE_ON)
        else:
            self.cmd.state(linuxcnc.STATE_OFF)

    def SET_MACHINE_HOMING(self, joint):
        log.info('Homing Joint: {}'.format(joint))
        self.set_task_mode(linuxcnc.MODE_MANUAL)
        self.cmd.teleop_enable(False)
        self.cmd.home(joint)

    def SET_MACHINE_UNHOMED(self, joint):
        self.set_task_mode(linuxcnc.MODE_MANUAL)
        self.cmd.teleop_enable(False)
        #self.cmd.traj_mode(linuxcnc.TRAJ_MODE_FREE)
        self.cmd.unhome(joint)

    def SET_AUTO_MODE(self):
        self.set_task_mode(linuxcnc.MODE_AUTO)

    def SET_LIMITS_OVERRIDE(self):
        self.cmd.override_limits()

    def SET_MDI_MODE(self):
        self.set_task_mode(linuxcnc.MODE_MDI)

    def SET_MANUAL_MODE(self):
        self.set_task_mode(linuxcnc.MODE_MANUAL)

    def MDI(self, code):
        self.set_task_mode(linuxcnc.MODE_MDI)
        self.cmd.mdi('%s'%code)

    def UPDATE_VAR_FILE(self):
        self.set_task_mode(linuxcnc.MODE_MANUAL)
        self.set_task_mode(linuxcnc.MODE_MDI)

    def OPEN_PROGRAM(self, fname):
        self.set_task_mode(linuxcnc.MODE_AUTO)
        flt = INFO.get_filter_program(str(fname))
        if not flt:
            self.cmd.program_open(str(fname))
        else:
            self.open_filter_program(str(fname), flt)
        STATUS.emit('reload-display')

    def SET_AXIS_ORIGIN(self,axis,value):
        m = "G10 L20 P0 %s%f"%(axis,value)
        success, prev_mode = self.set_task_mode(linuxcnc.MODE_MDI)
        self.cmd.mdi(m)
        self.set_task_mode(premode)
        STATUS.emit('reload-display')

    def RUN(self):
        self.set_task_mode(linuxcnc.MODE_AUTO)
        self.cmd.auto(linuxcnc.AUTO_RUN,0)

    def ABORT(self):
        self.set_task_mode(linuxcnc.MODE_AUTO)
        self.cmd.abort()

    def PAUSE(self):
        if not STATUS.stat.paused:
            self.cmd.auto(linuxcnc.AUTO_PAUSE)
        else:
            log.debug('resume')
            self.cmd.auto(linuxcnc.AUTO_RESUME)

    def SET_RAPID_RATE(self, rate):
        self.cmd.rapidrate(rate/100.0)
    def SET_FEED_RATE(self, rate):
        self.cmd.feedrate(rate/100.0)
    def SET_SPINDLE_RATE(self, rate):
        self.cmd.spindleoverride(rate/100.0)
    def SET_JOG_RATE(self, rate):
        STATUS.set_jog_rate(float(rate))
    def SET_JOG_INCR(self, incr):
        pass

    def SET_SPINDLE_ROTATION(self, direction = 1, rpm = 100):
        self.cmd.spindle(direction,rpm)
    def SET_SPINDLE_FASTER(self):
        self.cmd.spindle(linuxcnc.SPINDLE_INCREASE)
    def SET_SPINDLE_SLOWER(self):
        self.cmd.spindle(linuxcnc.SPINDLE_DECREASE)
    def SET_SPINDLE_STOP(self):
        self.cmd.spindle(linuxcnc.SPINDLE_OFF)

    def ZERO_G92_OFFSET (self, widget):
        self.MDI("G92.1")
        STATUS.emit('reload-display')
    def ZERO_ROTATIONAL_OFFSET(self, widget):
        self.MDI("G10 L2 P0 R 0")
        STATUS.emit('reload-display')

    def RECORD_CURRENT_MODE(self):
        mode = STATUS.get_current_mode()
        self.last_mode = mode
        return mode

    def RESTORE_RECORDED_MODE(self):
        self.set_task_mode(self.last_mode)

    def DO_JOG(self, axisnum, direction):
        distance = STATUS.current_jog_distance
        if axisnum in (3,4,5):
            rate = STATUS.angular_jog_velocity/60
        else:
            rate = STATUS.current_jog_rate/60
        self.JOG(axisnum, direction, rate, distance)

    def JOG(self, axisnum, direction, rate, distance=0):
        jjogmode,j_or_a = STATUS.get_jog_info(axisnum)
        if direction == 0:
            self.cmd.jog(linuxcnc.JOG_STOP, jjogmode, j_or_a)
        else:
            if distance == 0:
                self.cmd.jog(linuxcnc.JOG_CONTINUOUS, jjogmode, j_or_a, direction * rate)
            else:
                self.cmd.jog(linuxcnc.JOG_INCREMENT, jjogmode, j_or_a, direction * rate, distance)

    def TOGGLE_FLOOD(self):
        self.cmd.flood(not(STATUS.stat.flood))
    def SET_FLOOD_ON(self):
        self.cmd.flood(1)
    def SET_FLOOD_OFF(self):
        self.cmd.flood(0)

    def TOGGLE_MIST(self):
        self.cmd.mist(not(STATUS.stat.mist))
    def SET_MIST_ON(self):
        self.cmd.mist(1)
    def SET_MIST_OFF(self):
        self.cmd.mist(0)

    def RELOAD_TOOLTABLE(self):
        self.cmd.load_tool_table()

    def TOGGLE_OPTIONAL_STOP(self):
        self.cmd.set_optional_stop(not(STATUS.stat.optional_stop))
    def SET_OPTIONAL_STOP_ON(self):
        self.cmd.set_optional_stop(True)
    def SET_OPTIONAL_STOP_OFF(self):
        self.cmd.set_optional_stop(False)

    def TOGGLE_BLOCK_DELETE(self):
        self.cmd.set_block_delete(not(STATUS.stat.block_delete))
    def SET_BLOCK_DELETE_ON(self):
        self.cmd.set_block_delete(True)
    def SET_BLOCK_DELETE_OFF(self):
        self.cmd.set_block_delete(False)

    ######################################
    # Action Helper functions
    ######################################


    def set_task_mode(new_mode):
        """Sets task mode, if possible

        Args:
            new_mode (int): linuxcnc.MODE_MANUAL, MODE_MDI or MODE_AUTO

        Returns:
            tuple: (success, previous_mode)
        """
        if is_running():
            log.error("Can't set mode while machine is running")
            return (False, current_mode)
        current_mode = self.stat.task_mode
        if current_mode == new_mode:
            return (True, current_mode)
        else:
            self.cmd.mode(new_mode)
            self.cmd.wait_complete()
            return (True, current_mode)

    def is_running(self):
        """Returns TRUE if machine is moving due to MDI, program execution, etc."""
        self.stat.poll()
        if stat.state == linuxcnc.RCS_EXEC:
            return True
        else:
            return stat.task_mode == linuxcnc.MODE_AUTO \
                and stat.interp_state != linuxcnc.INTERP_IDLE

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
        dialog.format_secondary_text(stderr)
        dialog.run()
        dialog.destroy()

