import gcode
import linuxcnc
import os
import shutil

from qtpyvcp.utilities import logger
from qtpyvcp.plugins import getPlugin

LOG = logger.getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)
NOTIFICATIONS = getPlugin('notifications')

class BaseBackPlot(object):
    def __init__(self, inifile=None):
        self.notification = NOTIFICATIONS

        inifile = inifile or os.getenv("INI_FILE_NAME")
        if inifile is None or not os.path.isfile(inifile) and not IN_DESIGNER:
            raise ValueError("Invalid INI file: %s", inifile)

        self.canon = None

        self.stat = linuxcnc.stat()
        self.ini = linuxcnc.ini(inifile)
        self.config_dir = os.path.dirname(inifile)

        temp = self.ini.find("EMCIO", "RANDOM_TOOLCHANGER")
        self.random = int(temp or 0)

        temp = self.ini.find("DISPLAY", "GEOMETRY") or 'XYZ'
        self.geometry = temp.upper()

        temp = self.ini.find("DISPLAY", "LATHE") or "false"
        self.lathe_option = temp.lower() in ["1", "true", "yes"]

        temp = self.ini.find("RS274NGC", "PARAMETER_FILE") or "linuxcnc.var"
        self.parameter_file = os.path.join(self.config_dir, temp)
        self.temp_parameter_file = os.path.join(self.parameter_file + '.temp')

        self.last_filename = None

    def load(self, filename=None):
        if self.canon is None:
            return

        filename = filename or self.last_filename
        if filename is None:
            self.stat.poll()
            filename = self.stat.file

        if filename is None or not os.path.isfile(filename):
            self.canon = None
            self.notification.notification_dispatcher.setNotify("3D plot", "Can't load backplot, invalid file: {}".format(filename))
            # raise ValueError("Can't load backplot, invalid file: {}".format(filename))

        self.last_filename = filename

        if os.path.exists(self.parameter_file):
            shutil.copy(self.parameter_file, self.temp_parameter_file)

        self.canon.parameter_file = self.temp_parameter_file

        # Some initialization g-code to set the units and optional user code
        unitcode = "G%d" % (20 + (self.stat.linear_units == 1))
        initcode = self.ini.find("RS274NGC", "RS274NGC_STARTUP_CODE") or ""

        # THIS IS WHERE IT ALL HAPPENS: load_preview will execute the code,
        # call back to the canon with motion commands, and record a history
        # of all the movements.

        try:
            result, seq = gcode.parse(filename, self.canon, unitcode, initcode)

            if result > gcode.MIN_ERROR:
                msg = gcode.strerror(result)
                fname = os.path.basename(filename)
                self.notification.notification_dispatcher.setNotify(f"3D plot", "Error in {fname} line {seq - 1}\n{msg}")
                # raise SyntaxError("Error in %s line %i: %s" % (fname, seq - 1, msg))

        except KeyboardInterrupt:
            # probably raised by an (AXIS, stop) comment in the G-code file
            # abort generating the backplot
            pass
        
        except Exception as e:
            LOG.debug(f"CANON ERROR {e}")
        # clean up temp var file and the backup
        os.unlink(self.temp_parameter_file)
        os.unlink(self.temp_parameter_file + '.bak')


if __name__ == "__main__":
    from qtpyvcp import TOP_DIR
    from .base_canon import PrintCanon

    INI_FILE = os.path.join(TOP_DIR, 'sim/xyz.ini')
    NGC_FILE = os.path.join(TOP_DIR, 'sim/example_gcode/blank.ngc')
    gr = BaseBackPlot(INI_FILE, canon=PrintCanon)
    gr.load(NGC_FILE)
