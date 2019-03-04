import linuxcnc
import gcode
import shutil
import os

from base_canon import BaseCanon


class BaseBackPlot(object):
    def __init__(self, inifile=None, canon=BaseCanon):

        inifile = inifile or os.getenv("INI_FILE_NAME")
        if inifile is None or not os.path.isfile(inifile):
            raise ValueError("Invalid INI file: %s", inifile)

        self.canon_class = canon
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

        filename = filename or self.last_filename
        if filename is None:
            self.stat.poll()
            filename = self.stat.file

        if filename is None or not os.path.isfile(filename):
            self.canon = None
            raise ValueError("Can't load backplot, invalid file: %s" % filename)

        self.last_filename = filename

        # create the object which handles the canonical motion callbacks
        # (straight_feed, straight_traverse, arc_feed, rigid_tap, etc.)
        self.canon = self.canon_class()

        if os.path.exists(self.parameter_file):
            shutil.copy(self.parameter_file, self.temp_parameter_file)

        self.canon.parameter_file = self.temp_parameter_file

        # Some initialization g-code to set the units and optional user code
        unitcode = "G%d" % (20 + (self.stat.linear_units == 1))
        initcode = self.ini.find("RS274NGC", "RS274NGC_STARTUP_CODE") or ""

        # THIS IS WHERE IT ALL HAPPENS: load_preview will execute the code,
        # call back to the canon with motion commands, and record a history
        # of all the movements.
        result, seq = gcode.parse(filename, self.canon, unitcode, initcode)

        if result > gcode.MIN_ERROR:
            msg = gcode.strerror(result)
            fname = os.path.basename(filename)
            raise SyntaxError("Error in %s line %i: %s" % (fname, seq - 1, msg))

        # clean up temp var file and the backup
        os.unlink(self.temp_parameter_file)
        os.unlink(self.temp_parameter_file + '.bak')

    def print_moves(self):
        # each item is:
        # 1) the line number in the gcode file that generated the movement
        # 2) a tuple of coordinates: the line start location
        # 3) a tuple of coordinates: the line end location
        # 4) feedrate (ONLY FOR "FEED" and "ARCFEED" entries)
        # 5) a tuple of coordinates: the tool offset

        for item in self.canon.feed:
            print("Feed: ", item[0], item[1][:3], item[2][:3])

        for item in self.canon.arcfeed:
            print("ArcFeed: ", item[0], item[1][:3], item[2][:3])

        for item in self.canon.traverse:
            print("Rapid: ", item[0], item[1][:3], item[2][:3])


if __name__ == "__main__":
    from qtpyvcp import TOP_DIR
    from base_canon import PrintCanon
    INI_FILE = os.path.join(TOP_DIR, 'sim/xyz.ini')
    NGC_FILE = os.path.join(TOP_DIR, 'sim/example_gcode/qtpyvcp.ngc')
    gr = BaseBackPlot(INI_FILE, canon=PrintCanon)
    gr.load(NGC_FILE)
    gr.print_moves()
