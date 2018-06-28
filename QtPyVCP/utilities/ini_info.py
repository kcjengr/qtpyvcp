#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of PyQtUI.
#
#   PyQtUI is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   PyQtUI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with PyQtUI.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   This module is used to get information from the machine's INI file.
#   It does some sanity checking to ensure it returns valid values.
#   If an INI entry does not exist, it may return a default value.

import os
import sys

from linuxcnc import ini

# Setup logging
from QtPyVCP.utilities import logger
log = logger.getLogger(__name__)

CONFIG_DIR = os.environ.get('CONFIG_DIR', None)
ini_path = os.environ.get("INI_FILE_NAME", '/dev/null')
INI = ini(ini_path)


# Global variables
AXIS_LETTERS = 'xyzabcuvw'

# All example data is from the sim XYZY gantry config
AXIS_LETTER_LIST = []   # Axes letters ['x', 'y', 'z'], no duplicates
JOINT_AXIS_DICT = {}    # Joint:Axis correspondence {0: 0, 1: 1, 2: 2, 3: 1}
DOUBLE_ALETTER = ""     # The letter of the double axis 'y'
ALETTER_JNUM_DICT = {}  # Axis Letter:Joint correspondence {'x': 0, 'y0': 1, 'z': 2, 'y1': 3}
JNUM_ALETTER_DICT = {}  # Joint:Axis Letter correspondence {0: 'x', 1: 'y0', 2: 'z', 3: 'y1'}


def init(ini_path):
    global INI, CONFIG_DIR
    INI = ini(ini_path)
    CONFIG_DIR = os.path.split(ini_path)[0]
    get_joint_axis_mapping()

def get_machine_name():
    return INI.find('EMC', 'MACHINE') or "hazzy"

def get_file_path(section, option, default):
    temp = INI.find(section, option) or default
    if temp is None:
        return
    elif temp.startswith('~'):
        path = os.path.expanduser(temp)
    elif not os.path.isabs(temp):
        path = os.path.join(CONFIG_DIR, temp)
    return os.path.realpath(path)


def get_ui_file(default='pyqtvcp.ui'):
    return get_file_path('DISPLAY', 'UI_FILE', default)

def get_py_file(default='pyqtvcp.py'):
    return get_file_path('DISPLAY', 'PY_FILE', default)

def get_log_file(default='~/pyqtvcp.log'):
    return get_file_path('DISPLAY', 'LOG_FILE', default)

def get_preference_file(default='~/pyqtvcp.pref'):
    return get_file_path('DISPLAY', 'PREFERENCE_FILE', default)

def get_mdi_hystory_file(default='~/.axis_mdi_history'):
    return get_file_path('DISPLAY', 'MDI_HISTORY_FILE', default)

def get_tool_table_file(default='tool.tbl'):
    return get_file_path('EMCIO', 'TOOL_TABLE', default)

def get_coordinates():
    '''Returns [TRAJ] COORDINATES or xyz'''
    temp = INI.find('TRAJ', 'COORDINATES') or 'XYZ'
    temp = temp.replace(' ','')
    if not temp:
        log.warning("No [TRAJ] COORDINATES entry in INI, using XYZ")
        temp = "xyz"
    return temp.lower()

def get_num_joints():
    '''Returns value of [KINS] JOINTS or 3'''
    temp = INI.find('KINS', 'JOINTS')
    if not temp:
        log.warning("No [KINS] JOINTS entry in INI file, using 3")
        return (3)
    return int(temp)

def get_axis_list():
    '''Returns a list of the Cartesian axes.'''
    axis_list = []
    coordinates = get_coordinates()
    for axis_letter in coordinates:
        if axis_letter in axis_list:
            continue
        axis_list.append(axis_letter)
    return axis_list

def get_is_machine_metric():
    temp = INI.find('TRAJ', 'LINEAR_UNITS')
    if not temp:
        # Then get the X axis units
        temp = INI.find('AXIS_X', 'UNITS') or False
    if temp in ['mm', 'metric']:
        return True
    else:
        return False

def get_no_force_homing():
    temp = INI.find('TRAJ', 'NO_FORCE_HOMING')
    if temp and temp == '1':
        return True
    return False

def get_position_feedback():
    temp = INI.find('DISPLAY', 'POSITION_FEEDBACK')
    if not temp or temp == "0":
        return True
    if temp.lower() == "actual":
        return True
    else:
        return False

