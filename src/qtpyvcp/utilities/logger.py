# QtPyVCP Logging Module
# Provides a consistent and easy to use logging facility.  Log messages printed
# to the terminal will be colorized for easy identification of log level.
#
# Copyright (c) 2017 Kurt Jacobson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


import os

import logging
from logging.handlers import SocketHandler

from linuxcnc import ini

# Our custom colorizing formatter for the terminal handler
from qtpyvcp.lib.colored_formatter import ColoredFormatter
from qtpyvcp.lib.logger import TTYHandler
from qtpyvcp.utilities.misc import normalizePath

# Global name of the base logger
BASE_LOGGER_NAME = None

CONFIG_DIR = os.getenv('CONFIG_DIR')
DEFAULT_LOG_FILE = os.path.expanduser('~/qtpyvcp.log')

# Define the log message formats
TERM_FORMAT = '[%(name)s][%(levelname)s]  %(message)s (%(filename)s:%(lineno)d)'
FILE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
TTY_FORMAT = '\033[1;37;40m%(levelname)-5s\033[0m %(name)-8s %(message)s\r\n'

# Get logger for module based on module.__name__
def getLogger(name):
    if BASE_LOGGER_NAME is None:
        initBaseLogger('qtpyvcp')
    if not name.startswith(BASE_LOGGER_NAME):
        name = '{}.{}'.format(BASE_LOGGER_NAME, name)
    return logging.getLogger(name.replace('qtpyvcp', BASE_LOGGER_NAME))

# Get an integer log level from a level name
def logLevelFromName(level_name):
    return logging._checkLevel(level_name.upper())

# Set global logging level
def setGlobalLevel(log_level):
    base_log = logging.getLogger(BASE_LOGGER_NAME)
    try:
        base_log.setLevel()
        base_log.info('Base log level set to {}'.format(log_level))
    except KeyError:
        base_log.error("Log level '{}' is not valid, base log level not changed." \
            .format(log_level))

# Initialize the base logger
def initBaseLogger(name, log_file=None, log_level="DEBUG"):

    global BASE_LOGGER_NAME
    if BASE_LOGGER_NAME is not None:
        return getLogger(name)

    BASE_LOGGER_NAME = name

    log_file = normalizePath(log_file, CONFIG_DIR or os.getenv('HOME')) or DEFAULT_LOG_FILE

    # Clear the previous sessions log file
    with open(log_file, 'w') as fh:
        pass

    # Create base logger
    base_log = logging.getLogger(BASE_LOGGER_NAME)

    try:
        base_log.setLevel(logLevelFromName(log_level))
    except KeyError:
        raise ValueError("Log level '{}' is not valid.".format(log_level))

    # Add console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    cf = ColoredFormatter(TERM_FORMAT)
    ch.setFormatter(cf)
    base_log.addHandler(ch)

    # Add file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    ff = logging.Formatter(FILE_FORMAT)
    fh.setFormatter(ff)
    base_log.addHandler(fh)

    # Add socket handler
    # sh = SocketHandler('127.0.0.1', 19996)
    # sh.setLevel(logging.DEBUG)
    # sf = logging.Formatter(FILE_FORMAT)
    # sh.setFormatter(sf)
    # base_log.addHandler(sh)

    # Add tty handler
    # th = TTYHandler(port='/dev/ttyUSB0')
    # th.setLevel(logging.DEBUG)
    # tf = logging.Formatter(TTY_FORMAT)
    # th.setFormatter(tf)
    # base_log.addHandler(th)


    # Get logger for logger
    log = getLogger(__name__)
    base_log.info('Logging to yellow<{}>'.format(log_file))

    return base_log
