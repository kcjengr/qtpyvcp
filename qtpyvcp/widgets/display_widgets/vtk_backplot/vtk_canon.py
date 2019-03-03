#    This is a component of AXIS, a front-end for emc
#    Copyright 2004, 2005, 2006 Jeff Epler <jepler@unpythonic.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import math
import gcode


class VTKCanon(object):
    lineno = -1

    def __init__(self, geometry, is_foam=0):

        # traverse list - [line number, [start position], [end position], [tlo x, tlo y, tlo z]]
        self.traverse = []
        self.traverse_append = self.traverse.append

        # feed list - [line number, [start position], [end position], feedrate, [tlo x, tlo y, tlo z]]
        self.feed = []
        self.feed_append = self.feed.append

        # arcfeed list - [line number, [start position], [end position], feedrate, [tlo x, tlo y, tlo z]]
        self.arcfeed = []
        self.arcfeed_append = self.arcfeed.append

        # dwell list - [line number, color, pos x, pos y, pos z, plane]
        self.dwells = []
        self.dwells_append = self.dwells.append

        self.feedrate = 1
        self.dwell_time = 0
        self.lo = (0,) * 9

        self.first_move = True
        self.in_arc = 0
        self.suppress = 0

        self.plane = 1
        self.arcdivision = 64

        # extents
        self.min_extents = [9e99, 9e99, 9e99]
        self.max_extents = [-9e99, -9e99, -9e99]
        self.min_extents_notool = [9e99, 9e99, 9e99]
        self.max_extents_notool = [-9e99, -9e99, -9e99]

        # tool length offsets
        self.tool_offset_x = 0
        self.tool_offset_y = 0
        self.tool_offset_z = 0
        self.tool_offset_a = 0
        self.tool_offset_b = 0
        self.tool_offset_c = 0
        self.tool_offset_u = 0
        self.tool_offset_v = 0
        self.tool_offset_w = 0

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
        self.g5x_index = 1

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

        # XY rotation (degrees)
        self.rotation_xy = 0
        self.rotation_cos = 1
        self.rotation_sin = 0

        self.is_foam = is_foam
        self.foam_z = 0
        self.foam_w = 1.5
        self.notify = 0
        self.notify_message = ""
        self.highlight_line = None

    def comment(self, arg):
        if arg.startswith("AXIS,"):
            parts = arg.split(",")
            command = parts[1]

            if command == "stop":
                raise KeyboardInterrupt

            if command == "hide":
                self.suppress += 1

            if command == "show":
                self.suppress -= 1

            if command == "XY_Z_POS":
                if len(parts) > 2:
                    try:
                        self.foam_z = float(parts[2])
                        if 210 in self.state.gcodes:
                            self.foam_z = self.foam_z / 25.4
                    except:
                        self.foam_z = 5.0 / 25.4

            if command == "UV_Z_POS":
                if len(parts) > 2:
                    try:
                        self.foam_w = float(parts[2])
                        if 210 in self.state.gcodes:
                            self.foam_w = self.foam_w / 25.4
                    except:
                        self.foam_w = 30.0

            if command == "notify":
                self.notify = self.notify + 1
                self.notify_message = "(AXIS,notify):" + str(self.notify)
                if len(parts) > 2:
                    if len(parts[2]):
                        self.notify_message = parts[2]

    def message(self, message):
        pass

    def check_abort(self):
        pass

    def next_line(self, st):
        self.state = st
        self.lineno = self.state.sequence_number

    def calc_extents(self):
        self.min_extents, self.max_extents, self.min_extents_notool, \
        self.max_extents_notool = gcode.calc_extents(self.arcfeed, self.feed, self.traverse)

    def rotate_and_translate(self, x, y, z, a, b, c, u, v, w):
        x += self.g92_offset_x
        y += self.g92_offset_y
        z += self.g92_offset_z
        a += self.g92_offset_a
        b += self.g92_offset_b
        c += self.g92_offset_c
        u += self.g92_offset_u
        v += self.g92_offset_v
        w += self.g92_offset_w

        if self.rotation_xy:
            x = x * self.rotation_cos - y * self.rotation_sin
            y = x * self.rotation_sin + y * self.rotation_cos

        x += self.g5x_offset_x
        y += self.g5x_offset_y
        z += self.g5x_offset_z
        a += self.g5x_offset_a
        b += self.g5x_offset_b
        c += self.g5x_offset_c
        u += self.g5x_offset_u
        v += self.g5x_offset_v
        w += self.g5x_offset_w

        return [x, y, z, a, b, c, u, v, w]

    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):
        self.g5x_index = index
        self.g5x_offset_x = x
        self.g5x_offset_y = y
        self.g5x_offset_z = z
        self.g5x_offset_a = a
        self.g5x_offset_b = b
        self.g5x_offset_c = c
        self.g5x_offset_u = u
        self.g5x_offset_v = v
        self.g5x_offset_w = w

    def set_g92_offset(self, x, y, z, a, b, c, u, v, w):
        self.g92_offset_x = x
        self.g92_offset_y = y
        self.g92_offset_z = z
        self.g92_offset_a = a
        self.g92_offset_b = b
        self.g92_offset_c = c
        self.g92_offset_u = u
        self.g92_offset_v = v
        self.g92_offset_w = w

    def set_xy_rotation(self, rotation):
        self.rotation_xy = rotation
        theta = math.radians(rotation)
        self.rotation_cos = math.cos(theta)
        self.rotation_sin = math.sin(theta)

    def tool_offset(self, xo, yo, zo, ao, bo, co, uo, vo, wo):
        self.first_move = True
        x, y, z, a, b, c, u, v, w = self.lo

        self.lo = (
            x - xo + self.tool_offset_x, y - yo + self.tool_offset_y, z - zo + self.tool_offset_z,
            a - ao + self.tool_offset_a, b - bo + self.tool_offset_b, c - bo + self.tool_offset_b,
            u - uo + self.tool_offset_u, v - vo + self.tool_offset_v, w - wo + self.tool_offset_w)

        self.tool_offset_x = xo
        self.tool_offset_y = yo
        self.tool_offset_z = zo
        self.tool_offset_a = ao
        self.tool_offset_b = bo
        self.tool_offset_c = co
        self.tool_offset_u = uo
        self.tool_offset_v = vo
        self.tool_offset_w = wo

    def set_spindle_rate(self, speed):
        pass

    def set_feed_rate(self, feed_rate):
        self.feedrate = feed_rate / 60.

    def select_plane(self, plane):
        pass

    def change_tool(self, arg):
        self.first_move = True

    def straight_traverse(self, x, y, z, a, b, c, u, v, w):
        if self.suppress > 0:
            return
        pos = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)
        if not self.first_move:
            self.traverse_append(
                (self.lineno, self.lo, pos, [self.tool_offset_x, self.tool_offset_y, self.tool_offset_z]))
        self.lo = pos

    def rigid_tap(self, x, y, z):
        if self.suppress > 0:
            return
        self.first_move = False
        l = self.rotate_and_translate(x, y, z, 0, 0, 0, 0, 0, 0)[:3]
        l += [self.lo[3], self.lo[4], self.lo[5],
              self.lo[6], self.lo[7], self.lo[8]]
        self.feed_append((self.lineno, self.lo, l, self.feedrate,
                          [self.tool_offset_x, self.tool_offset_y, self.tool_offset_z]))
        #        self.dwells_append((self.lineno, self.colors['dwell'], x + self.offset_x, y + self.offset_y, z + self.offset_z, 0))
        self.feed_append((self.lineno, l, self.lo, self.feedrate,
                          [self.tool_offset_x, self.tool_offset_y, self.tool_offset_z]))

    def set_plane(self, plane):
        print "setting plane: ", plane
        self.plane = plane

    def arc_feed(self, x1, y1, cx, cy, rot, z1, a, b, c, u, v, w):
        if self.suppress > 0:
            return
        self.first_move = False
        self.in_arc = True
        try:
            self.lo = tuple(self.lo)
            segs = gcode.arc_to_segments(self, x1, y1, cx, cy, rot, z1, a, b, c, v, w, self.arcdivision)
            self.straight_arcsegments(segs)
        finally:
            self.in_arc = False

    def straight_arcsegments(self, segs):
        self.first_move = False
        lo = self.lo
        lineno = self.lineno
        feedrate = self.feedrate
        to = [self.tool_offset_x, self.tool_offset_y, self.tool_offset_z]
        append = self.arcfeed_append
        for l in segs:
            append((lineno, lo, l, feedrate, to))
            lo = l
        self.lo = lo

    def straight_feed(self, x, y, z, a, b, c, u, v, w):
        if self.suppress > 0: return
        self.first_move = False
        l = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)
        self.feed_append((self.lineno, self.lo, l, self.feedrate,
                          [self.tool_offset_x, self.tool_offset_y, self.tool_offset_z]))
        self.lo = l

    straight_probe = straight_feed

    def user_defined_function(self, i, p, q):
        if self.suppress > 0: return
        color = self.colors['m1xx']
        self.dwells_append((self.lineno, color, self.lo[0], self.lo[1],
                            self.lo[2], self.state.plane / 10 - 17))

    def dwell(self, arg):
        if self.suppress > 0:
            return

        self.dwell_time += arg
        color = self.colors['dwell']
        self.dwells_append((self.lineno, color, self.lo[0], self.lo[1],
                            self.lo[2], self.state.plane / 10 - 17))


