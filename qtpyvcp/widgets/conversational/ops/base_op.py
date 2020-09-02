class BaseGenerator(object):
    """
    This class handles the common start and end procedures for an operation.
    Before an operation the _start_op funtion can be called to set up the
    tool, spindle rpm, dir, WCS, coolant, and feed rate.

    After the operation the _end_op function can be called to turn off the coolant
    if enabled, and return the Z axis to the specified clearance height.
    """
    def __init__(self):
        self.wcs = ''
        self.coolant = ''
        self.units = ''
        self.tool_number = 0
        self.spindle_rpm = 0.
        self.spindle_dir = 'cw'
        self.z_start = 0.
        self.z_end = 0.
        self.retract = 0.
        self.z_feed = 0.
        self.z_clear = 0.
        self.xy_feed = 0.

    def _start_op(self):
        gcode = [
            'G20' if self.units.lower() == 'in' else 'G21',
            'T%i M6 G43' % self.tool_number,
            'S%.4f' % self.spindle_rpm,
            'M4' if self.spindle_dir.lower() == 'ccw' else 'M3',
            self.wcs,
            'F%.4f' % self.xy_feed
        ]

        if self.coolant.lower() == 'mist':
            gcode.append('M7')
        elif self.coolant.lower() == 'flood':
            gcode.append('M8')

        return gcode

    def _end_op(self):
        gcode = []
        if self.coolant.strip() != '':
            gcode.append('M9')
        gcode.append('G0 Z%.4f' % self.z_clear)
        return gcode
