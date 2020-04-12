
import os
import ast
import ConfigParser

from qtpyvcp.utilities.logger import getLogger
log = getLogger(__name__)


class RuntimeConfig(object):
    def __init__(self, fname='~/.qtpyvcprc'):
        self.fname = fname
        self._cp = ConfigParser.RawConfigParser()
        self._cp.optionxform = str

        self.require_write = False

        self.getters = {
            bool: self.getBool,
            float: self.getFloat,
            int: self.getInt,
            list: self.getList,
            dict: self.getDict,
            str: self.getStr,
        }

    def read(self, fname=None):
        self.fname = os.path.abspath(os.path.expanduser(fname or self.fname))
        self._cp.read(self.fname)
        return self

    def write(self, fname=None):
        fname = fname or self.fname
        with open(fname, 'w') as fh:
            self._cp.write(fh)

    def get(self, section, option, default=None):
        try:
            typ = (type(default) if default is not None else str)
            getter = self.getters.get(typ)
            value = getter(section, option, default)
            return value
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            # Add the section and the option
            self.set(section, option, default)

        return default

    def set(self, section, option, value):
        try:
            self._cp.set(section, option, str(value))
        except ConfigParser.NoSectionError:
            # Add the section and the option
            self._cp.add_section(section)
            self._cp.set(section, option, str(value))

        self.require_write = True

    def getStr(self, section, option, default):
        return self._cp.get(section, option)

    def getFloat(self, section, option, default):
        value = self._cp.get(section, option)
        try:
            return float(value)
        except (ValueError, SyntaxError):
            return default

    def getInt(self, section, option, default):
        value = self._cp.get(section, option)
        try:
            return int(value)
        except (ValueError, SyntaxError):
            return default

    def getBool(self, section, option, default):
        value = self._cp.get(section, option)
        if value.lower() in ['1', 'true', 'yes', 'on']:
            return True
        elif value.lower() in ['0', 'false', 'no', 'off']:
            return False
        log.error('Non boolean value "{0}" for option [{1}] {2},'
            ' using default value of "{3}"'.format(value, section, option, default))
        return default

    def getList(self, section, option, default):
        value = self._cp.get(section, option)
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            log.error('"{0}" for option [{1}] {2} is not a valid list,'
                ' using default value of "{3}"'.format(value, section, option, default))
            return default

    def getDict(self, section, option, default):
        value = self._cp.get(section, option)
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            log.error('"{0}" for option [{1}] {2} is not a valid dict,'
                ' using default value of "{3}"'.format(value, section, option, default))
            return default

    def __enter__(self):
        self.read()
        return self

    def __exit__(self, type, value, traceback):
        if self.require_write:
            self.write()


if __name__ == "__main__":

    with RuntimeConfig() as rc:
        print rc.get('TEST', 'STR_VALUE', 'default')
        rc.set('TEST', 'VALUE', 10)

    with RuntimeConfig('~/.axis_preferences') as rc:
        print rc.get('DEFAULT', 'recentfiles', default=[])
