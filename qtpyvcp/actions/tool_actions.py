import os
import hal

INI_FILE = os.getenv('INI_FILE_NAME')
TCLPATH = os.getenv('LINUXCNC_TCL_DIR', '/usr/lib/tcltk/linuxcnc')

"""Tool Actions launch LinuxCNC tools"""

def halshow():
    """Launch HALShow utility to view HAL and a Watch Window

    * Components
    * Pins
    * Parameters
    * Signals
    * Functions
    * Threads

    ActionButton syntax::

        tool_actions.halshow

    """
    p = os.popen("tclsh {0}/bin/halshow.tcl &".format(TCLPATH))

def calibration():
    """Launch the HAL PID calibration utility.

    Test PID, Scale, Acceleration and Velocity settings if they are in the INI
    file.

    ActionButton syntax::

        tool_actions.calibration

    """
    p = os.popen("tclsh {0}/bin/emccalib.tcl -ini {1} > /dev/null &"
                 .format(TCLPATH, INI_FILE), "w")

def halmeter():
    """Launch the HALMeter utility to display the current value of a single pin.

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

    Halscope is an oscilloscope for the HAL

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

def simulate_probe():
    """Launch Simulate Probe

    ActionButton syntax::

        tool_actions.simulate_probe

    """
    p = os.popen("simulate_probe > /dev/null &", "w")

halshow.ok = calibration.ok = halmeter.ok = status.ok = halscope.ok = classicladder.ok = simulate_probe.ok = lambda widget: True
halshow.bindOk = calibration.bindOk = halmeter.bindOk = status.bindOk = halscope.bindOk = classicladder.bindOk = simulate_probe.bindOk = lambda widget: None
