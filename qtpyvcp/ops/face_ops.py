
import math

from .base_op import BaseGenerator


class FaceOps(BaseGenerator):
    def __init__(self):
        super(FaceOps, self).__init__()
        self.tool_diameter = 0.
        self.step_over = 0.
        self.step_down = 0.
        self.x_start = self.x_end = 0.
        self.y_start = self.y_end = 0.

    def face(self):
        width = abs(self.y_end - self.y_start)
        depth = abs(self.z_end - self.z_start)

        num_step_down = abs(int(math.ceil(depth / self.step_down)))
        num_step_over = abs(int(math.ceil(width / self.step_over)))

        step_over = width / num_step_over
        step_down = depth / num_step_down

        tool_radius = self.tool_diameter / 2
        ramp_radius = self.retract + step_down

        x_start = self.x_start - tool_radius - ramp_radius
        y_start = self.y_start + tool_radius - step_over
        z_start = self.z_start

        z = z_start
        gcode = self._start_op()
        step_over = - step_over
        for i in range(num_step_down):
            x = self.x_end
            y = y_start
            gcode.append('G0 X{:.4f} Y{:.4f}'.format(x_start, y_start))
            gcode.append('G0 Z{:.4f}'.format(z + self.retract))
            gcode.append('G18 G2 X{:.4f} Z{:.4f} I{:.4f}'
                         .format(x_start + ramp_radius, z + self.retract - ramp_radius, ramp_radius))

            z -= step_down

            gcode.append('G1 X{:.4f}'.format(x))
            for _ in range(num_step_over - 1):
                y += step_over
                if x == self.x_end:
                    gcode.append('G17 G2 Y{:.4f} J{:.4f}'.format(y, step_over / 2))
                    x = self.x_start
                else:
                    gcode.append('G17 G3 Y{:.4f} J{:.4f}'.format(y, step_over / 2))
                    x = self.x_end

                gcode.append('G1 X{:.4f}'.format(x))

            if x == self.x_start:
                gcode.append('G18 G3 X{:.4f} Z{:.4f} K{:.4f}'.format(x - ramp_radius, z + ramp_radius, ramp_radius))
            else:
                gcode.append('G18 G2 X{:.4f} Z{:.4f} K{:.4f}'.format(x + ramp_radius, z + ramp_radius, ramp_radius))

            if i < (num_step_down - 1):
                gcode.append('G0 Z{:.4f}'.format(self.z_clear))

        gcode.extend(self._end_op())

        return gcode
