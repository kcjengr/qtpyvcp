#   Copyright (c) 2020 Kurt Jacobson
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

import os
from ConfigParser import ConfigParser
from collections import OrderedDict

from qtpyvcp.plugins import DataPlugin

class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):

        if key in self.keys():
            items = self.get(key)
            new = None
            if isinstance(value, list):
                new = value[0]
            if new is not None and new not in items:
                items.append(new)
        else:
            super(MultiOrderedDict, self).__setitem__(key, value)


class IniConfig(DataPlugin):
    def __init__(self, ini_file=None):
        super(IniConfig, self).__init__()

        self.config = ConfigParser(dict_type=MultiOrderedDict)

        self.ini_file = os.path.abspath(ini_file or os.environ.get("INI_FILE_NAME"))

    def getChannel(self, url):
        print(url)
        try:
            chan_obj = [url]
            chan_exp = chan_obj.getValue
        except KeyError:
            return None, None

        return chan_obj, chan_exp

    def initialise(self):
        self.config.read(self.ini_file)

        for section in self.config.sections():
            for option in self.config.items(section):
                self.log.debug("SECTION = {0} | OPTION = {1[0]} | VALUE {1[1]}".format(section, option))

    def terminate(self):
        pass

