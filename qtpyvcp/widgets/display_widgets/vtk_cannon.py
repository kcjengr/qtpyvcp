import rs274.glcanon
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


class StatCanon(rs274.glcanon.GLCanon, rs274.interpret.StatMixin):
    def __init__(self, colors, geometry, lathe_view_option, stat, random):
        rs274.glcanon.GLCanon.__init__(self, colors, geometry)
        rs274.interpret.StatMixin.__init__(self, stat, random)
        self.progress = NullProgress()
        self.lathe_view_option = lathe_view_option

    def is_lathe(self):
        return self.lathe_view_option


class VTKCanon(rs274.glcanon.GlCanonDraw):
    def __init__(self, inifile=None):
        inifile = inifile or os.getenv("INI_FILE_NAME")
        if inifile is None:
            raise ValueError("Invalid INI file.")

        self.inifile = linuxcnc.ini(inifile)
        self.INI_FILE_PATH = os.path.split(inifile)[0]
        self.select_primed = None

        temp = self.inifile.find("DISPLAY", "GEOMETRY")
        if temp:
            self.geometry = temp.upper()
        else:
            self.geometry = 'XYZ'

        temp = self.inifile.find("DISPLAY", "LATHE")
        self.lathe_option = temp == "1" or temp == "True" or temp == "true"

        rs274.glcanon.GlCanonDraw.__init__(self, linuxcnc.stat(), None)

        live_axis_count = 0
        for i, j in enumerate("XYZABCUVW"):
            if self.stat.axis_mask & (1 << i) == 0:
                continue
            live_axis_count += 1

        self.num_joints = int(self.inifile.find("TRAJ", "JOINTS") or live_axis_count)

    def load(self, filename=None):
        self.stat.poll()

        filename = filename or self.stat.file
        if filename is None or not os.path.isfile(filename):
            return

        # indicate the style of tool-changer
        random = int(self.inifile.find("EMCIO", "RANDOM_TOOLCHANGER") or 0)

        # create the object which handles the canonical motion callbacks
        # (straight_feed, straight_traverse, arc_feed, rigid_tap, etc.)
        # StatCanon inherits from GLCanon, which will do the work for us
        self.canon = StatCanon(None, self.get_geometry(), self.lathe_option,
                               self.stat, random)

        # load numbered g-code variables from files. Current working
        # directory must be where the files live Parameter files are
        # persistent across linuxcnc sessions.  Since this is just a
        # simulation, we don't want the gcode file to actually change
        # the persistent parameters, so we make a temporary copy
        parameter = self.inifile.find("RS274NGC", "PARAMETER_FILE")
        temp_parameter_orig = os.path.join(self.INI_FILE_PATH,
                                           os.path.basename(
                                               parameter or "linuxcnc.var"))

        temp_parameter_new = os.path.join(os.getcwd(), "tmp_params.var")
        if os.path.exists(parameter):
            shutil.copy(temp_parameter_orig, temp_parameter_new)

        self.canon.parameter_file = temp_parameter_new

        # Some initialization g-code to set the units and optional user code
        unitcode = "G%d" % (20 + (self.stat.linear_units == 1))
        initcode = self.inifile.find("RS274NGC",
                                     "RS274NGC_STARTUP_CODE") or ""

        # THIS IS WHERE IT ALL HAPPENS: load_preview will execute the code,
        # call back to the canon with motion commands, and record a history
        # of all the movements.
        result, seq = self.load_preview(filename, self.canon, unitcode,
                                        initcode)
        if result > gcode.MIN_ERROR:
            self.report_gcode_error(result, seq, filename)

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

    def get_limits(self):
        return self.soft_limits()

    def report_gcode_error(self, result, seq, filename):
        msg = gcode.strerror(result)
        print("G-Code error in {} line {}: {}".format(
            os.path.basename(filename), seq - 1, msg))


if __name__ == "__main__":
    from qtpyvcp import TOP_DIR
    INI_FILENAME = os.path.join(TOP_DIR, 'sim/xyz.ini')
    gr = VTKCanon(INI_FILENAME)
    gr.load()
    gr.print_moves()
