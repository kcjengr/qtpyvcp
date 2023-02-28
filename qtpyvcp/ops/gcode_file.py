class GCodeFile(object):
    """
    This class maintains a list of operations to be written to the gcode file.
    Each gcode operation inserts its op into the ops list. Each op
    is responsible for setting up its environment, however, this class will add the
    preamble and epilog to the beginning and end of the gcode file respectively.

    Calling write_to_file('filename.ngc') will write all operations along with the
    preamble and epilog to the given file name, creating it if not available and
    overwriting it if it already exists.

    Calling to_string will return the gcode file as a sting.
    """
    def __init__(self):
        self.ops = []

        self.preamble = ['G90 G94 G17 G91.1']
        self.epilog = ['G53 G0 Z0', 'M30', '%']
        self.starting_line_number = 10
        self.line_number_stride = 10

    def gcode(self):
        output = []

        output.extend(self.preamble)
        for op in self.ops:
            output.extend(op)
        output.extend(self.epilog)

        line_number = self.starting_line_number
        for i in range(len(output)):
            output[i] = 'N{:d} {}'.format(line_number, output[i])
            line_number += self.line_number_stride

        return output

    def to_string(self):
        return '\n'.join(self.gcode())

    def write_to_file(self, filename):
        f = open(filename, 'w')
        try:
            f.write(self.to_string())
        finally:
            f.close()
