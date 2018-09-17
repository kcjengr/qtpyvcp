import os
import hal

INI_FILE = os.getenv('INI_FILE')
TCLPATH = os.getenv('TCLLIBPATH')

def halshow():
    p = os.popen("tclsh {0}/bin/halshow.tcl &".format(TCLPATH))

def calibration():
    p = os.popen("tclsh {0}/bin/emccalib.tcl -- -ini {1} > /dev/null &".format(TCLPATH, INI_FILE), "w")

def halmeter():
    p = os.popen("halmeter &")

def status():
    p = os.popen("linuxcnctop  > /dev/null &", "w")

def halscope():
    p = os.popen("halscope  > /dev/null &", "w")

def classicladder():
    if hal.component_exists("classicladder_rt"):
        p = os.popen("classicladder  &", "w")
    else:
        text = "Classicladder real-time component not detected"
        print text
        # self.error_dialog.run(text)

halshow.ok = calibration.ok = halmeter.ok = status.ok = halscope.ok = classicladder.ok = lambda w: True
halshow.bindOk = calibration.bindOk = halmeter.bindOk = status.bindOk = halscope.bindOk = classicladder.bindOk = lambda w: None
