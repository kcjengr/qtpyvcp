import os
import hal

INI_FILE = os.getenv('INI_FILE_NAME')
TCLPATH = os.getenv('LINUXCNC_TCL_DIR', '/usr/lib/tcltk/linuxcnc')

def halshow():
    """Launch HALShow utility.

    ActionButton syntax::

        tool_actions.halshow

    """
    p = os.popen("tclsh {0}/bin/halshow.tcl &".format(TCLPATH))

def calibration():
    """Launch the HAL PID calibration utility.

    ActionButton syntax::

        tool_actions.calibration

    """
    p = os.popen("tclsh {0}/bin/emccalib.tcl -- -ini {1} > /dev/null &"
                 .format(TCLPATH, INI_FILE), "w")

def halmeter():
    """Launch the HALMeter utility.

    ActionButton syntax::

        tool_actions.halmeter

    """
    p = os.popen("halmeter &")

def status():
    """Launch the LinuxCNC status monitor utility.

    ActionButton syntax::

        tool_actions.status

    """
    p = os.popen("linuxcnctop  > /dev/null &", "w")

def halscope():
    """Launch the HALScope utility.

    ActionButton syntax::

        tool_actions.halscope

    """
    p = os.popen("halscope  > /dev/null &", "w")

def classicladder():
    """Launch the ClassicLadder editor.

    Todo:
        classicladder.bindOk should check for classicladder comp
    """
    if hal.component_exists("classicladder_rt"):
        p = os.popen("classicladder  &", "w")
    else:
        text = "Classicladder real-time component not detected"
        print text
        # self.error_dialog.run(text)

halshow.ok = calibration.ok = halmeter.ok = status.ok = halscope.ok = classicladder.ok = lambda widget: True
halshow.bindOk = calibration.bindOk = halmeter.bindOk = status.bindOk = halscope.bindOk = classicladder.bindOk = lambda widget: None
