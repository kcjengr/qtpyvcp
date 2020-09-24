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

import linuxcnc

from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import DataPlugin, DataChannel

INFO = Info()

INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))

MAX_LINEAR_VELOCITY = bool(INIFILE.find("TRAJ", "MAX_LINEAR_VELOCITY"))
MAX_ANGULAR_VELOCITY = bool(INIFILE.find("TRAJ", "MAX_ANGULAR_VELOCITY"))

MACHINE_UNITS = 2 if INFO.getIsMachineMetric() else 1

class GCodeProperties(DataPlugin):
    """Clock Plugin"""
    def __init__(self):
        super(GCodeProperties, self).__init__()

        self.loaded_file = None

    @DataChannel
    def name(self, chan):
        """The current file name.

        Args:
            None

        Returns:
            The current open file name as a string.

        Channel syntax::

            gcode_properties:name

        """

        if not self.loaded_file:
            return "No file loaded"

        chan.setValue(os.path.basename(self.loaded_file))

        return chan.value

    @DataChannel
    def size(self, chan):
        """The current file size.

        Args:
            None

        Returns:
            The current file size in bytes

        Channel syntax::

            gcode_properties:size

        """

        if not self.loaded_file:
            return 0

        chan.setValue(os.stat(self.loaded_file).st_size)

        return chan.value

    @DataChannel
    def rapids(self, chan):
        """The current file rapis distance.

        Args:
            None

        Returns:
            The current file rapis distance in machine units

        Channel syntax::

            gcpde_properties:rapids

        """

        if not self.loaded_file:
            return 0.0

        if MACHINE_UNITS == 2:
            conv = 1
            units = "mm"
            fmt = "%.3f"
        else:
            conv = 1/25.4
            units = "in"
            fmt = "%.4f"

    @DataChannel
    def lines(self, chan):
        """The current number of lines.

        Args:
            None

        Returns:
            The current number of lines the file has

        Channel syntax::

            gcode_properties:lines

        """

        if not self.loaded_file:
            return 0

        return chan.value

    @DataChannel
    def time(self, chan):
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
            return 0

        return chan.value

    @time.tostring
    def time(self, chan, format="%I:%M:%S %p"):
        return chan.value.strftime(format)

    # @DataChannel
    # def x_limit(self, chan):
    #     """The current date, updated every second.
    #
    #     Args:
    #         format (str) : Format spec. Defaults to ``%m/%d/%Y``.
    #             See http://strftime.org for supported formats.
    #
    #     Returns:
    #         The current date as a formatted string. Default MM/DD/YYYY
    #
    #     Channel syntax::
    #
    #         clock:date
    #         clock:date?string
    #         clock:date?string&format=%Y
    #
    #     """
    #     return chan.value

    @DataChannel
    def feed(self, chan):
        """The current file run distance.

        Args:
            None

        Returns:
            The distance the machine will run with the loaded file

        Channel syntax::

            gcode_properties:feed

        """
        return chan.value

    # @size.tostring
    # def date(self, chan, format="%m/%d/%Y"):
    #     return chan.value.strftime(format)

#     def gcode_properties(self):
#         props = {}
#         if not self.loaded_file:
#             props['name'] = _("No file loaded")
#         else:
#             ext = os.path.splitext(self.loaded_file)[1]
#             program_filter = None
#             if ext:
#                 program_filter = inifile.find("FILTER", ext[1:])
#             name = os.path.basename(self.loaded_file)
#             if program_filter:
#                 props['name'] = _("generated from %s") % name
#             else:
#                 props['name'] = name
#
#             size = os.stat(self.loaded_file).st_size
#             lines = int(widgets.text.index("end").split(".")[0])-2
#             props['size'] = _("%(size)s bytes\n%(lines)s gcode lines") % {'size': size, 'lines': lines}
#
#             if vars.metric.get():
#                 conv = 1
#                 units = _("mm")
#                 fmt = "%.3f"
#             else:
#                 conv = 1/25.4
#                 units = _("in")
#                 fmt = "%.4f"
#
#             mf = vars.max_speed.get()
#             #print o.canon.traverse[0]
#
#             g0 = sum(dist(l[1][:3], l[2][:3]) for l in o.canon.traverse)
#             g1 = (sum(dist(l[1][:3], l[2][:3]) for l in o.canon.feed) +
#                 sum(dist(l[1][:3], l[2][:3]) for l in o.canon.arcfeed))
#             gt = (sum(dist(l[1][:3], l[2][:3])/min(mf, l[3]) for l in o.canon.feed) +
#                 sum(dist(l[1][:3], l[2][:3])/min(mf, l[3])  for l in o.canon.arcfeed) +
#                 sum(dist(l[1][:3], l[2][:3])/mf  for l in o.canon.traverse) +
#                 o.canon.dwell_time
#                 )
#
#             props['g0'] = "%f %s".replace("%f", fmt) % (from_internal_linear_unit(g0, conv), units)
#             props['g1'] = "%f %s".replace("%f", fmt) % (from_internal_linear_unit(g1, conv), units)
#             if gt > 120:
#                 props['run'] = _("%.1f minutes") % (gt/60)
#             else:
#                 props['run'] = _("%d seconds") % (int(gt))
#
#             min_extents = from_internal_units(o.canon.min_extents, conv)
#             max_extents = from_internal_units(o.canon.max_extents, conv)
#             for (i, c) in enumerate("xyz"):
#                 a = min_extents[i]
#                 b = max_extents[i]
#                 if a != b:
#                     props[c] = _("%(a)f to %(b)f = %(diff)f %(units)s").replace("%f", fmt) % {'a': a, 'b': b, 'diff': b-a, 'units': units}
#         properties(root_window, _("G-Code Properties"), property_names, props)
#
#     def initialise(self):
#         pass
#
#     def terminate(self):
#         pass
#
# def dist(xxx_todo_changeme, xxx_todo_changeme1):
#     (x,y,z) = xxx_todo_changeme
#     (p,q,r) = xxx_todo_changeme1
#     return ((x-p)**2 + (y-q)**2 + (z-r)**2) ** .5
#
# def from_internal_units(pos, unit=None):
#     if unit is None:
#         unit = s.linear_units
#     lu = (unit or 1) * 25.4
#
#     lus = [lu, lu, lu, 1, 1, 1, lu, lu, lu]
#     return [a*b for a, b in zip(pos, lus)]
#
# def from_internal_linear_unit(v, unit=None):
#     if unit is None:
#         unit = s.linear_units
#     lu = (unit or 1) * 25.4
#     return v*lu