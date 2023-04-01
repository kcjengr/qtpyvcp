

import math

from .base_op import BaseGenerator


class DrillOps(BaseGenerator):
    """This class generates GCode for drilling/tapping cycles.
        The canned drilling cycles G81 (drill), G74 (left hand tap),
        G84 (right hand tap), G82 (dwell), G83 (peck), and G73
        (chip-breaking), as well as left and right hand rigid tapping cycles
        are all supported.

        The tapping cycle is intended for tapping with a floating chuck
        and dwell at the bottom of the hole.

        Rigid tapping is designed to be used with spindle synchronized motion
        with return.

        http://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g33.1

        Tapping cycles will automatically set the z feed based on the
        given spindle RPM (speed), and thread pitch (1/TPI). If the
        spindle RPM is positive, a right hand tapping operation (G84)
        will be performed. If the spindle RPM is negative, a left hand
        tapping operation (G74) will be performed.

        The add_hole_circle method will add the x, y positions for
        a bolt hole circle. Starting at the given angle, it will calculate
        the x, y positions along a circle of a given diameter for the number
        of holes specified and add them to the list of hole locations.
        After the bolt hole locations have been added, you can elect to run
        a drill, tap, rigid tap, peck, dwell, or chip-breaking cycle.

        Example:
            # This example is for demonstration purposes only and should not be
            # run on your CNC machine.
            f = GCodeFile()
            drill = DrillOps()
            drill.wcs = 'G55'
            drill.unit = 'G20'
            drill.xy_feed = 60
            drill.coolant = 'M8'
            drill.z_clear = 0.1
            drill.z_start = 0.02
            drill.z_feed = 5
            # Generate drill locations for 7 holes around a 5 in. diameter circle.
            # The circle is centered on the midpoint of the material at (2.5, 2.5) with
            # (0, 0) being the bottom left corner of the part. Use a 40 degree start
            # angle offset.
            drill.add_hole_circle(7, 5, (2.5, 2.5), 40)
            # Add another hole at the center of the circle
            drill.holes.append((2.5, 2.5))
            # Carbide Spot Drill 90 Degree Point, 1/4 in. Size
            drill.tool_number = 1
            # Set the spindle RPM for 1/4 spot drill
            drill.spindle_rpm = 1600
            # Set the feed rate for 1/4 spotting drill
            drill.z_feed = 4.8
            # Drill 1/8 in. into the material
            drill.z_end = -1 / 8
            # Use a dwell cycle for spotting with a dwell time of 0.5 seconds.
            f.ops.append(drill.dwell(0.5))
            # No. 7 High Speed Steel Spiral Flute
            drill.tool_number = 2
            # Set the spindle RPM for #7 HSS twist drill
            drill.spindle_rpm = 1600
            # Set the feed rate for #7 HSS twist drill
            drill.z_feed = 4.8
            # Drill through the 1/2 in. material. Run the drill 0.050 in. below the bottom of the material
            drill.z_end = -0.5 - 0.050
            # create files for drill, peck, and chip breaking.
            f.ops.append(drill.drill())
            f.ops.append(drill.peck(0.1))
            # High-Speed Steel General Purpose Tap 1/4-20
            drill.tool_number = 3
            # Slow down the spindle speed for tapping.
            # The feed will be set automatically according to the thread pitch.
            drill.spindle_rpm = 480
            # Run tap 1/8 in. below the bottom of the hole.
            drill.z_end = -0.5 - 1 / 8
            # Use the tap cycle to tap a 1/4-20 right hand thread.
            # If you want to tap a left hand thread, negate the spindle speed.
            f.ops.append(drill.tap(1 / 20))
            print f.to_string()
            f.write_to_file('/tmp/drill.ngc')
        """
    def __init__(self):
        super(DrillOps, self).__init__()
        self.retract_mode = 'G98'
        self.holes = []

    def manual(self):
        gcode = self._start_op()
        if len(self.holes) > 0:
            for h in self.holes:
                gcode.append('G0 X{:.4f} Y{:.4f}'.format(h[0], h[1]))
                gcode.append('G0 Z{:.4f}'.format(self.z_start + self.retract))
                gcode.append('M0')
                if self.retract_mode == 'G98':
                    gcode.append('G0 Z{:.4f}'.format(self.z_clear))

        gcode.extend(self._end_op())
        return gcode

    def drill(self):
        return self._create_gcode('{} G81 R{:.4f} Z{:.4f} F{:.4f}'
                                  .format(self.retract_mode, self.z_start + self.retract, self.z_end, self.z_feed))

    def dwell(self, dwell_time=0.):
        return self._create_gcode('{} G82 R{:.4f} Z{:.4f} P{:.4f} F{:.4f}'
                                  .format(self.retract_mode, self.z_start + self.retract, self.z_end, dwell_time,
                                          self.z_feed))

    def peck(self, peck_dist=0.1):
        return self._create_gcode('{} G83 R{:.4f} Z{:.4f} Q{:.4f} F{:.4f}'
                                  .format(self.retract_mode, self.z_start + self.retract, self.z_end, peck_dist,
                                          self.z_feed))

    def chip_break(self, break_dist=0.1):
        return self._create_gcode('{} G73 R{:.4f} Z{:.4f} Q{:.4f} F{:.4f}'
                                  .format(self.retract_mode, self.z_start + self.retract, self.z_end, break_dist,
                                          self.z_feed))

    def tap(self, pitch):
        feed = abs(self.spindle_rpm * pitch)
        return self._create_gcode('{} {} R{:.4f} Z{:.4f} F{:.4f} S{:.4f}'
                                  .format(self.retract_mode, 'G74' if self.spindle_dir.lower() == 'ccw' else 'G84',
                                          self.z_start + self.retract,
                                          self.z_end, feed, abs(self.spindle_rpm)))

    def rigid_tap(self, pitch):
        return self._create_gcode('G33.1 Z{:.4f} K{:.4f}'.format(self.z_end, pitch))

    def add_hole_circle(self, num_holes, circle_diam, circle_center, start_angle=0):
        if num_holes == 0:
            return

        num_holes = abs(num_holes)
        curr_angle = start_angle
        angle_step = (360. / num_holes)

        for _ in range(0, num_holes):
            x = math.cos(math.radians(curr_angle)) * (circle_diam / 2.)
            y = math.sin(math.radians(curr_angle)) * (circle_diam / 2.)
            x += circle_center[0]
            y += circle_center[1]
            curr_angle += angle_step

            self.holes.append((x, y))

    def _create_gcode(self, op):
        gcode = self._start_op()
        if len(self.holes) > 0:
            gcode.append('G0 X{:.4f} Y{:.4f}'.format(self.holes[0][0], self.holes[0][1]))
            gcode.append('G0 Z{:.4f}'.format(self.z_clear))
            gcode.append(op)
            for h in self.holes[1:]:
                gcode.append('X{:.4f} Y{:.4f}'.format(h[0], h[1]))

        gcode.append('G80')
        gcode.extend(self._end_op())

        return gcode
