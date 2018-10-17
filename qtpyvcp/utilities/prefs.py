#!/usr/bin/env python

"""Persistent preferences manager using INI format .pref file.

Setting Preference::

   set("section", "option", "value", type)
   set("DROs", "dec_places", 4 , int)

Getting Preference::

   get("section", "option", "default_val", type)
   dro_places = get("DROs", "dec_places", 3, int)

"""

import os
import ast

import ConfigParser

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.misc import normalizePath

# Set up logging
from qtpyvcp.utilities import logger
log = logger.getLogger(__name__)

INFO = Info()
CONFIG_DIR = os.getenv('CONFIG_DIR')

class _Preferences(ConfigParser.RawConfigParser):

    def __init__(self, pref_file='~/.qtpyvcp.pref'):
        ConfigParser.RawConfigParser.__init__(self)

        self.pref_file = normalizePath(pref_file, CONFIG_DIR) or '/dev/null'

        self.getters = {
            bool: self.getBool,
            float: self.getFloat,
            int: self.getInt,
            list: self.getList,
            dict: self.getDict,
            str: self.getStr,
        }

        self.optionxform = str  # Needed to maintain options case

        if not os.path.isfile(self.pref_file):
            log.info("No preference file exists, creating: {}".format(self.pref_file))

        self.read(self.pref_file)

    def getPref(self, section, option, default_val=None, opt_type=bool):
        try:
            getter = self.getters.get(opt_type)
            value = getter(section, option, default_val)
            return value
        except ConfigParser.NoSectionError:
            # Add the section and the option
            log.debug("Adding missing section [{0}]".format(section))
            self.add_section(section)
            log.debug('Adding missing option [{0}] "{1}"'.format(section, option))
            self.set(section, option, default_val)
        except ConfigParser.NoOptionError:
            # Add the option
            log.debug('Adding missing option [{0}] "{1}"'.format(section, option))
            self.set(section, option, default_val)

        with open(self.pref_file, "w") as fh:
            self.write(fh)

        return default_val

    def setPref(self, section, option, value):
        try:
            self.set(section, option, str(value))
        except ConfigParser.NoSectionError:
            # Add the section and the option
            log.debug('Adding missing option [{0}] "{1}"'.format(section, option))
            self.add_section(section)
            self.set(section, option, str(value))

        with open(self.pref_file, "w") as fh:
            self.write(fh)

    def getStr(self, section, option, default):
        return self.get(section, option)

    def getFloat(self, section, option, default):
        value = self.get(section, option)
        try:
            return float(value)
        except (ValueError, SyntaxError):
            return default

    def getInt(self, section, option, default):
        value = self.get(section, option)
        try:
            return int(value)
        except (ValueError, SyntaxError):
            return default

    def getBool(self, section, option, default):
        value = self.get(section, option)
        if value.lower() in ['1', 'true', 'yes', 'on']:
            return True
        elif value.lower() in ['0', 'false', 'no', 'off']:
            return False
        log.error('Non boolean value "{0}" for option [{1}] {2},'
            ' using default value of "{3}"'.format(value, section, option, default))
        return default

    def getList(self, section, option, default):
        value = self.get(section, option)
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            log.error('"{0}" for option [{1}] {2} is not a valid list,'
                ' using default value of "{3}"'.format(value, section, option, default))
            return default

    def getDict(self, section, option, default):
        value = self.get(section, option)
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            log.error('"{0}" for option [{1}] {2} is not a valid dict,'
                ' using default value of "{3}"'.format(value, section, option, default))
            return default

class Prefs(_Preferences):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = _Preferences(*args, **kwargs)
        return cls._instance
