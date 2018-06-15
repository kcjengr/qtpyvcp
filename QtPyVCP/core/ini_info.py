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
from QtPyVCP.core import logger
log = logger.get(__name__)


INI_FILE = os.environ.get('INI_FILE_NAME', '/dev/null')
ini = ini(INI_FILE)


class Config(object):

    def get_file_path(section, option, default):
        global ini
        temp = ini.find(section, option) or default
        if temp and temp.startswith('~'):
            path = os.path.expanduser(temp)
        elif not os.path.isabs(temp):
            path = os.path.join(self.CONFIG_DIR, temp)
        else:
            path = os.path.realpath(temp)
        return path


    COORDINATES = (ini.find('TRAJ', 'COORDINATES') or 'xyz').replace(' ','').lower()
    IS_METRIC = bool((ini.find('TRAJ', 'LINEAR_UNITS') or
            ini.find('AXIS_X', 'UNITS')) in ['mm', 'metric'])

    LOG_FILE = get_file_path('DISPLAY', 'LOG_FILE', '~/pyqtui.log')

    def __int__(self):

        self.CONFIG_DIR = os.environ.get('CONFIG_DIR')

        self.MACHINE_NAME = ini.find('EMC', 'MACHINE') or "PyQtUI Machine"


        # [DISPLAY]
        self.LOG_FILE = self.get_file_path('DISPLAY', 'LOG_FILE', '~/pyqtui.log')
        self.PREF_FILE = get_file_path('DISPLAY', 'PREFERENCE_FILE', '~/pyqtui.pref')
        self.XML_FILE = get_file_path('DISPLAY', 'XML_FILE', '~/pyqtui.xml')
        self.MDI_HISTORY_FILE = get_file_path('DISPLAY', 'MDI_HISTORY_FILE', '~/.axis_mdi_history')
        self.PROGRAM_PREFIX = self.get_program_prefix()

        self.DISPLAY_ACTUAL_POSITION = bool((ini.find('DISPLAY', 'POSITION_FEEDBACK') or
            'cmd').lower() == 'actual')
        self.IS_LATHE = bool((ini.find('DISPLAY', 'LATHE') or '0') == '1')
        self.IS_BACKTOOL_LATHE = bool((ini.find('DISPLAY', 'BACK_TOOL_LATHE') or '0') == '1')
        self.DEFAULT_LINEAR_VELOCITY = float(ini.find('DISPLAY', 'DEFAULT_LINEAR_VELOCITY') or 3.0) * 60
        self.MAX_LINEAR_VELOCITY = float(ini.find('DISPLAY', 'MAX_LINEAR_VELOCITY') or 10.0) * 60
        self.DEFAULT_SPINDLE_SPEED = float(ini.find('DISPLAY', 'DEFAULT_SPINDLE_SPEED') or 200)
        self.MIN_SPINDLE_OVERRIDE = float(ini.find('DISPLAY', 'MIN_SPINDLE_OVERRIDE') or 0.1)
        self.MAX_SPINDLE_OVERRIDE = float(ini.find('DISPLAY', 'MAX_SPINDLE_OVERRIDE') or 1.0)
        self.MAX_FEED_OVERRIDE = float(ini.find('DISPLAY', 'MAX_FEED_OVERRIDE') or 1.0)

        # [EMCIO]
        self.TOOL_TABLE = get_file_path('EMCIO', 'TOOL_TABLE', 'tool.tbl')

        # [TRAJ]
        self.COORDINATES = (ini.find('TRAJ', 'COORDINATES') or 'xyz').replace(' ','').lower()
        self.IS_METRIC = bool((ini.find('TRAJ', 'LINEAR_UNITS') or
            ini.find('AXIS_X', 'UNITS')) in ['mm', 'metric'])
        self.REQUIRE_HOMING = bool((ini.find('TRAJ', 'NO_FORCE_HOMING') or 0) == '1')
        self.MAX_VELOCITY = float(ini.find('TRAJ', 'MAX_VELOCITY') or 15.0) * 60

        # [KINS]
        self.NUM_JOINTS = int(ini.find('KINS', 'JOINTS') or len(self.COORDINATES))

        # [RS274NGC]
        self.PARAMETER_FILE = ini.find('RS274NGC', 'PARAMETER_FILE')
        self.STARTUP_CODE = ini.find('RS274NGC', 'RS274NGC_STARTUP_CODE')
        self.SUBROUTINE_PATH = ini.find('RS274NGC', 'SUBROUTINE_PATH') or self.PROGRAM_PREFIX

        # [FILTER]



        # Machine Info

        # These are useful
        self.NUM_AXES = 0
        self.AXIS_LETTER_LIST = []  # Axes letters [X, Y, Z, B], no duplicates
        self.JOIT_AXIS_DICT = {}    # Joint:Axis correspondence {0:0, 1:1, 2:2, 3:4}

        # These might be useful
        self.DOUBLE_AXIS_LETTER = ""
        self.AXIS_LETTER_JOINT_DICT = {}
        self.JOINT_AXIS_LETTER_DICT = {}

        self.get_joint_axis_relation()


    def get_file_path(section, option, default):
        temp = ini.find(section, option) or default
        if temp and temp.startswith('~'):
            path = os.path.expanduser(temp)
        elif not os.path.isabs(temp):
            path = os.path.join(self.CONFIG_DIR, temp)
        else:
            path = os.path.realpath(temp)
        return path

    def get_program_prefix(self):
        path = ini.find('DISPLAY', 'PROGRAM_PREFIX')

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

    def get_file_extentions(self):
        file_ext = ini.findall('FILTER', 'PROGRAM_EXTENSION')
        if file_ext:
            ext_list = ["*.ngc"]
            for data in file_ext:
                raw_ext = data.split(",")
                for extension in raw_ext:
                    ext = extension.split()
                    ext_list.append(ext[0].replace(".", "*."))
        else:
            log.error("Error converting file extensions in [FILTER] PROGRAM_EXTENSION, using default '*.ngc'")
            ext_list = ["*.ngc"]
        return ext_list

    def get_increments(self):
        jog_increments = []
        increments = ini.find('DISPLAY', 'INCREMENTS')
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


    def get_joint_axis_relation(self):
        # Axis letter list (Ex. ['X', 'Y', 'Z', 'B'])
        for joint, axis_letter in enumerate(self.COORDINATES):
            if axis_letter in axis_letter_list:
                continue
            axis_letter_list.append(axis_letter)

        self.NUM_AXES = len(axis_letter_list)

        # Joint:Axis dict (Ex. {0:0, 1:1, 2:2, 3:4})
        for jnum, aletter in enumerate(self.COORDINATES):
            anum = 'xyzabcuvw'.index(aletter)
            self.JOIT_AXIS_DICT[jnum] = anum

        for aletter in 'xyzabcuvw':
            if self.COORDINATES.count(aletter) > 1:
                DOUBLE_AXIS_LETTER += aletter
        if self.DOUBLE_AXIS_LETTER != "":
            log.info("Machine appearers to be a gantry config having a double {0} axis"
                  .format(self.DOUBLE_AXIS_LETTER))

        if self.NUM_JOINTS == len(self.COORDINATES):
            log.info("The machine has {0} axes and {1} joints".format(self.NUM_AXES, self.NUM_JOINTS))
            log.info("The Axis/Joint mapping is:")
            count = 0
            for jnum, aletter in enumerate(self.COORDINATES):
                if aletter in self.DOUBLE_AXIS_LETTER:
                    aletter = aletter + str(count)
                    count += 1
                self.AXIS_LETTER_JOINT_DICT[aletter] = jnum
                self.JOINT_AXIS_LETTER_DICT [jnum] = aletter
                log.info("Axis {0} --> Joint {1}".format(aletter.upper(), jnum))
        else:
            log.info("The number of joints ({0}) is not equal to the number of coordinates ({1})"
                  .format(self.NUM_JOINTS, len(self.COORDINATES)))
            log.info("It is highly recommended that you update your config.")
            log.info("Reverting to old style. This could result in incorrect behavior...")
            log.info("\nGuessing Axes/Joints mapping:")
            for jnum, aletter in enumerate('xyzabcuvw'):
                if aletter in self.COORDINATES:
                    self.AXIS_LETTER_JOINT_DICT[aletter] = jnum
                    log.info("Axis {0} --> Joint {1}".format(aletter, jnum))
