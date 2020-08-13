class BaseGenerator(object):
    def __init__(self):
        self.wcs = ''
        self.speed = 0.
        self.feed = 0.
        self.z_feed = 0.
        self.z_clear = 0.
        self.z_start = 0.
        self.z_end = 0.
        self.tool = 0
        self.coolant = ''
        self.unit = 'G20'

    def preamble(self):
        output = [
            'G90 G94 G17',
            self.wcs,
            self.unit,
            'G53 G0 Z0',
            'T%i M6 G43' % self.tool,
            'S%.4f' % abs(self.speed)
        ]

        output.append('M4') if self.speed < 0 else output.append('M3')

        if self.coolant:
            output.append(self.coolant)

        output.append('F%.4f' % self.feed)

        return '\n'.join(output)

    def epilog(self):
        output = []
        if self.coolant:
            output.append('M9')
        output.append('G53 G0 Z0')
        output.append('M30')
        output.append('%')

        return '\n'.join(output)
