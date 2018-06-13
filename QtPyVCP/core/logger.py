#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   Application wide logging module.


import os
import logging
from linuxcnc import ini

from QtPyVCP.lib.colored_formatter import ColoredFormatter


inipath = os.environ.get('INI_FILE_NAME')

if inipath:
    ini = ini(inipath)
    path = ini.find('DISPLAY', 'LOG_FILE')
    if not path:
        log_file = os.path.expanduser('~/hazzy.log')
    elif path.startswith('~'):
        log_file = os.path.expanduser(path)
    elif not os.path.isabs(path):
        log_file = os.path.join(Paths.CONFIGDIR, path)
    else:
        log_file = os.path.realpath(path)
else:
    log_file = os.path.expanduser('~/hazzy.log')

with open(log_file, 'w') as fh:
    pass

# Get logger for module.__name__
def get(name):
    # name = name.upper()
    return logging.getLogger(name)

# Set global logging level
def set_level(level):
    base_log.setLevel(getattr(logging, level))
    log.info('Base log level set to {}'.format(level))

# Create base logger
base_log = logging.getLogger("QtPyVCP")
base_log.setLevel(logging.DEBUG)

# Add console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
cf = ColoredFormatter("[%(name)s][%(levelname)s]  %(message)s (%(filename)s:%(lineno)d)")
ch.setFormatter(cf)
base_log.addHandler(ch)

# Add file handler
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
ff = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(ff)
base_log.addHandler(fh)

# Get logger for logger
log = get(__name__)
log.info('Logging to "{}"'.format(log_file))
