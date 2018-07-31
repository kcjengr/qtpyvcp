#!/usr/bin/env python

#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   Persistent preferences manager using INI format .pref file.


# Setting Preference:
#    set("section", "option", "value", type)
#    set("DROs", "dec_places", 4 , int)

# Getting Preference:
#    get("section", "option", "default_val", type)
#    dro_places = get("DROs", "dec_places", 3, int)

import os
import ast

import ConfigParser

from QtPyVCP.utilities.info import Info

# Set up logging
from QtPyVCP.utilities import logger
log = logger.getLogger(__name__)

INFO = Info()


class _Preferences(ConfigParser.RawConfigParser):

    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)

        self.getters = {
            bool: self.getBool,
            float: self.getFloat,
            int: self.getInt,
            list: self.getList,
            dict: self.getDict,
            str: self.getStr,
        }

        self.optionxform = str  # Needed to maintain options case

        self.fn = os.environ.get('VCP_PREF_FILE') or '/dev/null'
        if not os.path.isfile(self.fn):
            log.info("No preference file exists, creating: {}".format(self.fn))

        self.read(self.fn)

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

        with open(self.fn, "w") as fh:
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

        with open(self.fn, "w") as fh:
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
