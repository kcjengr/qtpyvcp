import sys
import linuxcnc
import tempfile

from qtpy.QtCore import Qt, QTimer
# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')
STAT = STATUS.stat
INFO = Info()
CMD = linuxcnc.command()

from qtpyvcp.actions.base_actions import setTaskMode


#==============================================================================
# Program actions
#==============================================================================

def load(fname, add_to_recents=True, isreload=False):
    if not fname:
        # load a blank file. Maybe should load [DISPLAY] OPEN_FILE
        clear()

    #setTaskMode(linuxcnc.MODE_AUTO)
    if not isreload:
        STATUS.addLock()
    
    filter_prog = INFO.getFilterProgram(fname)
    if not filter_prog:
        LOG.debug('Loading NC program: %s', fname)
        CMD.program_open(fname.encode('utf-8'))
        CMD.wait_complete()
    else:
        LOG.debug('Loading file with filter program: %s', fname)
        openFilterProgram(fname, filter_prog)

    if add_to_recents:
        addToRecents(fname)
    
    QTimer.singleShot(300, STATUS.removeLock)

load.ok = lambda *args, **kwargs: True
load.bindOk = lambda *args, **kwargs: True

def reload():
    """Reload the currently loaded NC program

    ActionButton syntax::

        program.reload
    """
    stat = linuxcnc.stat()
    stat.poll()
    fname = stat.file
    if os.path.exists(fname):
        load(stat.file, add_to_recents=False, isreload=True)

reload.ok = lambda *args, **kwargs: True
reload.bindOk = lambda *args, **kwargs: True

def clear():
    """Clear the loaded NC program

    ActionButton syntax::

        program.clear
    """

    _, blankfile = tempfile.mkstemp(prefix="new_program_", suffix=".ngc")
    with open(blankfile, 'w') as fp:
        fp.write("(New Program)\n\n\nM30")
    load(blankfile, add_to_recents=False)

clear.ok = lambda *args, **kwargs: True
clear.bindOk = lambda *args, **kwargs: True

def addToRecents(fname):
    files = STATUS.recent_files.getValue()
    if fname in files:
        files.remove(fname)
    files.insert(0, fname)
    STATUS.recent_files.setValue(files[:STATUS.max_recent_files])

# -------------------------------------------------------------------------
# program RUN action
# -------------------------------------------------------------------------
def run(start_line=0):
    """Runs the loaded program, optionally starting from a specific line.

    ActionButton syntax::

        program.run
        program.run:line

    Args:
        start_line (int, optional) : The line to start program from. Defaults to 0.
    """
    if STAT.state == linuxcnc.RCS_EXEC and STAT.paused:
        CMD.auto(linuxcnc.AUTO_RESUME)
    elif setTaskMode(linuxcnc.MODE_AUTO):
        CMD.auto(linuxcnc.AUTO_RUN, start_line)

