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
#   LinuxCNC program related actions

import linuxcnc
from PyQt5.QtWidgets import QAction

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


#==============================================================================
# Program actions
#==============================================================================

def bindWidget(widget, action):

    if isinstance(widget, QAction):
        sig = widget.triggered
    else:
        sig = widget.clicked
    sig.connect(globals()[action])

    if action == 'run':
        widget.setEnabled(runOk(widget))

        STATUS.estop.connect(lambda: runOk(widget))
        STATUS.enabled.connect(lambda: runOk(widget))
        STATUS.all_homed.connect(lambda: runOk(widget))
        STATUS.interp_state.connect(lambda: runOk(widget))
        STATUS.file.connect(lambda: runOk(widget))

    elif action == 'pause':
        widget.setEnabled(pauseOk())

        STATUS.state.connect(lambda: pauseOk(widget))
        STATUS.paused.connect(lambda: pauseOk(widget))

    elif action == 'resume':
        widget.setEnabled(STAT.paused)
        STATUS.paused.connect(lambda paused: widget.setEnabled(paused))
    elif action == 'step':
        widget.setEnabled(False)

def load(fname, add_to_recents=True):
    setTaskMode(linuxcnc.MODE_AUTO)
    filter_prog = INFO.getFilterProgram(fname)
    if not filter_prog:
        CMD.program_open(fname.encode('utf-8'))
    else:
        openFilterProgram(fname, filter_prog)

    if add_to_recents:
        addToRecents(fname)

def run(start_line=0):
    """
    Runs the loaded program, optionally starting from a specific line.

    Args:
        start_line (int, optional) : The line to start program from. Defaults to 0.
    """

    # check if it is OK to run
    if not runOk():
        LOG.error(runOk.msg)
        return
    if STAT.state == linuxcnc.RCS_EXEC and STAT.paused:
        CMD.auto(linuxcnc.AUTO_RESUME)
    elif setTaskMode(linuxcnc.MODE_AUTO):
        CMD.auto(linuxcnc.AUTO_RUN, start_line)

def runOk(widget=None):
    """
    Checks if it is OK to run a program.

    Args:
        widget (QWidget, optional) : If a widget is supplied it will be
            enabled/disabled according to the result, and will have it's
            statusTip property set to the reason the action is disabled.

    Returns:
        bool : True if Ok, else False.

    """
    if STAT.estop:
        ok = False
        msg = "Can't run program when in E-Stop"
    elif not STAT.enabled:
        ok = False
        msg = "Can't run program when not enabled"
    elif not STATUS.allHomed():
        ok = False
        msg = "Can't run program when not homed"
    elif not STAT.interp_state == linuxcnc.INTERP_IDLE:
        ok = False
        msg = "Can't run program when interpreter is not idle"
    elif STAT.file == "":
        ok = False
        msg = "Can't run program when no file loaded"
    else:
        ok = True
        msg = "Run Program"

    runOk.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def runFromLine():
    # TODO: This might should show a popup to select start line,
    #       or it could get the start line from the gcode view or
    #       even from the backplot.
    raise NotImplemented

def pause():
    if not pauseOk():
        LOG.error(pauseOk.msg)
        return
    LOG.debug("Pausing program execution")
    CMD.auto(linuxcnc.AUTO_PAUSE)

def pauseOk(widget=None):
    if STAT.state == linuxcnc.RCS_EXEC and not STAT.paused:
        msg = "Pause program"
        ok = True
    elif STAT.paused:
        msg = "Already paused"
        ok = False
    else:
        msg = "Can't pause when not running"
        ok = False

    runOk.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def resume():
    if STAT.state == linuxcnc.RCS_EXEC and STAT.paused:
        LOG.debug("Resuming program execution")
        CMD.auto(linuxcnc.AUTO_RESUME)
    else:
        LOG.warn("Can't resume program execution, is a program paused?")

def step():
    pass

def addToRecents(fname):
    if fname in STATUS.recent_files:
        STATUS.recent_files.remove(fname)
    STATUS.recent_files.insert(0, fname)
    STATUS.recent_files = STATUS.recent_files[:STATUS.max_recent_files]
    STATUS.recent_files_changed.emit(tuple(STATUS.recent_files))


#==============================================================================
# Program preprocessing handlers
#==============================================================================
import os, sys, time, select, re
import tempfile, atexit, shutil

FILTER_TEMP = None

def openFilterProgram(self, fname, flt):
    temp_dir = _mktemp()
    tmp = os.path.join(temp_dir, os.path.basename(fname))
    print 'temp', temp_dir
    flt = FilterProgram(flt, fname, tmp, lambda r: r or self._loadFilterResult(tmp))

def _loadFilterResult(self, fname):
    if fname:
        CMD.program_open(fname)

def _mktemp(self):
    global FILTER_TEMP
    if FILTER_TEMP is not None:
        return FILTER_TEMP
    FILTER_TEMP = tempfile.mkdtemp(prefix='emcflt-', suffix='.d')
    atexit.register(lambda: shutil.rmtree(FILTER_TEMP))

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
        LOG.error("Error loading filter program!")
        # dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
        #         _("The program %(program)r exited with code %(code)d.  "
        #         "Any error messages it produced are shown below:")
        #             % {'program': self.program_filter, 'code': exitcode})
        # diaLOG.format_secondary_text(stderr)
        # diaLOG.run()
        # diaLOG.destroy()
