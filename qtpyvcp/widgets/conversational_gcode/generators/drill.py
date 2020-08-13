from __future__ import division
from base_generator import BaseGenerator

import math


class Drill(BaseGenerator):
    """This class generates GCode for drilling/tapping cycles.

    The canned drilling cycles G81 (drill), G74 (left hand tap),
    G84 (right hand tap), G82 (dwell), G83 (peck), and G73
    (chip-breaking), are all supported.

    The tapping cycle is intended for tapping with a floating chuck
    and dwell at the bottom of the hole.

    Tapping cycles will automatically set the z feed based on the
    given spindle RPM (speed), and thread pitch (1/TPI). If the
    spindle RPM is positive, a right hand tapping operation (G84)
    will be performed. If the spindle RPM is negative, a left hand
    tapping operation (G74) will be performed.

    The bolt_hole_circle_xy method will add the x, y positions for
    a bolt hole circle. Starting at the given angle, it will calculate
    the x, y positions along a circle of a given diameter for the number
    of holes specified and add them to the list of hole locations.

    After the bolt hole locations have been added, you can elect to run
    a drill, tap, peck, dwell, or chip-breaking cycle.

    Example:
        # This example is for demonstration purposes only and should not be
        # run on your CNC machine.

        def write_to_file(file_name, data):
            f = open(file_name, 'w')
            try:
                f.write(data)
            finally:
                f.close()

        drill = Drill()
        drill.wcs = 'G55'
        drill.unit = 'G20'
        drill.feed = 60
        drill.coolant = 'M8'
        drill.z_clear = 0.1
        drill.z_start = 0.02

        # Generate drill locations for 7 holes around a 5 in. diameter circle.
        # The circle is centered on the midpoint of the material at (2.5, 2.5) with
        # (0, 0) being the bottom left corner of the part. Use a 40 degree start
        # angle offset.
        drill.bolt_hole_circle_xy(7, 5, (2.5, 2.5), 40)
        # Add another hole at the center of the circle
        drill.hole_locations.append((2.5, 2.5))

        # Carbide Spot Drill 90 Degree Point, 1/4 in. Size
        drill.tool = 1
        # Set the spindle RPM for 1/4 spot drill
        drill.speed = 1600
        # Set the feed rate for 1/4 spotting drill
        drill.z_feed = 4.8
        # Drill 1/8 in. into the material
        drill.z_end = -1/8
        # Use a dwell cycle for spotting with a dwell time of 0.5 seconds.
        write_to_file('/tmp/spot.ngc', drill.dwell(0.5))

        # No. 7 High Speed Steel Spiral Flute
        drill.tool = 2
        # Set the spindle RPM for #7 HSS twist drill
        drill.speed = 1600
        # Set the feed rate for #7 HSS twist drill
        drill.z_feed = 4.8
        # Drill through the 1/2 in. material. Run the drill 0.050 in. below the bottom of the material
        drill.z_end = -0.5-0.050
        # create files for drill, peck, and chip breaking.
        write_to_file('/tmp/drill.ngc', drill.drill())
        write_to_file('/tmp/peck.ngc', drill.peck(0.1))
        write_to_file('/tmp/chip_break.ngc', drill.chip_break(0.1))

        # High-Speed Steel General Purpose Tap 1/4-20
        drill.tool = 3
        # Slow down the spindle speed for tapping.
        # The feed will be set automatically according to the thread pitch.
        drill.speed = 480
        # Run tap 1/8 in. below the bottom of the hole.
        drill.z_end = -0.5 - 1 / 8
        # Use the tap cycle to tap a 1/4-20 right hand thread.
        # If you want to tap a left hand thread, negate the spindle speed.
        write_to_file('/tmp/tap.ngc', drill.tap(1 / 20))
    """

    def __init__(self):
        super(Drill, self).__init__()
        self.hole_locations = []

    def drill(self):
        return self.build_gcode_('G98 G81 R%.4f Z%.4f F%.4f' % (self.z_start, self.z_end, self.z_feed))

    def dwell(self, dwell_time):
        return self.build_gcode_('G98 G82 R%.4f Z%.4f P%.4f F%.4f' %
                                 (self.z_start, self.z_end, dwell_time, self.z_feed))

    def peck(self, delta):
        return self.build_gcode_('G98 G83 R%.4f Z%.4f Q%.4f F%.4f' % (self.z_start, self.z_end, delta, self.z_feed))

    def chip_break(self, delta):
        return self.build_gcode_('G98 G73 R%.4f Z%.4f Q%.4f F%.4f' % (self.z_start,  self.z_end, delta, self.z_feed))

    def tap(self, pitch):
        self.z_feed = abs(self.speed * pitch)
        return self.build_gcode_('G98 %s R%.4f Z%.4f F%.4f S%.4f' % ('G74' if self.speed < 0. else 'G84',
                                  self.z_start,  self.z_end, self.z_feed, abs(self.speed)))

    def bolt_hole_circle_xy(self, num_holes, circle_diam, circle_center, start_angle=0):
        curr_angle = start_angle
        angle_step = (360. / num_holes)

        for _ in range(0, num_holes):
            x = math.cos(math.radians(curr_angle)) * (circle_diam / 2.)
            y = math.sin(math.radians(curr_angle)) * (circle_diam / 2.)
            x += circle_center[0]
            y += circle_center[1]
            curr_angle += angle_step

            self.hole_locations.append((x, y))

    def build_gcode_(self, cycle):
        return '\n'.join([
            self.preamble(),
            "G0 X%.4f Y%.4f" % (self.hole_locations[0][0], self.hole_locations[0][1]),
            "G0 Z%.4f" % self.z_clear,
            cycle,
            self.add_holes_(),
            'G80',
            self.epilog()
        ])

    def add_holes_(self):
        output = []
        for hole in self.hole_locations[1:]:
            output.append('X%.4f Y%.4f' % (hole[0], hole[1]))

        return '\n'.join(output)