def _run_ok(widget=None):
    """Checks if it is OK to run a program.

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
    elif not STAT.paused and not STAT.interp_state == linuxcnc.INTERP_IDLE:
        ok = False
        msg = "Can't run program when already running"
    elif STAT.file == "":
        ok = False
        msg = "Can't run program when no file loaded"
    else:
        ok = True
        msg = "Run program"

    _run_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _run_bindOk(widget):
    STATUS.estop.onValueChanged(lambda: _run_ok(widget))
    STATUS.enabled.onValueChanged(lambda: _run_ok(widget))
    STATUS.all_axes_homed.onValueChanged(lambda: _run_ok(widget))
    STATUS.interp_state.onValueChanged(lambda: _run_ok(widget))
    STATUS.file.onValueChanged(lambda: _run_ok(widget))

run.ok = _run_ok
run.bindOk = _run_bindOk

# -------------------------------------------------------------------------
# program RUN from LINE action
# -------------------------------------------------------------------------
def run_from_line(line=None):
    # TODO: This might should show a popup to select start line,
    #       or it could get the start line from the gcode view or
    #       even from the backplot.
    LOG.error('Run from line not implemented yet.')


run_from_line.ok = _run_ok
run_from_line.bindOk = _run_bindOk

# -------------------------------------------------------------------------
# program STEP action
# -------------------------------------------------------------------------
def step():
    """Steps program line by line

    ActionButton syntax::

        program.step

    """
    if STAT.state == linuxcnc.RCS_EXEC and STAT.paused:
        CMD.auto(linuxcnc.AUTO_STEP)
    elif setTaskMode(linuxcnc.MODE_AUTO):
        CMD.auto(linuxcnc.AUTO_STEP)

step.ok = _run_ok
step.bindOk = _run_bindOk

# -------------------------------------------------------------------------
# program PAUSE action
# -------------------------------------------------------------------------
def pause():
    """Pause executing program


    ActionButton syntax::

        program.pause

    """
    LOG.debug("Pausing program execution")
    CMD.auto(linuxcnc.AUTO_PAUSE)

def _pause_ok(widget=None):
    """Checks if it is OK to pause the program.

    Args:
        widget (QWidget, optional) : If a widget is supplied it will be
            enabled/disabled according to the result, and will have it's
            statusTip property set to the reason the action is disabled.

    Returns:
        bool : True if Ok, else False.
    """
    if STAT.state == linuxcnc.RCS_EXEC and not STAT.paused:
        msg = "Pause program execution"
        ok = True
    elif STAT.paused:
        msg = "Program is already paused"
        ok = False
    else:
        msg = "No program running to pause"
        ok = False

    _pause_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _pause_bindOk(widget):
    STATUS.state.onValueChanged(lambda: _pause_ok(widget))
    STATUS.paused.onValueChanged(lambda: _pause_ok(widget))

pause.ok = _pause_ok
pause.bindOk = _pause_bindOk

# -------------------------------------------------------------------------
# program RESUME action
# -------------------------------------------------------------------------
def resume():
    """Resume a previously paused program

    ActionButton syntax::

        program.resume

    """
    LOG.debug("Resuming program execution")
    CMD.auto(linuxcnc.AUTO_RESUME)

def _resume_ok(widget):
    """Checks if it is OK to resume a paused program.

    Args:
        widget (QWidget, optional) : If a widget is supplied it will be
            enabled/disabled according to the result, and will have it's
            statusTip property set to the reason the action is disabled.

    Returns:
        bool : True if Ok, else False.
    """
    if STAT.state == linuxcnc.RCS_EXEC and STAT.paused:
        ok = True
        msg = "Resume program execution"
    else:
        ok = False
        msg = "No paused program to resume"

    _resume_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _resume_bindOk(widget):
    STATUS.paused.onValueChanged(lambda: _resume_ok(widget))
    STATUS.state.onValueChanged(lambda: _resume_ok(widget))

resume.ok = _resume_ok
resume.bindOk = _resume_bindOk

# -------------------------------------------------------------------------
# program ABORT action
# -------------------------------------------------------------------------
def abort():
    """Aborts any currently executing program, MDI command or homing operation.

    ActionButton syntax::

        program.abort

    """

    LOG.debug("Aborting program")
    CMD.abort()

def _abort_ok(widget=None):
    """Checks if it is OK to abort current operation.

    Args:
        widget (QWidget, optional) : If a widget is supplied it will be
            enabled/disabled according to the result, and will have it's
            statusTip property set to the reason the action is disabled.

    Returns:
        bool : True if Ok, else False.
    """
    if STAT.state == linuxcnc.RCS_EXEC or STAT.state == linuxcnc.RCS_ERROR:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Nothing to abort"

    _abort_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _abort_bindOk(widget):
    STATUS.state.onValueChanged(lambda: _abort_ok(widget))

abort.ok = _abort_ok
abort.bindOk = _abort_bindOk

# -------------------------------------------------------------------------
# BLOCK DELETE actions
# -------------------------------------------------------------------------
class block_delete:
    """Block Delete Group"""
    @staticmethod
    def on():
        """Start ignoring lines beginning with '/'.

        ActionButton syntax::

            program.block-delete.on

        """

        LOG.debug("Setting block delete green<ON>")
        CMD.set_block_delete(True)

    @staticmethod
    def off():
        """Stop ignoring lines beginning with '/'.

        ActionButton syntax::

            program.block-delete.off

        """

        LOG.debug("Setting block delete red<OFF>")
        CMD.set_block_delete(False)

    @staticmethod
    def toggle():
        """Toggle ignoring lines beginning with '/'.

        ActionButton syntax::

            program.block-delete.toggle

        """

        if STAT.block_delete == True:
            block_delete.off()
        else:
            block_delete.on()

def _block_delete_ok(widget=None):
    """Checks if it is OK to set block_delete.

    Args:
        widget (QWidget, optional) : If a widget is supplied it will be
            enabled/disabled according to the result, and will have it's
            statusTip property set to the reason the action is disabled.

    Returns:
        bool : True if Ok, else False.
    """
    if STAT.task_state == linuxcnc.STATE_ON:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be ON to set Block Del"

    _block_delete_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _block_delete_bindOk(widget):
    widget.setChecked(STAT.block_delete)
    STATUS.task_state.onValueChanged(lambda: _block_delete_ok(widget))
    STATUS.block_delete.onValueChanged(lambda s: widget.setChecked(s))

block_delete.on.ok = block_delete.off.ok = block_delete.toggle.ok = _block_delete_ok
block_delete.on.bindOk = block_delete.off.bindOk = block_delete.toggle.bindOk = _block_delete_bindOk

# -------------------------------------------------------------------------
# OPTIONAL STOP actions
# -------------------------------------------------------------------------
class optional_stop:
    """Optional Stop Group"""
    @staticmethod
    def on():
        """Pause when a line beginning with M1 is encountered

        ActionButton syntax::

            program.optional-stop.on

        """

        LOG.debug("Setting optional stop green<ON>")
        CMD.set_optional_stop(True)

    @staticmethod
    def off():
        """Don't pause when a line beginning with M1 is encountered

        ActionButton syntax::

            program.optional-stop.off

        """

        LOG.debug("Setting optional stop red<OFF>")
        CMD.set_optional_stop(False)

    @staticmethod
    def toggle():
        """Toggle pause when a line beginning with M1 is encountered

        ActionButton syntax::

            program.optional-stop.toggle

        """

        if STAT.optional_stop == True:
            optional_stop.off()
        else:
            optional_stop.on()

def _optional_stop_ok(widget=None):
    """Checks if it is OK to set optional_stop.

    Args:
        widget (QWidget, optional) : If a widget is supplied it will be
            enabled/disabled according to the result, and will have it's
            statusTip property set to the reason the action is disabled.

    Returns:
        bool : True if Ok, else False.
    """
    if STAT.task_state == linuxcnc.STATE_ON:
        ok = True
        msg = ""
    else:
        ok = False
        msg = "Machine must be ON to set Opt Stop"

    _optional_stop_ok.msg = msg

    if widget is not None:
        widget.setEnabled(ok)
        widget.setStatusTip(msg)
        widget.setToolTip(msg)

    return ok

def _optional_stop_bindOk(widget):
    widget.setChecked(STAT.block_delete)
    STATUS.task_state.onValueChanged(lambda: _optional_stop_ok(widget))
    STATUS.optional_stop.onValueChanged(lambda s: widget.setChecked(s))

optional_stop.on.ok = optional_stop.off.ok = optional_stop.toggle.ok = _optional_stop_ok
optional_stop.on.bindOk = optional_stop.off.bindOk = optional_stop.toggle.bindOk  = _optional_stop_bindOk

optional_skip = block_delete

#==============================================================================
# Program preprocessing handlers
#==============================================================================
import os, sys, time, select, re
import tempfile, atexit, shutil

FILTER_TEMP = None

def openFilterProgram(infile, prog_name):
    temp_dir = _mktemp()
    outfile = os.path.join(temp_dir, os.path.basename(infile))
    #FilterProgram(prog_name, infile, outfile, lambda r: r or _loadFilterResult(outfile))
    FilterProgram(prog_name, infile, outfile, None)
    CMD.program_open(outfile)
    LOG.debug('Linuxcnc Command - program_open')

def _loadFilterResult(fname):
    if fname:
        CMD.program_open(fname)

def _mktemp():
    global FILTER_TEMP
    if FILTER_TEMP is not None:
        return FILTER_TEMP
    FILTER_TEMP = tempfile.mkdtemp(prefix='emcflt-', suffix='.d')
    atexit.register(lambda: shutil.rmtree(FILTER_TEMP))
    return FILTER_TEMP

# slightly reworked code from gladevcp
# loads a filter program and collects the result
progress_re = re.compile("^FILTER_PROGRESS=(\\d*)$")
class FilterProgram:
    def __init__(self, prog_name, infile, outfile, callback=None):
        import subprocess
        outfile = open(outfile, "w")
        infile = infile.replace("'", "'\\''")

        env = dict(os.environ)
        env['AXIS_PROGRESS_BAR'] = '1'
        self.p = subprocess.run(["sh", "-c", "%s '%s'" % (prog_name, infile)],
                                  stdin=subprocess.PIPE,
                                  stdout=outfile,
                                  stderr=subprocess.PIPE,
                                  env=env,
                                  text=True)

        self.stderr_text = []
        self.program_filter = prog_name
        self.callback = callback
        #self.gid = STATUS.onValueChanged('periodic', self.update)
        #progress = Progress(1, 100)
        #progress.set_text(_("Filtering..."))
        # force file load until know what to do about update/finish

    def update(self, w):
        if self.p.poll() is not None:
            self.finish()
            STATUS.disconnect(self.gid)
            return False

        r, w, x = select.select([self.p.stderr], [], [], 0)
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