class PrintCanon:
    def set_g5x_offset(self, *args):
        print "set_g5x_offset", args

    def set_g92_offset(self, *args):
        print "set_g92_offset", args

    def next_line(self, state):
        print "next_line", state.sequence_number
        self.state = state

    def set_plane(self, plane):
        print "set plane", plane

    def set_feed_rate(self, arg):
        print "set feed rate", arg

    def comment(self, arg):
        print "#", arg

    def straight_traverse(self, *args):
        print "straight_traverse %.4g %.4g %.4g  %.4g %.4g %.4g" % args

    def straight_feed(self, *args):
        print "straight_feed %.4g %.4g %.4g  %.4g %.4g %.4g" % args

    def dwell(self, arg):
        if arg < .1:
            print "dwell %f ms" % (1000 * arg)
        else:
            print "dwell %f seconds" % arg

    def arc_feed(self, *args):
        print "arc_feed %.4g %.4g  %.4g %.4g %.4g  %.4g  %.4g %.4g %.4g" % args


class StatMixin:
    def __init__(self, s, r):
        self.s = s
        self.tools = list(s.tool_table)
        self.random = r

    def change_tool(self, pocket):
        if self.random:
            self.tools[0], self.tools[pocket] = self.tools[pocket], self.tools[
                0]
        elif pocket == 0:
            self.tools[
                0] = -1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
        else:
            self.tools[0] = self.tools[pocket]

    def get_tool(self, pocket):
        if pocket >= 0 and pocket < len(self.tools):
            return tuple(self.tools[pocket])
        return -1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0

    def get_external_angular_units(self):
        return self.s.angular_units or 1.0

    def get_external_length_units(self):
        return self.s.linear_units or 1.0

    def get_axis_mask(self):
        return self.s.axis_mask

    def get_block_delete(self):
        return self.s.block_delete