def get_is_lathe():
    temp = INI.find('DISPLAY', 'LATHE')
    if not temp or temp == "0":
        return False
    return True

def get_is_backtool_lathe():
    temp = INI.find('DISPLAY', 'BACK_TOOL_LATHE')
    if not temp or temp == "0":
        return False
    return True

def get_jog_vel():
    # get default jog velocity
    # must convert from INI's units per second to hazzys's units per minute
    temp = INI.find('DISPLAY', 'DEFAULT_LINEAR_VELOCITY')
    if not temp:
        temp = 3.0
    return float(temp) * 60

def get_max_jog_vel():
    # get max jog velocity
    # must convert from INI's units per second to hazzy's units per minute
    temp = INI.find('DISPLAY', 'MAX_LINEAR_VELOCITY')
    if not temp:
        temp = 10.0
    return float(temp) * 60

# ToDo : This may not be needed, as it could be recieved from linuxcnc.stat
def get_max_velocity():
    # max velocity settings: more then one place to check
    # This is the maximum velocity of the machine
    temp = INI.find('TRAJ', 'MAX_VELOCITY')
    if  temp == None:
        log.warning("No MAX_VELOCITY found in [TRAJ] of INI file. Using 15ipm")
        temp = 15.0
    return float(temp) * 60

def get_default_spindle_speed():
    # check for default spindle speed settings
    temp = INI.find('DISPLAY', 'DEFAULT_SPINDLE_SPEED')
    if not temp:
        temp = 300
        log.warning("No DEFAULT_SPINDLE_SPEED entry found in [DISPLAY] of INI file. Using 300rpm")
    return float(temp)

def get_max_spindle_override():
    # check for override settings
    temp = INI.find('DISPLAY', 'MAX_SPINDLE_OVERRIDE')
    if not temp:
        temp = 1.0
        log.warning("No MAX_SPINDLE_OVERRIDE entry found in [DISPLAY] of INI file. Using 1.0")
    return float(temp)

def get_min_spindle_override():
    temp = INI.find('DISPLAY', 'MIN_SPINDLE_OVERRIDE')
    if not temp:
        temp = 0.1
        log.warning("No MIN_SPINDLE_OVERRIDE entry found in [DISPLAY] of INI file. Using 0.1")
    return float(temp)

def get_max_feed_override():
    temp = INI.find('DISPLAY', 'MAX_FEED_OVERRIDE')
    if not temp:
        temp = 1.0
        log.warning("No MAX_FEED_OVERRIDE entry found in [DISPLAY] of INI file. Using 1.0")
    return float(temp)

def get_parameter_file():
    temp = INI.find('RS274NGC', 'PARAMETER_FILE')
    if not temp:
        return False
    return temp

def get_program_prefix():
    path = INI.find('DISPLAY', 'PROGRAM_PREFIX')
    if path:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path
        else:
            log.warning("Path '{}' given in [DISPLAY] PROGRAM_PREFIX does not exist, "
            "trying '~/linuxcnc/nc_files'".format(path))

    path = os.path.expanduser("~/linuxcnc/nc_files")
    if os.path.exists(path):
        return path
    else:
        log.warning("Default path '~/linuxcnc/nc_files' does not exist, using '~/' as path")
        path = os.path.expanduser('~/')
        return path

def get_program_extentions():
    extensions = INI.findall("FILTER", "PROGRAM_EXTENSION")
    ext_list = ([ext.split(None, 1) for ext in extensions]) or None
    return ext_list

def get_glob_filefilter():
    """Returns list of glob style file filters"""
    file_ext = INI.findall('FILTER', 'PROGRAM_EXTENSION')
    ext_list = ["*.ngc"]
    if file_ext:
        for data in file_ext:
            raw_ext = data.split(",")
            for extension in raw_ext:
                ext = extension.split()
                ext_list.append(ext[0].replace(".", "*."))
    else:
        log.error("Error converting file extensions in [FILTER] PROGRAM_EXTENSION, using default '*.ngc'")
    return ext_list

def get_qt_filefilter():
    """Returns Qt file filter string for use with QtFileDialoge"""
    qt_filter_list = [("G-code (*.ngc)")]
    extensions = get_program_extentions()
    if extensions is not None:
        try:
            for extention, description in get_program_extentions():
                extention = extention.replace(' ', '').replace(',', ' ').replace('.','*.')
                description = description.strip()
                qt_filter_list.append(( ';;{} ({})'.format(description, extention)))
            return ''.join(qt_filter_list)
        except:
            log.error("Error converting file extensions in [FILTER] PROGRAM_EXTENSION, using default '*.ngc'")
    return qt_filter_list[0]

