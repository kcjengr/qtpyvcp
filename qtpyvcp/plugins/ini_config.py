
import os
import linuxcnc


class INIConfig(object):

    def __init__(self, ini_file=None):

        self.ini_file = os.path.abspath(ini_file or
                                        os.environ.get("INI_FILE_NAME"))
        self.config_dir = os.path.dirname(self.ini_file)

        self.ini = linuxcnc.ini(self.ini_file)

        self._linear_units = None

        self.display = _display(self.ini, 'display')


class INISection(object):
    def __init__(self, ini, section):
        self.ini = ini
        self.section = section

    def __getattr__(self, item):
        try:
            return getattr(self, item.lower())
        except:
            print 'error'
            val = self.ini.find(self.section.upper(), item.upper())
            setattr(self, item.lower(), val)
            return val


class _display(INISection):
    def __init__(self, ini, section):
        super(_display, self).__init__(ini, section)

        self.ini = ini
        self._machine = None

    @property
    def machine(self):
        if self._machine is None:
            self._machine = self.ini.find('EMC', 'MACHINE') or "QtPyVCP Machine"
        return self._machine

ini = INIConfig('/media/data/dev/cnc/qtpyvcp/sim/xyz.ini')

print ini
print ini.display.machine
print ini.display.display
print ini.display.display
print ini.display.display