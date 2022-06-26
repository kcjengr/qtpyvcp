"""
GCodeProperties
--------

This plugin provides the information about sizes and times

This plugin is not loaded by default, so to use it you will first
need to add it to your VCPs YAML config file.

YAML configuration:

.. code-block:: yaml

    data_plugins:
      gcode_properties:
        provider: qtpyvcp.plugins.gcode_properties:GCodeProperties

"""
import os
import pprint
import shutil
import gcode
import linuxcnc

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import DataPlugin, DataChannel

from qtpyvcp.widgets.display_widgets.vtk_backplot.base_canon import BaseCanon

LOG = getLogger(__name__)
STATUS = getPlugin('status')
INFO = Info()

INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))

MAX_LINEAR_VELOCITY = bool(INIFILE.find("TRAJ", "MAX_LINEAR_VELOCITY"))
MAX_ANGULAR_VELOCITY = bool(INIFILE.find("TRAJ", "MAX_ANGULAR_VELOCITY"))

MACHINE_UNITS = 2 if INFO.getIsMachineMetric() else 1


class GCodeProperties(DataPlugin):
    """GCodeProperties Plugin"""
    def __init__(self):
        super(GCodeProperties, self).__init__()

        inifile = os.getenv("INI_FILE_NAME")
        self.stat = STATUS
        self.ini = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        self.config_dir = os.path.dirname(inifile)

        self.canon = None
        self.loaded_file = None
        
        temp = self.ini.find("RS274NGC", "PARAMETER_FILE") or "linuxcnc.var"
        self.parameter_file = os.path.join(self.config_dir, temp)
        self.temp_parameter_file = os.path.join(self.parameter_file + '.temp')

    def initialize(self):
        
        self.stat.file.notify(self._file_event)

    @DataChannel
    def file_name(self, chan):
        """The current file name.

        Args:
            None

        Returns:
            The current open file name as a string.

        Channel syntax::

            gcode_properties:file_name

        """

        if not self.loaded_file:
            chan.value = "No file loaded"

        return chan.value

    @file_name.tostring
    def file_name(self, chan):
        return chan.value

    @DataChannel
    def tool_calls_num(self, chan):
        """The total tool calls number.

        Args:
            None

        Returns:
            The total tool calls number

        Channel syntax::

            gcode_properties:tool_calls_num

        """

        if not self.loaded_file:
            chan.value = 0

        return chan.value

    @tool_calls_num.tostring
    def tool_calls_num(self, chan):
        return chan.value

    @DataChannel
    def file_size(self, chan):
        """The current file size.

        Args:
            None

        Returns:
            The current file size in bytes

        Channel syntax::

            gcode_properties:size

        """

        if not self.loaded_file:
            chan.value = 0

        return chan.value

    @file_size.tostring
    def file_size(self, chan):
        return chan.value
    
    @DataChannel
    def file_rapids(self, chan):
        """The current file rapis distance.

        Args:
            None

        Returns:
            The current file rapis distance in machine units

        Channel syntax::

            gcode_properties:rapids

        """

        if not self.loaded_file:
            chan.value.float(0.0)

        if MACHINE_UNITS == 2:
            conv = 1
            units = "mm"
            fmt = "%.3f"
        else:
            conv = 1/25.4
            units = "in"
            fmt = "%.4f"

        return chan.value

    @file_rapids.tostring
    def file_rapids(self, chan):
        return chan.value

    @DataChannel
    def file_lines(self, chan):
        """The current number of lines.

        Args:
            None

        Returns:
            The current number of lines the file has

        Channel syntax::

            gcode_properties:file_lines

        """

        if not self.loaded_file:
            chan.value = 0

        return chan.value

    @file_lines.tostring
    def file_lines(self, chan):
        return chan.value
    
    
    @DataChannel
    def file_time(self, chan):
        """The current file run time.

        Args:
            format (str) : Format spec. Defaults to ``%I:%M:%S %p``.
                See http://strftime.org for supported formats.

        Returns:
            The run time of the loaded file as a formatted string. Default HH:MM:SS AM

        Channel syntax::

            gcode_properties:time
            gcode_properties:time?string
            gcode_properties:time?string&format=%S

        """

        if not self.loaded_file:
            chan.value(0)

        return chan.value

    @file_time.tostring
    def file_time(self, chan, format="%I:%M:%S %p"):
        return chan.value.strftime(format)

    @DataChannel
    def file_rapid_distance(self, chan):
        """The full distance done in rapid of the path.

        Args:

        Returns:
            The full distance done in rapid of the path

        Channel syntax::

            gcode_properties:file_rapid_distance

        """

        if not self.loaded_file:
            chan.value = 0

        return chan.value

    @file_rapid_distance.tostring
    def file_rapid_distance(self, chan):
        return chan.value
    
    @DataChannel
    def file_feed_distance(self, chan):
        """The full distance done in feed velocity of the path.

        Args:

        Returns:
            The full distance done in feed velocity of the path

        Channel syntax::

            gcode_properties:file_feed_distance

        """

        if not self.loaded_file:
            chan.value = 0

        return chan.value

    @file_feed_distance.tostring
    def file_feed_distance(self, chan):
        return chan.value

    @DataChannel
    def file_work_planes(self, chan):
        """The current file plane.

        Args:
            None

        Returns:
            The file work planes

        Channel syntax::

            gcode_properties:file_work_planes

        """

        if not self.loaded_file:
            chan.value = []
        
        return chan.value

    @file_work_planes.tostring
    def file_work_planes(self, chan):
        return chan.value
    
    @DataChannel
    def file_rigid_taps(self, chan):
        """The rigid taps found in file.

        Args:
            None

        Returns:
            The rigid taps found in file.

        Channel syntax::

            gcode_properties:file_rigid_taps

        """

        if not self.loaded_file:
            chan.value = []
        
        return chan.value

    @file_rigid_taps.tostring
    def file_rigid_taps(self, chan):
        return chan.value
    
    @DataChannel
    def file_offsets(self, chan):
        """The offsets found in file.

        Args:
            None

        Returns:
            The offsets found in file.

        Channel syntax::

            gcode_properties:file_offsets

        """

        if not self.loaded_file:
            chan.value = dict()
        
        return chan.value

    @file_offsets.tostring
    def file_offsets(self, chan):
        return chan.value
    
    @DataChannel
    def file_feed(self, chan):
        """The current file run distance.

        Args:
            None

        Returns:
            The distance the machine will run with the loaded file

        Channel syntax::

            gcode_properties:feed

        """
        return chan.value

    @file_feed.tostring
    def file_feed(self, chan):
        return chan.value

    def initialise(self):
        pass

    def terminate(self):
        pass

    def _file_event(self, file_path):
        """" This function gets notified about files begin loaded """
        self.loaded_file = file_path

        self.canon = PropertiesCanon()

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
            result, seq = gcode.parse(self.loaded_file, self.canon, unitcode, initcode)

            if result > gcode.MIN_ERROR:
                msg = gcode.strerror(result)
                LOG.debug(f"Error in {self.loaded_file} line {seq - 1}\n{msg}")
        except Exception as e:
            LOG.debug(f"Error {e}")
        
        # clean up temp var file and the backup
        os.unlink(self.temp_parameter_file)
        os.unlink(self.temp_parameter_file + '.bak')

        file_name = self.loaded_file
        file_size = os.stat(self.loaded_file).st_size
        file_lines = self.canon.num_lines
        
        tool_calls = self.canon.tool_calls
        
        g0 = sum(self.dist(l[0][:3], l[1][:3]) for l in self.canon.traverse)
        g1 = (sum(self.dist(l[0][:3], l[1][:3]) for l in self.canon.feed) +
            sum(self.dist(l[0][:3], l[1][:3]) for l in self.canon.arcfeed))
        
        self.file_name.setValue(file_name)
        self.file_size.setValue(file_size)
        self.file_lines.setValue(file_lines)
        
        self.tool_calls_num.setValue(tool_calls)
        
        self.file_rapid_distance.setValue(g0)
        self.file_feed_distance.setValue(g1)
        
        self.file_work_planes.setValue(self.canon.work_planes)
        self.file_rigid_taps.setValue(self.canon.rigid_taps)
        self.file_offsets.setValue(self.canon.g5x_offset_dict)

    def calc_distance(self):

        mf = 100.0
        
        g0 = sum(self.dist(l[0][:3], l[1][:3]) for l in self.canon.traverse)
        
        g1 = (sum(self.dist(l[0][:3], l[1][:3]) for l in self.canon.feed) +
            sum(self.dist(l[0][:3], l[1][:3]) for l in self.canon.arcfeed))
        
        
        # gt = (sum(self.dist(l[0][:3], l[1][:3])/min(mf, l[1][0]) for l in self.canon.feed) +
        #     sum(self.dist(l[0][:3], l[1][:3])/min(mf, l[1][0])  for l in self.canon.arcfeed) +
        #     sum(self.dist(l[0][:3], l[1][:3])/mf  for l in self.canon.traverse) +
        #     self.canon.dwell_time
        #     )
        #
        # LOG.debug(f"path time {gt} secconds")        
        #
        # min_extents = self.from_internal_units(self.canon.min_extents, conv)
        # max_extents = self.from_internal_units(self.canon.max_extents, conv)
        #
        # for (i, c) in enumerate("xyz"):
        #     a = min_extents[i]
        #     b = max_extents[i]
        #     if a != b:
        #             props[c] = ("%(a)f to %(b)f = %(diff)f %(units)s").replace("%f", fmt) % {'a': a, 'b': b, 'diff': b-a, 'units': units}
        # # properties(root_window, _("G-Code Properties"), property_names, props)
        # pprint.pprint(props)

    def dist(self, xxx, xxx_1):
        (x,y,z) = xxx  # todo changeme
        (p,q,r) = xxx_1  # todo changeme
        return ((x-p)**2 + (y-q)**2 + (z-r)**2) ** .5
    
    def from_internal_units(self, pos, unit=None):
        if unit is None:
            unit = s.linear_units
        lu = (unit or 1) * 25.4
    
        lus = [lu, lu, lu, 1, 1, 1, lu, lu, lu]
        return [a*b for a, b in zip(pos, lus)]
    
    def from_internal_linear_unit(self, v, unit=None):
        if unit is None:
            unit = s.linear_units
        lu = (unit or 1) * 25.4
        return v*lu

