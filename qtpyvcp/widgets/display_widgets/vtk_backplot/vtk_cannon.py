import vtk_canon
import rs274.interpret
import linuxcnc
import gcode
import shutil
import os


class NullProgress(object):
    def nextphase(self, var1):
        pass

    def progress(self):
        pass


class StatCanon(vtk_canon.VTKCanon):
    def __init__(self, colors, geometry, lathe_view_option, stat, random):
        vtk_canon.VTKCanon.__init__(self, colors, geometry, stat, random)
        self.progress = NullProgress()
        self.lathe_view_option = lathe_view_option

    def is_lathe(self):
        return self.lathe_view_option


class VTKCanon(object):
    def __init__(self, inifile=None):
        inifile = inifile or os.getenv("INI_FILE_NAME")
        if inifile is None or not os.path.isfile(inifile):
            raise ValueError("Invalid INI file: %s", inifile)

        self.stat = linuxcnc.stat()
        self.ini = linuxcnc.ini(inifile)
        self.config_dir = os.path.dirname(inifile)

        temp = self.ini.find("DISPLAY", "GEOMETRY") or 'XYZ'
        self.geometry = temp.upper()

        temp = self.ini.find("DISPLAY", "LATHE") or "false"
        self.lathe_option = temp.lower() in ["1", "true", "yes"]

        temp = self.ini.find("RS274NGC", "PARAMETER_FILE") or "linuxcnc.var"
        self.parameter_file = os.path.join(self.config_dir, temp)
        self.temp_parameter_file = os.path.join(self.parameter_file + '.temp')

    def load(self, filename=None):
        self.stat.poll()

        filename = filename or self.stat.file
        if filename is None or not os.path.isfile(filename):
            return

        # indicate the style of tool-changer
        random = int(self.ini.find("EMCIO", "RANDOM_TOOLCHANGER") or 0)

        # create the object which handles the canonical motion callbacks
        # (straight_feed, straight_traverse, arc_feed, rigid_tap, etc.)
        # StatCanon inherits from VTKCanon, which will do the work for us
        self.canon = vtk_canon.VTKCanon(self.geometry)

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
            self.report_gcode_error(result, seq, filename)

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

    def get_geometry(self):
        return self.geometry

    def report_gcode_error(self, result, seq, filename):
        msg = gcode.strerror(result)
        print("G-Code error in {} line {}: {}".format(
            os.path.basename(filename), seq - 1, msg))


if __name__ == "__main__":
    from qtpyvcp import TOP_DIR
    INI_FILENAME = os.path.join(TOP_DIR, 'sim/xyz.ini')
    gr = VTKCanon(INI_FILENAME)
    gr.load(os.path.join(TOP_DIR, '/sim/example_gcode/qtpyvcp.ngc'))
    gr.print_moves()