def get_filter_program(fname):
    """Returns the filter program specified for processing this type of file"""
    ext = os.path.splitext(fname)[1]
    if ext:
        return INI.find("FILTER", ext[1:])
    else:
        return None








def get_increments():
    jog_increments = []
    increments = INI.find('DISPLAY', 'INCREMENTS')
    if increments:
        if "," in increments:
            for i in increments.split(","):
                jog_increments.append(i.strip())
        else:
            jog_increments = increments.split()
        jog_increments.insert(0, 0)
    else:
        jog_increments = [ "0", "1.000", "0.100", "0.010", "0.001" ]
        log.warning("No default jog increments entry found in [DISPLAY] of INI file")
    return jog_increments

def get_subroutine_paths():
    subroutines_paths = INI.find('RS274NGC', 'SUBROUTINE_PATH')
    if not subroutines_paths:
        log.info("No subroutine folder or program prefix given in INI file")
        subroutines_paths = program_prefix()
    if not subroutines_paths:
        return False
    return subroutines_paths

def get_RS274_start_code():
    temp = INI.find('RS274NGC', 'RS274NGC_STARTUP_CODE')
    if not temp:
        return False
    return  temp

def get_startup_notification():
    return INI.find('DISPLAY', 'STARTUP_NOTIFICATION')

def get_startup_warning():
    return INI.find('DISPLAY', 'STARTUP_WARNING')


def get_joint_axis_mapping():
    global AXIS_LETTERS, AXIS_LETTER_LIST, JOINT_AXIS_DICT, DOUBLE_ALETTER, \
        ALETTER_JNUM_DICT, JNUM_ALETTER_DICT

    coordinates = get_coordinates()
    num_joints = get_num_joints()

    # Axis letter list (Ex. ['X', 'Y', 'Z', 'B'])
    for joint, axis_letter in enumerate(coordinates):
        if axis_letter in AXIS_LETTER_LIST:
            continue
        AXIS_LETTER_LIST.append(axis_letter)

    num_axes = len(AXIS_LETTER_LIST)

    # Joint:Axis dict (Ex. {0:0, 1:1, 2:2, 3:4})
    for jnum, aletter in enumerate(coordinates):
        anum = AXIS_LETTERS.index(aletter)
        JOINT_AXIS_DICT[jnum] = anum

    for aletter in AXIS_LETTERS:
        if coordinates.count(aletter) > 1:
            DOUBLE_ALETTER += aletter
    if DOUBLE_ALETTER != "":
        log.info("Machine appearers to be a gantry config having a double {0} axis"
              .format(DOUBLE_ALETTER.upper()))

    if num_joints == len(coordinates):
        log.info("The machine has {0} axes and {1} joints".format(num_axes, num_joints))
        log.info("The Axis/Joint mapping is:")
        count = 0
        for jnum, aletter in enumerate(coordinates):
            if aletter in DOUBLE_ALETTER:
                aletter = aletter + str(count)
                count += 1
            ALETTER_JNUM_DICT[aletter] = jnum
            JNUM_ALETTER_DICT[jnum] = aletter
            log.info("Axis {0} --> Joint {1}".format(aletter.upper(), jnum))
    else:
        log.info("The number of joints ({0}) is not equal to the number of coordinates ({1})"
              .format(num_joints, len(coordinates)))
        log.info("It is highly recommended that you update your config.")
        log.info("Reverting to old style. This could result in incorrect behavior...")
        log.info("\nGuessing Axes/Joints mapping:")
        for jnum, aletter in enumerate(AXIS_LETTERS):
            if aletter in coordinates:
                ALETTER_JNUM_DICT[aletter] = jnum
                log.info("Axis {0} --> Joint {1}".format(aletter, jnum))

    # print "AXIS_LETTER_LIST ", AXIS_LETTER_LIST
    # print "JOINT_AXIS_DICT, ", JOINT_AXIS_DICT
    # print "ALETTER_JNUM_DICT ", ALETTER_JNUM_DICT
    # print "JNUM_ALETTER_DICT ", JNUM_ALETTER_DICT