class PropertiesCanon(BaseCanon):

    def __init__(self):
        self.num_lines = 0
        self.tool_calls = 0
        
        # traverse list - [line number, [start position], [end position], [tlo x, tlo y, tlo z]]
        self.traverse = []
        
        # feed list - [line number, [start position], [end position], feedrate, [tlo x, tlo y, tlo z]]
        self.feed = []
        
        # arcfeed list - [line number, [start position], [end position], feedrate, [tlo x, tlo y, tlo z]]
        self.arcfeed = []
        
        # dwell list - [line number, color, pos x, pos y, pos z, plane]
        self.dwells = []
                
        self.work_planes = []    
                    
        self.rigid_taps = []
            

        self.feedrate = 1
        self.dwell_time = 0

        self.seq_num = -1
        self.last_pos = (0,) * 9

        self.first_move = True
        self.in_arc = False
        self.suppress = 0

        self.plane = 1
        
        self.arcdivision = 64

        # extents
        self.min_extents = [9e99, 9e99, 9e99]
        self.max_extents = [-9e99, -9e99, -9e99]
        self.min_extents_notool = [9e99, 9e99, 9e99]
        self.max_extents_notool = [-9e99, -9e99, -9e99]

        # tool length offsets
        self.tlo_x = 0.0
        self.tlo_y = 0.0
        self.tlo_z = 0.0
        self.tlo_a = 0.0
        self.tlo_b = 0.0
        self.tlo_c = 0.0
        self.tlo_u = 0.0
        self.tlo_v = 0.0
        self.tlo_w = 0.0

        self.tool_offsets = (0.0,) * 9

        # G92/G52 offsets
        self.g92_offset_x = 0.0
        self.g92_offset_y = 0.0
        self.g92_offset_z = 0.0
        self.g92_offset_a = 0.0
        self.g92_offset_b = 0.0
        self.g92_offset_c = 0.0
        self.g92_offset_u = 0.0
        self.g92_offset_v = 0.0
        self.g92_offset_w = 0.0

        # g5x offsets
        self.g5x_offset_x = 0.0
        self.g5x_offset_y = 0.0
        self.g5x_offset_z = 0.0
        self.g5x_offset_a = 0.0
        self.g5x_offset_b = 0.0
        self.g5x_offset_c = 0.0
        self.g5x_offset_u = 0.0
        self.g5x_offset_v = 0.0
        self.g5x_offset_w = 0.0

        self.g5x_offset_dict = dict()

        # XY rotation (degrees)
        self.rotation_xy = 0
        self.rotation_cos = 1
        self.rotation_sin = 0
    
    def set_g5x_offset(self, offset, x, y, z, a, b, c, u, v, w):
        try:
            self.g5x_offset_dict[str(offset)] = (x, y, z, a, b, c, u, v, w)
        except Exception as e:
            LOG.debug(f"straight_traverse: {e}")

    def set_g92_offset(self, x, y, z, a, b, c, u, v, w):
        
        self.g92_offset_x = x
        self.g92_offset_y = y
        self.g92_offset_z = z
        self.g92_offset_a = z
        self.g92_offset_b = b
        self.g92_offset_c = c
        self.g92_offset_u = u
        self.g92_offset_v = v
        self.g92_offset_w = w

    def set_plane(self, plane):
        self.work_planes.append(plane)

    def set_feed_rate(self, arg):
        pass
        # print(("set feed rate", arg))

    def comment(self, comment):
        pass
        # print(("#", comment))

    def straight_traverse(self, x, y, z, a, b, c, u, v, w):
        try:
            if self.suppress > 0:
                 return
        
            pos = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)
            if not self.first_move:
                self.traverse.append([self.last_pos, pos])
    
            self.last_pos = pos
        except Exception as e:
            LOG.debug(f"straight_traverse: {e}")

    def straight_feed(self, x, y, z, a, b, c, u, v, w):
        try:
            if self.suppress > 0:
                return
    
            self.first_move = False
            pos = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)
    
            self.feed.append([self.last_pos, pos])
            self.last_pos = pos
        except Exception as e:
            LOG.debug(f"straight_feed: {e}")

    def dwell(self, arg):
        if arg < .1:
            print(("dwell %f ms" % (1000 * arg)))
        else:
            print(("dwell %f seconds" % arg))

    def arc_feed(self, end_x, end_y, center_x, center_y, rot, end_z, a, b, c, u, v, w):
        try:
            if self.suppress > 0:
                return
    
            self.first_move = False
            self.in_arc = True
            try:
                # this self.lo goes straight into the c code, cannot be changed
                self.lo = tuple(self.last_pos)
                segs = gcode.arc_to_segments(self, end_x, end_y, center_x, center_y,
                                             rot, end_z, a, b, c, u, v, w, self.arcdivision)
                self.straight_arcsegments(segs)
            finally:
                self.in_arc = False
        except Exception as e:
            LOG.debug(f"straight_feed: {e}")

    def get_axis_mask(self):
        return 7  # XYZ
    
    def rigid_tap(self, x, y, z):
        try:
            if self.suppress > 0:
                return
            
            self.rigid_taps.append((x, y, z))
            
            self.first_move = False
            pos = self.rotate_and_translate(x, y, z, 0, 0, 0, 0, 0, 0)[:3]
            pos += self.last_pos[3:]
        
            self.feed.append([self.last_pos, pos])
            
        except Exception as e:
            LOG.debug(f"straight_feed: {e}")

    def change_tool(self, pocket):
        if pocket != -1:
            self.tool_calls += 1
        # print(("pocket", pocket))

    def next_line(self, st):
        self.num_lines += 1
        
        # state attributes
        # 'block', 'cutter_side', 'distance_mode', 'feed_mode', 'feed_rate',
        # 'flood', 'gcodes', 'mcodes', 'mist', 'motion_mode', 'origin', 'units',
        # 'overrides', 'path_mode', 'plane', 'retract_mode', 'sequence_number',
        # 'speed', 'spindle', 'stopping', 'tool_length_offset', 'toolchange',
        # print(("state", st))
        # print(("seq", st.sequence_number))
        # print(("MCODES", st.mcodes))
        # print(("TOOLCHANGE", st.toolchange))
