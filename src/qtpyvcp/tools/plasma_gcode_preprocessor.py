#!/usr/bin/env python3

"""Plasma GCode Preprocessor - process gcode files for qtpyvcp plasma_db usage

    Using the 'filter' program model of linuxcnc,
    processes the raw gcode file coming from a sheetcam
    or similar to a gcode file with material and path
    substitutions needed to support plasma_db plugin
    cut/material/process configs.
    The results are printed to standard-out. Other
    special case data (e.g. progress) is sent to
    standard-error

Usage:
  plasma_gcode_preprocessor <gcode-file>
  plasma_gcode_preprocessor -h

"""

import os
import sys
import re
# import math
from math import sqrt, radians, degrees, pi, fabs, cos, sin, atan2
import logging
# import time
from enum import Enum, auto
# from typing import List, Dict, Tuple, Union

import hal
import linuxcnc
from qtpyvcp.plugins.plasma_processes import PlasmaProcesses
from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.utilities.config_loader import load_config_files

# import pydevd;pydevd.settrace()

PREPROC_VERSION = '00.30'

PREPROC_VERSION = '00.30'

INI = linuxcnc.ini(os.environ['INI_FILE_NAME'])
preprocessor_log_name = normalizePath(path='gcode_preprocessor.log', base=os.getenv('CONFIG_DIR', '~/'))
# Construct LOG from qtpyvcp standard logging framework
formatter = "%(asctime)s; %(levelname)s; %(message)s"
logging.basicConfig(filename=preprocessor_log_name, level=logging.DEBUG, format=formatter)
LOG = logging.getLogger(__name__)
LOG.info('---------------------------------------------------')
LOG.info('------------- Initialising log system -------------')
LOG.info('---------------------------------------------------')


# Catch unhandled exceptions
def excepthook(exc_type, exc_msg, exc_tb):
    try:
        LOG.debug(exc_type)
        LOG.debug(exc_msg)
        LOG.debug(exc_tb)
    except Exception as e:
        LOG.info(f"Exception hook: {e}")


sys.excepthook = excepthook
LOG.info("Initialising ExceptionHook.")


# Set over arching converstion fact. All thinking and calcs are in mm so need
# convert and arbirary values to bannas when they are in use
UNITS, PRECISION, UNITS_PER_MM = ['in',6,25.4] if INI.find('TRAJ', 'LINEAR_UNITS') == 'inch' else ['mm',4,1]

# force the python HAL lib to load/init. Not doing this causes a silent "crash"
# when trying to set a hal pin
try:
    h = hal.component('dummy')
    LOG.debug('Python HAL is available')
except Exception as e:
    LOG.warn(f'Python HAL is NOT available: {e}')


# Define some globals that will be referenced from anywhere
# assumption is MM's is the base unit of reference.
PLASMADB = None
DEBUG_COMMENTS = True

G_MODAL_GROUPS = {
    1: ('G0','G1','G2','G3','G33','G38.n','G73','G76','G80','G81',\
        'G82','G83','G84','G85','G86','G87','G88','G89'),
    2: ('G17','G18','G19','G17.1','G18.1','G19.1'),
    3: ('G90','G91'),
    4: ('G90.1','G91.1'),
    5: ('G93','G94','G95'),
    6: ('G20','G21'),
    7: ('G40','G41','G42','G41.1','G42.1'),
    8: ('G43','G43.1','G49'),
    10: ('G98','G99'),
    12: ('G54','G55','G56','G57','G58','G59','G59.1','G59.2','G59.3'),
    13: ('G61','G61.1','G64'),
    14: ('G96','G97'),
    15: ('G7','G8')}

M_MODAL_GROUPS = {
    4: ('M0','M1','M2','M30','M60'),
    7: ('M3','M4','M5'),
    9: ('M48','M49')}


# Enum for line type
class Commands(Enum):
    COMMENT                     = auto()
    CONTAINS_COMMENT            = auto()
    ABSOLUTE                    = auto()
    RELATIVE                    = auto()
    MOVE_LINEAR                 = auto()
    MOVE_ARC                    = auto()
    ARC_RELATIVE                = auto()
    ARC_ABSOLUTE                = auto()
    TOOLCHANGE                  = auto()
    PASSTHROUGH                 = auto()
    OTHER                       = auto()
    XY                          = auto()
    MAGIC_MATERIAL              = auto()
    MATERIAL_CHANGE             = auto()
    BEGIN_CUT                   = auto()
    END_CUT                     = auto()
    BEGIN_SCRIBE                = auto()
    END_SCRIBE                  = auto()
    BEGIN_SPOT                  = auto()
    END_SPOT                    = auto()
    BEGIN_MARK                  = auto()
    END_MARK                    = auto()
    END_ALL                     = auto()
    SELECT_PROCESS              = auto()
    WAIT_PROCESS                = auto()
    FEEDRATE_MATERIAL           = auto()
    FEEDRATE_LINE               = auto()
    ENABLE_IGNORE_ARC_OK_SYNCH  = auto()
    ENABLE_IGNORE_ARC_OK_IMMED  = auto()
    DISABLE_IGNORE_ARC_OK_SYNCH = auto()
    DISABLE_IGNORE_ARC_OK_IMMED = auto()
    DISABLE_THC_SYNCH           = auto()
    DISABLE_THC_IMMED           = auto()
    ENABLE_THC_SYNCH            = auto()
    ENABLE_THC_IMMED            = auto()
    DISABLE_TORCH_SYNCH         = auto()
    DISABLE_TORCH_IMMED         = auto()
    ENABLE_TORCH_SYNCH          = auto()
    ENABLE_TORCH_IMMED          = auto()
    FEED_VEL_PERCENT_SYNCH      = auto()
    FEED_VEL_PERCENT_IMMED      = auto()
    CUTTER_COMP_LEFT            = auto()
    CUTTER_COMP_RIGHT           = auto()
    CUTTER_COMP_OFF             = auto()
    HOLE_MODE                   = auto()
    HOLE_DIAM                   = auto()
    HOLE_VEL                    = auto()
    HOLE_OVERCUT                = auto()
    PIERCE_MODE                 = auto()
    KEEP_Z                      = auto()
    UNITS                       = auto()
    PATH_BLENDING               = auto()
    ADAPTIVE_FEED               = auto()
    SPINDLE_ON                  = auto()
    SPINDLE_OFF                 = auto()
    PROGRAM_END                 = auto()
    DIGITAL_IN                  = auto()
    DIGITAL_OUT                 = auto()
    ANALOG_IN                   = auto()
    ANALOG_OUT                  = auto()
    OWORD                       = auto()
    VARIABLE                    = auto()
    REMOVE                      = auto()
    RAW                         = auto()



class CodeLine:
# Class to represent a single line of gcode

    def __init__(self, line, parent = None, g2g3flip = False):
        """args:
        line:  the gcode line to be parsed
        mode: the model state. i.e. what G state has been set
        """
        self._parent = parent
        self.arc_flip = g2g3flip
        self.command = ()
        self.params = {}
        self.comment = ''
        self.raw = line
        self.errors = {}
        self.type = None
        self.is_hole = False
        self.is_pierce = False
        self.token = ''
        self.active_g_modal_groups = {}
        self.cutchart_id = None
        self.hole_builder = None
        self.pierce_builder = None


        # token mapping for line commands
        tokens = {
            'G0':(Commands.MOVE_LINEAR, self.parse_linear),
            'G10':(Commands.PASSTHROUGH, self.parse_raw),
            'G1':(Commands.MOVE_LINEAR, self.parse_linear),
            'G20':(Commands.UNITS, self.set_inches),
            'G21':(Commands.UNITS, self.set_mms),
            'G2':(Commands.MOVE_ARC, self.parse_arc),
            'G3':(Commands.MOVE_ARC, self.parse_arc),
            #'M3$0':Commands.BEGIN_CUT,
            #'M5$0':Commands.END_CUT,
            #'M3$1':Commands.BEGIN_SCRIBE,
            #'M5$1':Commands.END_SCRIBE,
            #'M3$2':Commands.BEGIN_SPOT,
            #'M5$2':Commands.END_SPOT,
            #'M5$-1':Commands.END_ALL,
            #'M190':(Commands.SELECT_PROCESS, self.placeholder),
            #'M66P3L3':(Commands.WAIT_PROCESS, self.placeholder),
            #'F#<_hal[plasmac.cut-feed-rate]>':Commands.FEEDRATE_MATERIAL,
            #'M62P1':Commands.ENABLE_IGNORE_ARC_OK_SYNCH,
            #'M64P1':Commands.ENABLE_IGNORE_ARC_OK_IMMED,
            #'M63P1':Commands.DISABLE_IGNORE_ARC_OK_SYNCH,
            #'M65P1':Commands.DISABLE_IGNORE_ARC_OK_IMMED,
            #'M62P2':Commands.DISABLE_THC_SYNCH,
            #'M64P2':Commands.DISABLE_THC_IMMED,
            #'M63P2':Commands.ENABLE_THC_SYNCH,
            #'M65P2':Commands.ENABLE_THC_IMMED,
            #'M62P3':Commands.DISABLE_TORCH_SYNCH,
            #'M64P3':Commands.DISABLE_TORCH_IMMED,
            #'M63P3':Commands.ENABLE_TORCH_SYNCH,
            #'M65P3':Commands.ENABLE_TORCH_IMMED,
            #'M67E3':Commands.FEED_VEL_PERCENT_SYNCH,
            #'M68E3':Commands.FEED_VEL_PERCENT_IMMED,
            'G41':(Commands.CUTTER_COMP_LEFT, self.cutter_comp_error),
            'G42':(Commands.CUTTER_COMP_RIGHT, self.cutter_comp_error),
            'G41.1':(Commands.CUTTER_COMP_LEFT, self.cutter_comp_error),
            'G42.1':(Commands.CUTTER_COMP_RIGHT, self.cutter_comp_error),
            'G40':(Commands.CUTTER_COMP_OFF, self.parse_passthrough),
            'G64':(Commands.PATH_BLENDING, self.parse_passthrough),
            'M52':(Commands.ADAPTIVE_FEED, self.parse_passthrough),
            'M2':(Commands.PROGRAM_END, self.parse_passthrough),
            'M30':(Commands.PROGRAM_END, self.parse_passthrough),
            'M3':(Commands.SPINDLE_ON, self.parse_spindle_on),
            'M5':(Commands.SPINDLE_OFF, self.parse_spindle_off),
            'M190':(Commands.MATERIAL_CHANGE, self.parse_passthrough),
            'M62':(Commands.DIGITAL_OUT, self.parse_passthrough),
            'M63':(Commands.DIGITAL_OUT, self.parse_passthrough),
            'M64':(Commands.DIGITAL_OUT, self.parse_passthrough),
            'M65':(Commands.DIGITAL_OUT, self.parse_passthrough),
            'M66':(Commands.WAIT_PROCESS, self.parse_passthrough),
            'M67':(Commands.ANALOG_OUT, self.parse_passthrough),
            'M68':(Commands.ANALOG_OUT, self.parse_passthrough),
            'G90':(Commands.ABSOLUTE, self.parse_passthrough),
            'G91':(Commands.RELATIVE, self.parse_passthrough),
            'G91.1':(Commands.ARC_RELATIVE, self.parse_passthrough),
            'G90.1':(Commands.ARC_ABSOLUTE, self.parse_passthrough),
            'F#':(Commands.FEEDRATE_MATERIAL, self.parse_passthrough),
            'F':(Commands.FEEDRATE_LINE, self.parse_feedrate),
            'O':(Commands.OWORD, self.parse_raw),
            '#<holes>':(Commands.HOLE_MODE, self.placeholder),
            '#<h_diameter>':(Commands.HOLE_DIAM, self.placeholder),
            '#<h_velocity>':(Commands.HOLE_VEL, self.placeholder),
            '#<oclength>':(Commands.HOLE_OVERCUT, self.placeholder),
            '#<pierce-only>':(Commands.PIERCE_MODE, self.placeholder),
            #'#<keep-z-motion>':Commands.KEEP_Z,
            '#<':(Commands.VARIABLE, self.parse_raw),
            ';':(Commands.COMMENT, self.parse_comment),
            '(o=':(Commands.MAGIC_MATERIAL, self.parse_material),
            '(':(Commands.COMMENT, self.parse_comment),
            'T':(Commands.TOOLCHANGE, self.parse_toolchange)
            }

        # a line could have multiple Gcodes on it. This is typical of the
        # preamble set by many CAM packages.  The processor should not need
        # to change any of this. It should be 'correct'.  So all we need
        # to do is
        # [1] Recognise it is there
        # [2] Scan for any illegal codes, set any error codes if needed
        # [3] Mark line for pass through
        multi_codes = re.findall(r"G\d+|T\s*\d+|M\d+", line.upper().strip())
        if len(multi_codes) > 1:
            LOG.debug(f'Codeline: Multi codes on line detected: {line}')
            # we have multiple codes on the line
            self.type = Commands.PASSTHROUGH
            # scan for possible 'bad' codes
            for code in multi_codes:
                if code in ('G41','G42','G41.1','G42.1'):
                    # we have an error state
                    self.cutter_comp_error()
                # look for G90
                if code == 'G90':
                    self._parent.set_active_g_modal('G90')
                # look for G90
                if code == 'G91':
                    self._parent.set_active_g_modal('G91')
            # look for Tx M6 combo
            f = re.findall(r"T\s*\d+|M6", line.upper().strip())
            if len(f) == 2:
                # we have a tool change combo. Assume in form Tx M6
                self.parse_toolchange(combo=True)
        else:
            # not a multi code on single line situation so process line
            # to set line type
            LOG.debug(f'Codeline: Non-Multi code: Scan tokens on line. {line}')
            for k in tokens:
                # do regex searches to find exact matches of the token patterns
                # magic = False
                if k == '(':
                    # deal with escaping the '(' which is special char in regex
                    pattern = r"^\({1}"
                    r = re.search(pattern, line.upper().strip())
                elif k == '(o=':
                    pattern = r"^\(o={1}"
                    # magic = True
                    r = re.search(pattern, line.lower().strip())
                else:
                    pattern = r"^"+k + r"{1}"
                    r = re.search(pattern, line.upper().strip())
                
                # we need to do an over ride check for a line that has gcode
                # variables in it.  These lines need to be passed through with
                # no further processing else the intent of the gcode progam
                # could be ruined.
                override = re.search('#<', line.upper().strip())
                if override is not None:
                    # found gcode variables, force r to None
                    r = None
                
                if r is not None:
                    # since r is NOT None we must have found something
                    self.type = tokens[k][0]
                    self.token = k
                    LOG.debug(f'Non-Multi: token type = {self.type} token = {self.token}')
                    # call the parser method bound to this key
                    tokens[k][1]()
                    # check for an inline comment if the entire line is not a comment
                    if self.type not in [Commands.COMMENT, Commands.MAGIC_MATERIAL]:
                        self.parse_inline_comment()
                    # break out of the loop, we found a match
                    break
                else:
                    # nothing of interest just mark the line for pass through processing
                    self.type = Commands.PASSTHROUGH
            if self.type is Commands.PASSTHROUGH:
                LOG.debug('Codeline: Command type = PASSTHROUGH: Do further checks, e.g. XY line/')
                # If the result was seen as 'OTHER' do some further checks
                # As soon as we shift off being type OTHER, exit the method
                # 1. is it an XY line
                override = re.search('#<', line.upper().strip())
                if override is None:
                    self.parse_XY_line()
                #if self.type is not Commands.OTHER: return


    def strip_inline_comment(self, line):
        s = re.split(r";|\(", line, 1)
        try:
            return s[0].strip()
        except Exception as e:
            LOG.info(f'Strip inline issue: {e}')
            return line

    def save_g_modal_group(self, grp):
        self.active_g_modal_groups = grp.copy()


    def parse_comment(self):
        self.comment = self.raw
        self.command = (';', None)
        self.params = {}


    def parse_inline_comment(self):
        # look for possible inline comment
        s = re.split(r";|\(",self.raw[1:],1)
        robj = re.search(r";|\(",self.raw[1:])
        if robj is not None:
            # found an inline comment. get the char token for the comment
            i = robj.start() + 1
            found_c = self.raw[i]
            self.comment = found_c + s[1]
        else:
            # no comment found to empty the char token var
            found_c = ''
            self.comment = ''


    def parse_other(self):
        LOG.debug(f'Type OTHER -- {self.token} -- found - this code is not handled or considered')
        self.type = Commands.OTHER

    def parse_raw(self):
        self.type = Commands.RAW

    def parse_passthrough(self):
        self.type = Commands.PASSTHROUGH

    def parse_remove(self):
        self.type = Commands.REMOVE

    def parse_linear(self):
        # linear motion means either G0 or G1. So looking for X/Y on this line
        self.command = ('G',int(self.token[1:]))
        # split the raw line at the token and then look for X/Y existence
        line = self.raw.upper().split(self.token,1)[1].strip()
        tokens = re.finditer(r"X[\d\+\.-]*|Y[\d\+\.-]*", line)
        for token in tokens:
            params = re.findall(r"X|Y|[\d\+\.-]+", token.group())
            # this is now a list which can be added to the params dictionary
            if len(params) == 2:
                self.params[params[0]] = float(params[1])


    def parse_XY_line(self):
        line = self.strip_inline_comment(self.raw.upper().strip())
        tokens = re.finditer(r"X[\d\+\.-]*|Y[\d\+\.-]*", line)
        for token in tokens:
            params = re.findall(r"X|Y|[\d\+\.-]+", token.group())
            # this is now a list which can be added to the params dictionary
            if len(params) == 2:
                self.params[params[0]] = float(params[1])
            # if we are in the loop then we found X/Y instances so mark the line type
            self.type = Commands.XY


    def parse_arc(self):
        # arc motion means either G2 or G3. So looking for X/Y/I/J/P on this line
        self.command = ('G',int(self.token[1:]))
        # check for g2g3 flip and adjust command as needed
        if self.arc_flip:
            LOG.debug(f"Arc Flip True. Unchanged command: {self.command}")
            if self.command == ('G',2):
                self.command = ('G',3)
            else:
                self.command = ('G',2)
            LOG.debug(f"Arc Flip True. CHANGED command: {self.command}")
        # split the raw line at the token and then look for X/Y/I/J/P existence
        line = self.strip_inline_comment(self.raw).upper().split(self.token,1)[1].strip()
        tokens = re.finditer(r"X[\d\+\.-]*|Y[\d\+\.-]*|I[\d\+\.-]*|J[\d\+\.-]*|P[\d\+\.-]*", line)
        for token in tokens:
            params = re.findall(r"X|Y|I|J|P|[\d\+\.-]+", token.group())
            # this is now a list which can be added to the params dictionary
            if len(params) == 2:
                self.params[params[0]] = float(params[1])

    def parse_spindle_on(self):
        self.type = Commands.SPINDLE_ON
        self.command = ('M', int(self.token[1:]))
        # split the raw line at the token
        line = self.strip_inline_comment(self.raw).upper().split(self.token,1)[1].strip()
        params = re.findall(r"\$\d+|S\d+", line)
        if len(params) == 2:
            self.params['$'] = int(params[0][1:])
            self.params['S'] = int(params[1][1:])
        elif len(params) == 1:
            self.params['$'] = int(params[0][1:])
            self.params['S'] = int(1)
        elif len(params) == 0:
            # no spindle reference found so assume $0
            self.params['$'] = int(0)
            self.params['S'] = int(1)
    
    def parse_spindle_off(self):
        self.type = Commands.SPINDLE_OFF
        self.command = ('M', int(self.token[1:]))
        # split the raw line at the token
        line = self.strip_inline_comment(self.raw).upper().split(self.token,1)[1].strip()
        params = re.findall(r"\$\d+", line)
        if len(params) == 1:
            self.params['$'] = int(params[0][1:])
        elif len(params) == 0:
            # no spindle reference found so assume $-1
            self.params['$'] = int(-1)

    def parse_material(self):
        # Using the an enhanced version of the magic material
        # format used in qtplasmac we support
        # the dynamic creation of a cut material/process.
        # At this point only dynamic materials are supported with the
        # intention that a tool like SheetCam can hold all the material
        # data and thus not require syncing of data back to the plasma
        # processes database. Only valid for o=0 at the moment.
        # Used params:
        # o=0,
        # na=the material name/description
        # ph=pierce height
        # pd=pierce delay
        # ch=cut height
        # fr=feed rate
        # kw=kerf width
        # th=thc on (1) or off (0) 
        # ca=cut amps
        # cv=cut voltage
        # pe=pause at end
        # jh=puddle jump height
        # jd=puddle jump delay
        # mt=material thickness
        # mc=material type code
        #    Valid codes are:
        #    al -- aluminium
        #    ms -- steel
        #    ss -- stainless steel
        #    cp -- copper
        #    br -- brass
        self.comment = self.raw
        LOG.debug("Magic comment material parsing")
        line = self.raw.strip(" ()")
        # clean the line for processing.  It needs to be very specific
        line = re.sub(r",\s*", ",", line)
        parts = dict(item.split("=") for item in line.split(","))
        if int(parts['o']) != 0:
            LOG.debug("Magic comment material parsing - type set as PASSTHROUGH")
            self.type = Commands.PASSTHROUGH
        else:
            # mandatory
            LOG.debug("Magic comment material parsing - building out details to parent object")
            self._parent.pierce_height = float(parts['ph'])
            self._parent.pierce_delay = float(parts['pd'])
            self._parent.cut_height  = float(parts['ch'])
            self._parent.active_feedrate = self._parent.cut_speed = float(parts['fr'])
            # optional
            self._parent.active_thickness = float(parts.get('mt', 8/UNITS_PER_MM))
            LOG.debug(f"material parsing - thickness = {self._parent.active_thickness}")
            self._parent.process_name = parts.get('na', 'Automatic Process')
            self._parent.thc = int(parts.get('th', 0))
            self._parent.volts = float(parts.get('cv', 99))
            self._parent.kerf_width = float(parts.get('kw', 1.5/UNITS_PER_MM))
            self._parent.plunge_rate = 100
            self._parent.puddle_height = float(parts.get('jh', 0))
            self._parent.puddle_delay = float(parts.get('jd', 0))
            self._parent.amps = int(parts.get('ca', 40))
            self._parent.pressure = 90
            self._parent.pause_at_end = float(parts.get('pe', 0))
            self._parent.active_cutchart = 99999
            # now determine and set materialID and thicknessID from DB
            linear_system_list = PLASMADB.linearsystems()
            for linear_system in linear_system_list:
                if linear_system.name == UNITS:
                    linear_system_id = linear_system.id
            thickness_list = PLASMADB.thicknesses(linear_system_id)
            for thickness in thickness_list:
                if thickness.thickness == self._parent.active_thickness:
                    self._parent.active_thicknessid = thickness.id
            mat_code = parts.get('mc', None)
            if mat_code is not None:
                material_list = PLASMADB.materials()
                for mat in material_list:
                    if mat.code == mat_code:
                        self._parent.active_materialid = mat.id
            


    def parse_toolchange(self, combo=False):
        # A tool change is deemed a process change.
        # The Tool Number is to be the unique ID of a Process combination from
        # the CutChart table. This will need to be supported by the
        # CAM having a loading of tools where the tool #  is the
        # tool_number from this table but filtered by machine/units/pressure
        # so that tool_number is unique
        # Param: combo - if True then line has both Tx and M6
        line = self.strip_inline_comment(self.raw)
        if combo:
            f = re.findall(r"T\s*\d+|M6", line.upper().strip())
            # assume is in format Tx M6
            tool = int(re.split('T', f[0], 1)[1])
            self.type = Commands.PASSTHROUGH
        else:
            tool = int(re.split('T', line, 1)[1])
            self.command = ('T',tool)
            self.type = Commands.TOOLCHANGE
        # test if this process ID is known about
        cut_process = PLASMADB.tool_id(tool)
        LOG.debug(f"parse toolchange - tool = {tool}")
        if len(cut_process) == 0:
            # rewrite the raw line as an error comment
            self.raw = f"; ERROR: Invalid Cutchart ID in Tx. Check CAM Tools: {self.raw}"
            LOG.warn(f'Tool {tool} not a valid cut process in DB')
        else:
            self.cutchart_id = tool
            self._parent.active_cutchart = tool
            self._parent.active_feedrate = cut_process[0].cut_speed
            if tool != 99999:
                # only change tool if not magic tool as already set as part of magic comment
                self._parent.active_thickness = cut_process[0].thickness.thickness
            self._parent.active_machineid = cut_process[0].machineid
            self._parent.active_thicknessid = cut_process[0].thicknessid
            self._parent.active_materialid = cut_process[0].materialid
            

    def parse_feedrate(self):
        # assumption is that the feed is on its own line
        line = self.strip_inline_comment(self.raw)
        feed = float(re.split('F', line, 1)[1])
        if self._parent.active_feedrate is not None:
            feed = self._parent.active_feedrate
        self.command = ('F', feed)


    def set_inches(self):
        global UNITS_PER_MM
        UNITS_PER_MM = 25.4
        self.command = ('G', 20)


    def set_mms(self):
        global UNITS_PER_MM
        UNITS_PER_MM = 1
        self.command = ('G', 21)


    def cutter_comp_error(self):
        # cutter compensation detected.  Not supported by processor
        self.errors['compError'] = "Cutter compensation detected. \
                                    Ensure all compensation is baked into the tool path."
        print('ERROR:CUTTER_COMP:INVALID GCODE FOUND',file=sys.stderr)
        sys.stderr.flush()
        self.type = Commands.REMOVE

    def get_active_feedrate(self):
        return self._parent.active_feedrate

    def placeholder(self):
        LOG.debug(f'Type PLACEHOLDER -- {self.token} -- found - this code is not handled or considered')
        pass


class HoleBuilder:
    def __init__(self):
        self.torch_on = False
        self.elements = []

    # def degrees(self, rad):
    #     #convert radians to degrees to help decipher the angles
    #     return(rad *(180/pi))

    def line_length(self, x1, y1, x2, y2):
        a = (x2 - x1)**2
        b = (y2 - y1)**2
        s = a + b
        rtn = sqrt(s)
        return rtn

    def create_ccw_arc_gcode(self, x, y, rx, ry):
        return {
            "code": "G3",
            "x": x,
            "y": y,
            "i": rx,
            "j": ry
        }

    def create_cw_arc_gcode(self, x, y, rx, ry):
        return {
            "code": "G2",
            "x": x,
            "y": y,
            "i": rx,
            "j": ry
        }

    def create_line_gcode(self, x, y, rapid):
        return {
            "code": "G0" if rapid else "G1",
            "x": x,
            "y": y
        }

    def create_cut_on_off_gcode(self, cut_on, spindle=0):
        self.torch_on = cut_on
        return {
            "code": f"M3 ${spindle}" if cut_on else "M5 $-1"
        }

    def create_kerf_off_gcode(self):
        return {
            "code": "G40"
        }

    def create_comment(self, txt):
        return {
            "code": f"({txt})"
        }
        
    def create_debug_comment(self, txt):
        return {
            "code": f"({txt})" if DEBUG_COMMENTS else None
        }

    def create_dwell(self, t):
        # add a G4 Pn dwell between segments
        return {
             "code": f"G4 P{t}"
        }
        
    def create_feed(self, r):
        return {
            "code": f"F{r}"
        }
    
    def create_absolute_arc(self):
        return {
            "code": "G90.1"
        }

    def create_relative_arc(self):
        return {
            "code": "G91.1"
        }

    def create_thc_off_synch(self):
        return {
            "code": "M62 P2"
        }

    def create_thc_on_synch(self):
        return {
            "code": "M63 P2"
        }
        
    def create_relative(self):
        return {
            "code": "G91"
        }
    
    def create_absolute(self):
        return {
            "code": "G90"
        }
    
    def reset_feed(self):
        return {
            "code": "F#<_hal[plasmac.cut-feed-rate]>"}

    def element_to_gcode_line(self, e):
        if PRECISION == 4:
            xy = '{} x{:.4f} y{:.4f}'
            ij = ' i{:.4f} j{:.4f}'
        else:
            xy = '{} x{:.6f} y{:.6f}'
            ij = ' i{:.6f} j{:.6f}'
        
        if 'i' in e:
            line = (xy + ij).format(e['code'], e['x'], e['y'], e['i'], e['j'])
        elif 'x' in e:
            line = xy.format(e['code'], e['x'], e['y'])
        else:
            line = e['code']
        return line

    def plasma_mark(self, line, x, y, delay):
        self.elements=[]
        # feed_rate = line.get_active_feedrate()
        self.elements.append(self.create_comment('---- Marking/Spotting Start ----'))
        #self.elements.append(self.create_feed(feed_rate))
        self.elements.append(self.create_line_gcode(x, y, True))
        self.elements.append(self.create_cut_on_off_gcode(True, 2))
        self.elements.append(self.create_relative())
        self.elements.append(self.create_line_gcode((0.001/UNITS_PER_MM), 0, False))
        self.elements.append(self.create_absolute())
        #self.elements.append(self.create_dwell(delay *1.2))
        self.elements.append(self.create_cut_on_off_gcode(False))
        self.elements.append(self.create_comment('---- Marking/Spotting End ----'))

    def plasma_hole(self, line, x, y, d, kerf, leadin_radius, hidef_settings=None, hidef=False):
        # Params:
        # x:              Hole Centre X position
        # y:              Hole Centre y position
        # d:              Hole diameter
        # kerf:           Kerf width for cut
        # leadin_radius:  Radius for the lead in arc
        # splits[]:       List of length segments. Segments will support different speeds
        #                 and starting positions of the circle. Including overburn
        
        # Arc intersect calculation
        def arc_intersect(h1, k1, h2, k2, r1, r2):
            # h1,k1 = center of circle/arc 1
            # h2,k2 = center of circle/arc 2
            # r1 = radius of circle/arc 1
            # r2 = radius of circle/arc 2
            # distance between centres as L
            L = sqrt((h2-h1)**2 + (k2-k1)**2)
            # Calculate the distance 'a' from the center of the first circle
            # to the point between intersection points
            a = (r1**2 - r2**2 + L**2) / (2*L)
            # Calculate the distance 'b' from the line joining the centers
            # to the intersection points
            b = sqrt(r1**2 - a**2)
            x = h1 + (a*(h2-h1))/L + (b*(k2-k1))/L
            y = k1 + (a*(k2-k1))/L - (b*(h2-h1))/L
            return (x,y)

        
        LOG.debug('Build smart hole')
        #kerf compensation
        # often code is already compensated. We need to be able to tell the script if it is
        #changed the radius parameter to be ad diameter which is more in keeping with the hole data methodology
        feed_rate = line.get_active_feedrate()
        arc1_feed = feed_rate * hal.get_value('qtpyvcp.plasma-arc1-percent.out')/100
        arc2_feed = feed_rate * hal.get_value('qtpyvcp.plasma-arc2-percent.out')/100
        arc3_feed = feed_rate * hal.get_value('qtpyvcp.plasma-arc3-percent.out')/100
        overburn_feed = feed_rate * hal.get_value('qtpyvcp.plasma-overburn-percent.out')/100
        leadin_feed = feed_rate * hal.get_value('qtpyvcp.plasma-leadin-percent.out')/100

        straight_leadin = hal.get_value('qtpyvcp.plasma-force-straight-leadin.checked')
        kerf_adjusted = hal.get_value('qtpyvcp.plasma-is-kerf-compensated.checked')
        overburn_adjustment = hal.get_value('qtpyvcp.plasma-overburn-adjustment.out')/100

        if hidef and hidef_settings is not None:
            # over ride all the UI settings with the hidef data for hole build
            # "hidef_leadin_radius": hidef_leadin_radius,
            # "hidef_kerf": hidef_kerf,
            # "hidef_cutheight": hidef_cutheight,
            # "hidef_leadin_speed": hidef_leadin_speed,
            # "hidef_speed1": hidef_speed1,
            # "hidef_speed2": hidef_speed2,
            # "hidef_speed3": hidef_speed3,
            # "hidef_overburn_speed": hidef_overburn_speed,
            # "hidef_overburn_adjust": hidef_overburn_adjust,
            # "hidef_straight_leadin": hidef_straight_leadin
            kerf_adjusted = hidef_settings["hidef_kerf"]
            leadin_feed = hidef_settings["hidef_leadin_speed"]
            arc1_feed = hidef_settings["hidef_speed1"]
            arc2_feed = hidef_settings["hidef_speed2"]
            arc3_feed = hidef_settings["hidef_speed3"]
            overburn_feed = hidef_settings["hidef_overburn_speed"]
            overburn_adjustment = hidef_settings["hidef_overburn_adjust"]
            straight_leadin = hidef_settings["hidef_straight_leadin"]
            LOG.debug(f"HiDef settings applied to hole: {leadin_radius}")
            

        LOG.debug(f"Key params: kerf={kerf}, leadin_radius={leadin_radius}")

        # is G40 active or not
        if line.active_g_modal_groups[7] == 'G40':
            g40 = True
        else:
            g40 = False

        r = float(d) / 2.00
        kc = float(kerf) / 2.00
        # kerf larger than hole -> hole disappears
        # Mark that hole has been ignored with a comment.
        if kc > r:
            self.elements = []
            self.elements.append(self.create_comment('1/2 Kerf > Hole Radius.  Smart Hole processing skipped.'))
            return

        # convert split distances to angles (in radians)
        split_angles = []
        full_circle = pi * 2  # 360 degrees. We need to use this for a segment moving to 12 O'clock
        degs90 = pi / 2
        # crossed_origin = False
        # for spt in splits:
            # using the relationship of arc_length/circumfrance = angle/360 if you work the algebra you find:
            # angle = arc_length/radius (in radians)
            # tmp_ang = float(spt) / float(r)     # need to typecast to prevent Python from truncating to whole values, maybe should be double?
            # this_ang = tmp_ang    # Accoding to Juha, all angles are from 0 degrees, -ve angles to the right, +ve angles to the left
            # this_ang = full_circle + tmp_ang    # Accoding to Juha, all angles are from 0 degrees, -ve angles to the right, +ve angles to the left
            # if (this_ang > full_circle) and (crossed_origin == False):
            #     # Has this split got to the 0deg/360 deg  origin?
            #     # when we cross the origin, add a 360 degree keep it in the correct order
            #     split_angles.append(full_circle)
            #     this_ang = tmp_ang
            #     crossed_origin = True
            # split_angles.append(this_ang)
            # LOG.debug(f"Splits to angles: Split = {spt}, Angle = {this_ang} rad, {degrees(this_ang)} deg")
        #Sorting is not helpful with splits becasue the smaller values come before the first segment.
        #We need to keep segments in order

        # compensate hole radius and leadin radius if not already compensated code
        # Testing for g40 active.  HOWEVER using a G41/42 code causes so many lost plasmac featrues
        # why on earth would you use it?
        r = r if g40 and kerf_adjusted else r - kc
        leadin_radius = leadin_radius if g40 and kerf_adjusted else leadin_radius - kc
        LOG.debug(f"Adjusted leadin_radius={leadin_radius}")

        # the first real point of the hole (after leadin)
        arc_x0 = x
        arc_y0 = y + r
        # center for the final arc in an arc lead in
        leadin_arc_cx = None
        leadin_arc_cy = None
        # flag for leadin type
        is_straight_leadin = False

        # make sure gcode elements list is empty
        self.elements = []

        if line.active_g_modal_groups[4] == 'G91.1':
            self.elements.append(self.create_absolute_arc())
        if hidef:
            self.elements.append(self.create_comment('---- HiDef Hole ----'))
        self.elements.append(self.create_debug_comment(f'Hole Center x={x} y={y} r={r} leadin_r={leadin_radius}'))
        self.elements.append(self.create_debug_comment(f'First point on hole: x={arc_x0} y={arc_y0}'))
        self.elements.append(self.create_debug_comment(f'Leadin... Forced Straight = {straight_leadin}'))

        centre_to_leadin_diam_gap = fabs(arc_y0 - (2 * leadin_radius) - y)
        
        # set the lead in speed
        self.elements.append(self.create_feed(leadin_feed))
        # turn off the THC
        self.elements.append(self.create_thc_off_synch())

        # leadin radius too small or greater (or equal) than r.
        # --> use straight leadin from the hole center.
        if leadin_radius < 0 or leadin_radius >= r-kc or straight_leadin:
            LOG.debug("Build straight leadin")
            if straight_leadin:
                self.elements.append(self.create_debug_comment('forced straight leadin'))
            else:
                self.elements.append(self.create_debug_comment('too small'))
            self.elements.append(self.create_line_gcode(x, y, True))
            self.elements.append(self.create_kerf_off_gcode())
            # TORCH ON
            self.elements.append(self.create_cut_on_off_gcode(True))
            self.elements.append(self.create_line_gcode(arc_x0, arc_y0, False))
            is_straight_leadin = True

        # leadin radius <= r / 2.
        # --> use half circle leadin
        # done nothing here
        elif leadin_radius <= (r / 2):
            LOG.debug("Build radius leadin where leadin_radius <= r/2")
            self.elements.append(self.create_debug_comment('Half circle radius'))
            # rapid to hole centre
            self.elements.append(self.create_debug_comment(f'Half circle radius. Centre-to-Leadin-Gap={centre_to_leadin_diam_gap}'))
            if centre_to_leadin_diam_gap < kerf:
                LOG.debug("... single arc")
                self.elements.append(self.create_debug_comment('... single arc'))
                self.elements.append(self.create_line_gcode(x, y, True))
                self.elements.append(self.create_kerf_off_gcode())
                # TORCH ON
                self.elements.append(self.create_cut_on_off_gcode(True))
                self.elements.append(self.create_line_gcode(x, arc_y0 - 2 * leadin_radius, False))
                self.elements.append(self.create_ccw_arc_gcode(arc_x0, arc_y0, x, arc_y0 - leadin_radius))
            else:
                LOG.debug("... double back arc")
                self.elements.append(self.create_debug_comment('... double back arc'))
                self.elements.append(self.create_line_gcode(x, y, True))
                self.elements.append(self.create_kerf_off_gcode())
                # TORCH ON
                self.elements.append(self.create_cut_on_off_gcode(True))
                self.elements.append(self.create_cw_arc_gcode(x, y + centre_to_leadin_diam_gap, \
                                                              x, y + centre_to_leadin_diam_gap/2))
                self.elements.append(self.create_ccw_arc_gcode(arc_x0, arc_y0, x, arc_y0 - leadin_radius))
            leadin_arc_cx = x
            leadin_arc_cy = arc_y0 - leadin_radius
            LOG.debug(f"Half circle radius leading arc centre: {leadin_arc_cx} , {leadin_arc_cy}")

        # r/2 < leadin radius < r.
        # --> use combination of leadin arc and a smaller arc from the hole center
        else:
            # TODO:
            LOG.debug("Build radius leadin where leadin_radius > r/2")
            self.elements.append(self.create_debug_comment('Greater than Half circle radius'))
            self.elements.append(self.create_debug_comment(f'Half circle radius. Centre-to-Leadin-Gap={centre_to_leadin_diam_gap}'))

            if centre_to_leadin_diam_gap < kerf:
                LOG.debug("... single arc")
                self.elements.append(self.create_debug_comment('... single arc'))
                self.elements.append(self.create_line_gcode(x, y, True))
                self.elements.append(self.create_kerf_off_gcode())
                # TORCH ON
                self.elements.append(self.create_cut_on_off_gcode(True))
                self.elements.append(self.create_line_gcode(x, y - centre_to_leadin_diam_gap, False))
                self.elements.append(self.create_ccw_arc_gcode(arc_x0, arc_y0, x, arc_y0 - leadin_radius))
            else:
                LOG.debug("... double back arc")
                self.elements.append(self.create_debug_comment('... double back arc'))
                self.elements.append(self.create_line_gcode(x, y, True))
                self.elements.append(self.create_kerf_off_gcode())
                # TORCH ON
                self.elements.append(self.create_cut_on_off_gcode(True))
                self.elements.append(self.create_ccw_arc_gcode(x, y - centre_to_leadin_diam_gap, \
                                                              x, y - centre_to_leadin_diam_gap/2))
                self.elements.append(self.create_ccw_arc_gcode(arc_x0, arc_y0, x, arc_y0 - leadin_radius))
            leadin_arc_cx = x
            leadin_arc_cy = arc_y0 - leadin_radius
            LOG.debug(f"Greater than half circle radius leading arc centre: {leadin_arc_cx} , {leadin_arc_cy}")


            
            
            #leadin_diameter =  (leadin_radius + kc) * 2
            #from_centre = leadin_diameter - (r + kc)  # distance from centre
            # always start from centre of the hole
            #start1_x = x
            #startl_y = y
            #start1_y = r + from_centre  + kc # Y coordinate of start position
            
            # rapid to hole centre
            #self.elements.append(self.create_line_gcode(x, y , True))
            
            # self.elements.append(self.create_line_gcode(x, y-d/2 , True))
            # if abs(from_centre) < (kerf * 2):
            #      # no room for arc, use straight segment from hole centre
            #     self.elements.append(self.create_comment('no room for arc, use straight segment from hole centre...'))
            #     self.elements.append(self.create_line_gcode(start1_x, start1_y, False))
            # elif start1_y < r:
            #     # leadin diameter is shorter than hole radius, Use G2 for first arc
            #     self.elements.append(self.create_comment('leadin diameter is shorter than hole radius, Use G2 for first arc...'))
            #     self.elements.append(self.create_cw_arc_gcode(start1_x , start1_y, x, start1_y - from_centre))
            # else:
            #     #leadin diameter is longer than hole radius, Use G3 for first arc
            #     self.elements.append(self.create_comment('leadin diameter is longer than hole radius, Use G3 for first arc...'))
            #     self.elements.append(self.create_ccw_arc_gcode(x , -(leadin_diameter) , x, -(start1_y - from_centre/2)))
            # self.elements.append(self.create_ccw_arc_gcode(x , y - kc, x, -(leadin_diameter-(leadin_diameter - kc)/2)))

        self.elements.append(self.create_comment('Hole...'))
        #this has been reworked quite a bit. The original code was referring to the cursor X & Y positions and they needed to be the hole centre
        # TODO: not happy with this as it only works where x = 0 I think. Nees to be more robust
        cx = x
        cy = y
        # build the split angles
        inner_cut_radius = r - kc
        leadin_outer_cut_radius = leadin_radius + kc
        cut_end_angle = full_circle - kc/r + overburn_adjustment
        if is_straight_leadin:
            arc3_end_angle = full_circle - kerf/r
        else:
            arc3_end_x, arc3_end_y = \
                          arc_intersect(x, y, \
                                  leadin_arc_cx, leadin_arc_cy, \
                                  inner_cut_radius, leadin_outer_cut_radius)
            # calc arc3 end angle from x,y points, against hole centre
            arc3_end_angle = full_circle - atan2(arc3_end_y, arc3_end_x)
            LOG.debug(f"arc3 end x,y: {(arc3_end_x, arc3_end_y)}")
            
        if cut_end_angle <= arc3_end_angle:
            cut_end_angle = arc3_end_angle + radians(0.5)

        split_angles = \
            [radians(60), \
            arc3_end_angle - radians(60), \
            arc3_end_angle, \
            cut_end_angle]

        LOG.debug(f"arc3 end angle: {arc3_end_angle} rads,  {degrees(arc3_end_angle)} degs")
        LOG.debug(f"split angle list = {split_angles}")
        
        if len(split_angles) > 0:
            sector_num = 0
            prev_angle = 0.0
            for sang in split_angles:
                end_angle = sang
                end_x = ( cx + r * cos(end_angle + degs90))
                end_y = ( cy + r * sin(end_angle + degs90))
                if sang == full_circle or sang == 0:
                    #reset coordinates to 0,0 if angle = 360 degrees. We want the next segments to refer to 0 degrees
                    end_x = x
                    end_y = y + r
                # if sang < split_angles[0] and sang > 0.00:
                #     #conditional to coordinate positive angles
                #     end_x = (cx - r * math.cos(end_angle + degs90))
                #     end_y = (cy - r * math.sin(end_angle + degs90))
                #comment the code
                self.elements.append(self.create_debug_comment(f'Settings: end_angle {str(end_angle)} radians {str(degrees(end_angle))} degrees'))
                self.elements.append(self.create_comment(f'Sector number: {sector_num}'))
                # only process a sector if the angle is different from the previous sector.
                # same angle means 0 length sector and creating arc will generate odd behaviour
                if sang > prev_angle:
                    if sector_num == 0:
                        self.elements.append(self.create_feed(arc1_feed))
                    elif sector_num == 1:
                        self.elements.append(self.create_feed(arc2_feed))
                    elif sector_num == 2:
                        self.elements.append(self.create_feed(arc3_feed))
                    elif sector_num == 3:
                        self.elements.append(self.create_feed(overburn_feed))
                    self.elements.append(self.create_ccw_arc_gcode(end_x, end_y, cx, cy))
                else:
                    self.elements.append(self.create_comment(f'Sector number: {sector_num} collapased as angle smaller than previous sector'))
                    
                # if (end_x == 0.00 and end_y == 0.00) == False:
                #     #if not 12 O'clock, dwell for 0.5 sec so we have a visual indicator of each segment
                #     # we need to insert a call to a procedure that creates the required gcode actions at the end of each segment
                #     self.elements.append(self.create_dwell('0.5'))
                sector_num += 1
                prev_angle = sang
        else:
            # create hole as four arcs. no overburn or anything special.
            self.elements.append(self.create_ccw_arc_gcode(x-r, y, x, y))
            self.elements.append(self.create_ccw_arc_gcode(x, y-r, x, y))
            self.elements.append(self.create_ccw_arc_gcode(x+r, y, x, y))
            self.elements.append(self.create_ccw_arc_gcode(x, y+r, x, y))

        # TORCH OFF
        if self.torch_on:
            self.elements.append(self.create_cut_on_off_gcode(False))
        # turn on the THC
        self.elements.append(self.create_thc_on_synch())
        # reset feed rate
        # self.elements.append(self.create_feed(feed_rate))
        self.elements.append(self.reset_feed())
        if line.active_g_modal_groups[4] == 'G91.1':
            self.elements.append(self.create_relative_arc())

    def generate_hole_gcode(self):
        for e in self.elements:
            if e['code'] is not None:
                print(self.element_to_gcode_line(e), file=sys.stdout)
                sys.stdout.flush()


class PierceBuilder:
    def generate_pierce_gcode(self, line):
        print('M3 $0', file=sys.stdout)
        if line.active_g_modal_groups[3] == 'G90':
            # shift from absolute to relative
            print('G91', file=sys.stdout)
        # small wiggle
        print('G1 X0.0001', file=sys.stdout)
        if line.active_g_modal_groups[3] == 'G90':
            # shift back to absolute
            print('G90', file=sys.stdout)
        print('M5 $0', file=sys.stdout)
        sys.stdout.flush()


class HiDefHole:
    def __init__(self, data_list):
        self.hole_list = []
        for d in data_list:
            LOG.debug(f'HiDefHole init: data_list={data_list}')
            self.hole_list.append({'hole': d.hole_size, \
                                   'leadinradius': d.leadin_radius, \
                                   'kerf': d.kerf, \
                                   'cutheight': d.cut_height, \
                                   'leadin_speed': d.leadin_speed, \
                                   'speed1': d.speed1, \
                                   'speed2': d.speed2, \
                                   'speed3': d.speed3, \
                                   'overburn_speed': d.overburn_speed, \
                                   'overburn_adjust': d.overburn_adjust, \
                                   'straight_leadin': d.straight_leadin, \
                                   'amps': d.amps
                                   })
        # for i in range(len(self.hole_list)):
        #     # calculate the scale factors to use.
        #     # Factors are scaled over the diameter range of the hole
        #     if i > 0:
        #         delta = self.hole_list[i]['hole'] - self.hole_list[i-1]['hole']
        #         LOG.debug(f"HiDefHole init: delta calc.  i={i}, delta={delta}: {self.hole_list[i]['hole']} - {self.hole_list[i-1]['hole']}")
        #         self.hole_list[i]['scale_leadinradius'] = self.hole_list[i]['leadinradius']/delta
        #         self.hole_list[i]['scale_kerf'] = self.hole_list[i]['kerf']/delta       # why would kerf scale?
        #         self.hole_list[i]['scale_cutheight'] = self.hole_list[i]['cutheight']/delta
        #         self.hole_list[i]['scale_leadin_speed'] = self.hole_list[i]['leadin_speed']/delta
        #         self.hole_list[i]['scale_speed1'] = self.hole_list[i]['speed1']/delta
        #         self.hole_list[i]['scale_speed2'] = self.hole_list[i]['speed2']/delta
        #         self.hole_list[i]['scale_speed3'] = self.hole_list[i]['speed3']/delta
        #         self.hole_list[i]['scale_overburn_speed'] = self.hole_list[i]['overburn_speed']/delta
        #         self.hole_list[i]['scale_overburn_adjust'] = self.hole_list[i]['overburn_adjust']/delta

    def get_attribute(self, attribute, holesize):
        """
        Valid attributes:
            leadinradius
            kerf
            cutheight
            speed1
            speed2
            speed3
            overburn_speed
            overburn_adjust
            straight_leadin
        """
        for i in range(1, len(self.hole_list)):
            # exact matches so no need for scaling
            if self.hole_list[i-1]['hole'] == holesize:
                lr = self.hole_list[i-1][f'{attribute}']
                LOG.debug(f'HiDefHole get_attribute: holesize={holesize}, attribute={attribute}, lr={lr}')
                return lr

            if self.hole_list[i]['hole'] == holesize:
                lr = self.hole_list[i][f'{attribute}']
                LOG.debug(f'HiDefHole get_attribute: holesize={holesize}, attribute={attribute}, lr={lr}')
                return lr

            # hole is somwehere in a band between two sizes.  So need to scale some of the parameters
            # Scaling process for those attributes that do scale:
            # 1. get the bottom boundary metric
            # 2. get the delta of the metric and divide by the hole size delta. This give a scale per hole size unit
            # 3. test if metric changes between hole bounds.  If not then no scaling and use bottom value. Else do #4
            # 4. result:  (target_hole_size - bottom_boundry_hole_size) x metric_delta + bottom_boundary_metric             
            if self.hole_list[i-1]['hole'] <= holesize and holesize <= self.hole_list[i]['hole']:
                if attribute is 'straight_leadin':
                    lr = self.hole_list[i][f'{attribute}']
                    LOG.debug(f'HiDefHole get_attribute: holesize={holesize}, attribute={attribute}, lr={lr}')
                    return lr

                # test if there is a scaling task to be done or not
                if self.hole_list[i-1][f'{attribute}'] == self.hole_list[i][f'{attribute}']:
                    lr = self.hole_list[i-1][f'{attribute}']
                    LOG.debug(f'HiDefHole get_attribute: no scaling needed >> holesize={holesize}, attribute={attribute}, lr={lr}')
                    return lr

                bottom_boundary_metric = self.hole_list[i-1][f'{attribute}']
                top_boundary_metric = self.hole_list[i][f'{attribute}']
                metric_delta = top_boundary_metric - bottom_boundary_metric
                target_hole_size_delta = holesize - self.hole_list[i-1]['hole']
                hole_size_delta = self.hole_list[i]['hole'] - self.hole_list[i-1]['hole']
                metric_delta_scale = metric_delta / hole_size_delta

                # there is scaling to be done so calc this
                lr = target_hole_size_delta * metric_delta_scale + bottom_boundary_metric
                LOG.debug(f'HiDefHole get_attribute: scaled attribute >> holesize={holesize}, attribute={attribute}, lr={lr}')
                LOG.debug('HiDefHole get_attribute: scaling calc data:')
                LOG.debug(f'    >>  bottom_boundary_metric={bottom_boundary_metric}')
                LOG.debug(f'    >>  top_boundary_metric={top_boundary_metric}')
                LOG.debug(f'    >>  metric_delta={metric_delta}')
                LOG.debug(f'    >>  hole_size_delta={hole_size_delta}')
                LOG.debug(f'    >>  target_hole_size_delta={target_hole_size_delta}')
                LOG.debug(f'    >>  metric_delta_scale={metric_delta_scale}')
                return lr
            
        # catch all return in case its all fallen through
        LOG.debug('HiDefHole get_attribute: Return NONE')
        return None


    def leadin_radius(self, holesize):
        return self.get_attribute('leadinradius', holesize)
    
    def kerf(self, holesize):
        return self.get_attribute('kerf', holesize)
    
    def cut_height(self, holesize):
        return self.get_attribute('cutheight', holesize)

    def leadin_speed(self, holesize):
        return self.get_attribute('leadin_speed', holesize)
    
    def speed1(self, holesize):
        return self.get_attribute('speed1', holesize)
    
    def speed2(self, holesize):
        return self.get_attribute('speed2', holesize)
    
    def speed3(self, holesize):
        return self.get_attribute('speed3', holesize)
    
    def overburn_speed(self, holesize):
        return self.get_attribute('overburn_speed', holesize)
    
    def overburn_adjust(self, holesize):
        return self.get_attribute('overburn_adjust', holesize)
    
    def straight_leadin(self, holesize):
        return self.get_attribute('straight_leadin', holesize)
    

class PreProcessor:
    def __init__(self, inCode):
        self._new_gcode = []
        self._parsed = []
        self.preparsed = False
        self._line = ''
        self._line_num = 0
        self._line_type = 0
        self._orig_gcode = None
        self.active_g_modal_grps = {}
        self.active_m_modal_grps = {}
        self.active_cutchart = None
        self.active_feedrate = None
        self.active_thickness = None
        self.active_machineid = None
        self.active_thicknessid = None
        # self.active_materialid = hal.get_value('qtpyvcp.material-id')
        self.active_materialid = None
        # used for Magic material/process system
        self.process_name = None
        self.pierce_height = None
        self.pierce_delay = None
        self.cut_height  = None
        self.cut_speed = None
        self.volts = None
        self.kerf_width = None
        self.plunge_rate = None
        self.puddle_height = None
        self.puddle_delay = None
        self.amps = None
        self.pressure = None
        self.pause_at_end = None
        self.thc = None
        # track if flip or mirror is active
        self.g2g3_flip = False

        # find the active machine from the ini string
        machine_name = INI.find('PLASMAC', 'MACHINE')
        machine_list = PLASMADB.machines()
        for machine in machine_list:
            LOG.debug(f"machines in machine_list:{machine}")
            if machine.name == machine_name:
                self.active_machineid = machine.id

        openfile= open(inCode, 'r')
        self._orig_gcode = openfile.readlines()
        openfile.close()
        
        # Test to see if the file has been previously parsed by this processor
        # This test is agnostic of the version of the preprocessor
        line1 = self._orig_gcode[0]
        line2 = self._orig_gcode[1]
        
        if line1 == '(--------------------------------------------------)\n':
            LOG.debug("Line1 HAS pre parse match")
            if line2 == '(            Plasma G-Code Preprocessor            )\n':
                LOG.debug("Line2 HAS pre parse match")
                self.preparsed = True
            else:
                LOG.debug("Line2 not have pre parse match")
        else:
            LOG.debug("Line1 not have pre parse match")


    def set_active_g_modal(self, gcode):
        # get the modal grp for the code and set things
        # if a code is not found then nothing will be set
        for g_modal_grp in G_MODAL_GROUPS:
            if gcode in G_MODAL_GROUPS[g_modal_grp]:
                self.active_g_modal_grps[g_modal_grp] = gcode
                break


    def active_motion_code(self):
        try:
            return self.active_g_modal_grps[1]
        except Exception as e:
            LOG.info(f'Active motion code issue: {e}')
            return None


    def flag_holes(self):
        LOG.debug("Start Gather info from HAL pins")
        # connect to HAL and collect the data we need to determine what holes
        # should be processes and what are too large
        thickness_ratio = hal.get_value('qtpyvcp.plasma-hole-thickness-ratio.out')
        max_hole_size = hal.get_value('qtpyvcp.plasma-max-hole-size.out')
        
        # arc1_feed_percent = hal.get_value('qtpyvcp.plasma-arc1-percent.out')/100
        
        # arc2_distance = hal.get_value('qtpyvcp.plasma-arc2-distance.out')
        # arc2_feed_percent = hal.get_value('qtpyvcp.plasma-arc2-percent.out')/100
        
        # arc3_distance = hal.get_value('qtpyvcp.plasma-arc3-distance.out')
        # arc3_feed_percent = hal.get_value('qtpyvcp.plasma-arc3-percent.out')/100

        # overburn_adjustment = hal.get_value('qtpyvcp.plasma-overburn-distance.out')
        # overburn_distance = hal.get_value('qtpyvcp.plasma-overburn-distance.out')
        # arc3_feed_percent = hal.get_value('qtpyvcp.plasma-arc3-percent.out')/100
        
        # leadin_feed_percent = hal.get_value('qtpyvcp.plasma-leadin-percent.out')/100
        leadin_radius = hal.get_value('qtpyvcp.plasma-leadin-radius.out')
        
        kerf_width = hal.get_value('qtpyvcp.param-kirfwidth.out')
        hole_kerf = hal.get_value('qtpyvcp.plasma-hole-kerf.out')
        if hole_kerf != 0:
            kerf_width = hole_kerf
            LOG.debug(f"Hole Kerf is non Zero [{hole_kerf}].  Kerf aligned to Hole Kerh.  Kerf={kerf_width}")


        # overburn_start_distance_before_zero = hal.get_value('qtpyvcp.plasma-overburn-start-distance.out')
                
        small_hole_size = 0
        small_hole_detect = hal.get_value('qtpyvcp.plasma-small-hole-detect.checked')
        if small_hole_detect:
            small_hole_size = hal.get_value('qtpyvcp.plasma-small-hole-threshold.out')
            
        # marking_voltage = hal.get_value('qtpyvcp.spot-threshold.out')
        marking_delay = hal.get_value('qtpyvcp.spot-delay.out')
        LOG.debug("Got all info from HAL pins")
        
        # old school loop so we can easily peek forward or back of the current
        # record being processed.
        LOG.debug("Start scanning loop")
        i = 0
        while i < len(self._parsed):
            line = self._parsed[i]
            if len(line.command) == 2:
                if line.command[0] == 'G' and line.command[1] == 3:
                    # this could be a hole, test for it.
                    # NB: Only circles that are defined as cww are deemed to be
                    # a hole.  cw (G2) cuts are deemed as an outer edge not inner.
                                        
                    #[1] find the last X and Y position while grp 1 was either G0 or G1
                    j = i-1
                    for j in range(j, -1, -1):
                        prev = self._parsed[j]
                        # is there an X or Y in the line
                        if 'X' in prev.params.keys() and prev.active_g_modal_groups[1] in ('G0','G1','G2','G3'):
                            lastx = prev.params['X']
                            break
                    j = i-1
                    for j in range(j, -1, -1):
                        prev = self._parsed[j]
                        # is there an X or Y in the line
                        if 'Y' in prev.params.keys() and prev.active_g_modal_groups[1] in ('G0','G1','G2','G3'):
                            lasty = prev.params['Y']
                            break
                    endx = line.params['X'] if 'X' in line.params.keys() else lastx
                    endy = line.params['Y'] if 'Y' in line.params.keys() else lasty
                    if endx == lastx and endy == lasty:
                        line.is_hole = True
                    else:
                        line.is_hole = False

                    # if line is a hole then prepare to replace
                    # with "smart" holes IF it is within the upper params of a
                    # hole definition.  Nomally <= 5 * thickness
                    if line.is_hole:
                        LOG.debug("Found a Hole. Start HoleBuilder")
                        line.hole_builder = HoleBuilder()
                        arc_i = line.params.get('I', 0)
                        arc_j = line.params.get('J', 0)
                        centre_x = endx + arc_i
                        centre_y = endy + arc_j
                        radius = line.hole_builder.line_length(centre_x, centre_y,endx, endy)
                        diameter = 2 * fabs(radius)
                        circumferance = diameter * pi
                        
                        # see if can find hidef data for this hole scenario
                        if self.active_materialid is not None:
                            LOG.debug(f"Look for HiDef data on this machine/material/thickness {(self.active_machineid, self.active_materialid, self.active_thicknessid)}")
                            hidef_data = PLASMADB.hidef_holes(self.active_machineid, self.active_materialid, self.active_thicknessid)
                        else:
                            hidef_data = []
                        hidef = False
                        LOG.debug(f"Finished hidef data look. Found {len(hidef_data)}")
                        if len(hidef_data) > 0:
                            LOG.debug("Building up hidef hole defintion")
                            # leadin_radius = Column(Float)
                            # kerf = Column(Float)
                            # cut_height = Column(Float)
                            # leadin_speed = Column(Float)
                            # speed1 = Column(Float)
                            # speed2 = Column(Float)
                            # speed3 = Column(Float)
                            # overburn_speed = Column(Float)
                            # overburn_adjust = Column(Float)
                            # straight_leadin = Column(Boolean)

                            hidef_hole = HiDefHole(hidef_data)
                            hidef_leadin_radius = hidef_hole.leadin_radius(diameter)
                            hidef_kerf = hidef_hole.kerf(diameter)
                            hidef_cutheight = hidef_hole.cut_height(diameter)
                            hidef_leadin_speed = hidef_hole.leadin_speed(diameter)
                            hidef_speed1 = hidef_hole.speed1(diameter)
                            hidef_speed2 = hidef_hole.speed2(diameter)
                            hidef_speed3 = hidef_hole.speed3(diameter)
                            hidef_overburn_speed = hidef_hole.overburn_speed(diameter)
                            hidef_overburn_adjust = hidef_hole.overburn_adjust(diameter)
                            hidef_straight_leadin = hidef_hole.straight_leadin(diameter)
                            if None not in (hidef_leadin_radius, hidef_kerf, \
                                            hidef_cutheight, hidef_leadin_speed, hidef_speed1, \
                                            hidef_speed2, hidef_speed3, \
                                            hidef_overburn_speed, hidef_overburn_adjust, \
                                            hidef_straight_leadin):
                                hidef = True
                            LOG.debug(f"HiDef status is {hidef}")
                        
                        if diameter < small_hole_size and small_hole_detect:
                            # removde the hole and replace with a pulse
                            LOG.debug("Hole diamter smaller the small-hole.  Remove hole and replace with pulse")
                            line.hole_builder.\
                                plasma_mark(line, centre_x, centre_y, marking_delay)
                            # scan forward and back to mark the M3 and M5 as Coammands.REMOVE
                            j = i-1
                            found_m3 = False
                            for j in range(j, -1, -1):
                                prev = self._parsed[j]
                                # mark for removal any lines until find the M3
                                if prev.token.startswith('M3'):
                                    found_m3 = True
                                    prev.type = Commands.REMOVE
                                if not found_m3:
                                    prev.type = Commands.REMOVE
                                try:
                                    if prev.active_g_modal_groups[1] != 'G0' and found_m3:
                                        break
                                    elif prev.active_g_modal_groups[1] == 'G0':
                                        prev.type = Commands.REMOVE
                                except KeyError:
                                    # access to the dictionary index failed,
                                    # so no longer in a g0 mode
                                    break
                            j = i+1
                            for j in range(j, len(self._parsed)):
                                next = self._parsed[j]
                                # mark all lines for removal until find M5
                                next.type = Commands.REMOVE
                                if next.token.startswith('M5'):
                                    next.type = Commands.REMOVE
                                    break
                        elif hidef:
                            LOG.debug("Build a hole using hidef data")
                            #TODO: fix for 3 segments and overburn
                            # hidef_leadin_radius = hidef_hole.leadin_radius(diameter)
                            # hidef_kerf = hidef_hole.kerf(diameter)
                            # hidef_cutheight = hidef_hole.cut_height(diameter)
                            # hidef_leadin_speed = hidef_hole.leadin_speed(diameter)
                            # hidef_speed1 = hidef_hole.speed1(diameter)
                            # hidef_speed2 = hidef_hole.speed2(diameter)
                            # hidef_speed3 = hidef_hole.speed3(diameter)
                            # hidef_overburn_speed = hidef_hole.overburn_speed(diameter)
                            # hidef_overburn_adjust = hidef_hole.overburn_adjust(diameter)
                            # hidef_straight_leadin = hidef_hole.straight_leadin(diameter)
                            hidef_settings = {
                                "hidef_leadin_radius": hidef_leadin_radius,
                                "hidef_kerf": hidef_kerf,
                                "hidef_cutheight": hidef_cutheight,
                                "hidef_leadin_speed": hidef_leadin_speed,
                                "hidef_speed1": hidef_speed1,
                                "hidef_speed2": hidef_speed2,
                                "hidef_speed3": hidef_speed3,
                                "hidef_overburn_speed": hidef_overburn_speed,
                                "hidef_overburn_adjust": hidef_overburn_adjust,
                                "hidef_straight_leadin": hidef_straight_leadin
                                }
                            line.hole_builder.\
                                plasma_hole(line, centre_x, centre_y, diameter, \
                                            hidef_kerf, hidef_leadin_radius, \
                                            hidef_settings, hidef)
                            
                            # scan forward and back to mark the M3 and M5 as Coammands.REMOVE
                            j = i-1
                            found_m3 = False
                            for j in range(j, -1, -1):
                                prev = self._parsed[j]
                                # mark for removal any lines until find the M3
                                if prev.token.startswith('M3'):
                                    found_m3 = True
                                    prev.type = Commands.REMOVE
                                if not found_m3:
                                    prev.type = Commands.REMOVE
                                try:
                                    if prev.active_g_modal_groups[1] != 'G0' and found_m3:
                                        break
                                    elif prev.active_g_modal_groups[1] == 'G0':
                                        prev.type = Commands.REMOVE
                                except KeyError:
                                    # access to the dictionary index failed,
                                    # so no longer in a g0 mode
                                    break
                            j = i+1
                            for j in range(j, len(self._parsed)):
                                next = self._parsed[j]
                                # mark all lines for removal until find M5
                                next.type = Commands.REMOVE
                                if next.token.startswith('M5'):
                                    next.type = Commands.REMOVE
                                    break
                            
                        elif (diameter <= self.active_thickness * thickness_ratio) or \
                           (diameter <= max_hole_size):
                            LOG.debug("Build a normal hole using UI params")
                            # Only build the hole of within a certain size of
                            # Params:
                            # x:              Hole Centre X position
                            # y:              Hole Centre y position
                            # d:              Hole diameter
                            # kerf:           Kerf width for cut
                            # leadin_radius:  Radius for the lead in arc
                            # splits[]:       List of length segments. Segments will support different speeds. +ve is left of 12 o'clock
                            #                 -ve is right of 12 o'clock
                            #                 and starting positions of the circle. Including overburn
                            if leadin_radius == 0:
                                this_hole_leadin_radius = radius-(radius/4)-(kerf_width/2)
                            else:
                                this_hole_leadin_radius = leadin_radius
                                
                            # arc1_distance = circumferance - arc2_distance - arc3_distance - overburn_start_distance_before_zero
                            # arc2_from_zero = arc1_distance + arc2_distance
                            # arc3_from_zero = arc2_from_zero + arc3_distance
                            # overburn_from_zero = arc3_from_zero + overburn_distance - circumferance
                            # overburn_from_zero = arc3_from_zero + overburn_distance
                            line.hole_builder.\
                                plasma_hole(line, centre_x, centre_y, diameter, \
                                            kerf_width, this_hole_leadin_radius)
                            
                            # scan forward and back to mark the M3 and M5 as Coammands.REMOVE
                            j = i-1
                            found_m3 = False
                            for j in range(j, -1, -1):
                                prev = self._parsed[j]
                                # mark for removal any lines until find the M3
                                if prev.token.startswith('M3'):
                                    found_m3 = True
                                    prev.type = Commands.REMOVE
                                if not found_m3:
                                    prev.type = Commands.REMOVE
                                try:
                                    if prev.active_g_modal_groups[1] != 'G0' and found_m3:
                                        break
                                    elif prev.active_g_modal_groups[1] == 'G0':
                                        prev.type = Commands.REMOVE
                                except KeyError:
                                    # access to the dictionary index failed,
                                    # so no longer in a g0 mode
                                    break
                            j = i+1
                            for j in range(j, len(self._parsed)):
                                next = self._parsed[j]
                                # mark all lines for removal until find M5
                                next.type = Commands.REMOVE
                                if next.token.startswith('M5'):
                                    next.type = Commands.REMOVE
                                    break
                        else:
                            line.is_hole = False
                            line.hole_builder = None
            i += 1

    def flag_pierce(self):
        # old school loop so we can easily peek forward or back of the current
        # record being processed.
        i = 0
        while i < len(self._parsed):
            line = self._parsed[i]
            if len(line.command) == 2:
                if line.command[0] == 'M' and line.command[1] == 3:
                    # this is a torce start so must be a pierce.
                    line.is_pierce = True
                    line.pierce_builder = PierceBuilder()
                            
                    # scan forward to find the M5 and remove all the 
                    # stuff in the moddle using Coammands.REMOVE
                    # Aadd in a wiggle for the pierce 
                    j = i+1
                    for j in range(j, len(self._parsed)):
                        next = self._parsed[j]
                        # mark all lines for removal until find M5
                        next.type = Commands.REMOVE
                        if next.token.startswith('M5'):
                            next.type = Commands.REMOVE
                            break
            i += 1
        

    def parse(self):
        # Build Header for parsed file
        self._parsed.append(CodeLine( '(--------------------------------------------------)', parent=self))
        self._parsed.append(CodeLine( '(            Plasma G-Code Preprocessor            )', parent=self))
        self._parsed.append(CodeLine(f'(                 {PREPROC_VERSION}                            )', parent=self))
        self._parsed.append(CodeLine( '(--------------------------------------------------)', parent=self))
        # Build inputs for scale, tiles, flip, mirror and rotation
        self._parsed.append(CodeLine( ';inputs', parent=self))
        self._parsed.append(CodeLine( '#<ucs_x_offset> = [#5221 + [[#5220-1] * 20]]', parent=self))
        self._parsed.append(CodeLine( '#<ucs_y_offset> = [#5222 + [[#5220-1] * 20]]', parent=self))
        self._parsed.append(CodeLine( '#<ucs_r_offset> = [#5230 + [[#5220-1] * 20]]', parent=self))
        self._parsed.append(CodeLine( f'#<array_x_offset> = {hal.get_value("qtpyvcp.column-separation.out")}', parent=self))
        self._parsed.append(CodeLine( f'#<array_y_offset> = {hal.get_value("qtpyvcp.row-separation.out")}', parent=self))
        self._parsed.append(CodeLine( f'#<array_columns> = {hal.get_value("qtpyvcp.tile-columns.out")}', parent=self))
        self._parsed.append(CodeLine( f'#<array_rows> = {hal.get_value("qtpyvcp.tile-rows.out")}', parent=self))
        self._parsed.append(CodeLine( '#<origin_x_offset> = 0.0', parent=self))
        self._parsed.append(CodeLine( '#<origin_y_offset> = 0.0', parent=self))
        self._parsed.append(CodeLine( '#<array_angle> = 0.0', parent=self))
        self._parsed.append(CodeLine( f'#<blk_scale> = {hal.get_value("qtpyvcp.gcode-scale.out")}', parent=self))
        self._parsed.append(CodeLine( f'#<shape_angle> = {hal.get_value("qtpyvcp.gcode-rotation.out")}', parent=self))

        if hal.get_value("qtpyvcp.gcode-mirror.checked"):
            self._parsed.append(CodeLine( '#<shape_mirror> = -1', parent=self))
            self.g2g3_flip = not self.g2g3_flip
        else:
            self._parsed.append(CodeLine( '#<shape_mirror> = 1', parent=self))

        if hal.get_value("qtpyvcp.gcode-flip.checked"):
            self._parsed.append(CodeLine( '#<shape_flip> = -1', parent=self))
            self.g2g3_flip = not self.g2g3_flip
        else:
            self._parsed.append(CodeLine( '#<shape_flip> = 1', parent=self))
        
        self._parsed.append(CodeLine( ';calculations', parent=self))
        self._parsed.append(CodeLine( '#<this_col> = 0', parent=self))
        self._parsed.append(CodeLine( '#<this_row> = 0', parent=self))
        self._parsed.append(CodeLine( '#<array_rot> = [#<array_angle> + #<ucs_r_offset>]', parent=self))
        self._parsed.append(CodeLine( '#<blk_x_offset> = [#<origin_x_offset> + [#<ucs_x_offset> * 1]]', parent=self))
        self._parsed.append(CodeLine( '#<blk_y_offset> = [#<origin_y_offset> + [#<ucs_y_offset> * 1]]', parent=self))
        self._parsed.append(CodeLine( '#<x_sin> = [[#<array_x_offset> * #<blk_scale>] * SIN[#<array_rot>]]', parent=self))
        self._parsed.append(CodeLine( '#<x_cos> = [[#<array_x_offset> * #<blk_scale>] * COS[#<array_rot>]]', parent=self))
        self._parsed.append(CodeLine( '#<y_sin> = [[#<array_y_offset> * #<blk_scale>] * SIN[#<array_rot>]]', parent=self))
        self._parsed.append(CodeLine( '#<y_cos> = [[#<array_y_offset> * #<blk_scale>] * COS[#<array_rot>]]', parent=self))
        self._parsed.append(CodeLine( '', parent=self))

        self._parsed.append(CodeLine( ';main loop', parent=self))
        self._parsed.append(CodeLine( 'o<loop> while [#<this_row> LT #<array_rows>]', parent=self))
        self._parsed.append(CodeLine( '#<shape_x_start> = [[#<this_col> * #<x_cos>] - [#<this_row> * #<y_sin>] + #<blk_x_offset>]', parent=self))
        self._parsed.append(CodeLine( '#<shape_y_start> = [[#<this_row> * #<y_cos>] + [#<this_col> * #<x_sin>] + #<blk_y_offset>]', parent=self))
        self._parsed.append(CodeLine( '#<blk_angle> = [#<shape_angle> + #<array_rot>]', parent=self))
        self._parsed.append(CodeLine( 'G10 L2 P0 X#<shape_x_start> Y#<shape_y_start> R#<blk_angle>', parent=self))     
        
        # setup any global default modal groups that we need to be aware of
        self.set_active_g_modal('G91.1')
        self.set_active_g_modal('G40')
        # start parsing through the loaded file
        for line in self._orig_gcode:
            self._line_num += 1
            self._line = line.strip()
            LOG.debug('Parse: Build gcode line.')
            cline = CodeLine(self._line, parent=self, g2g3flip=self.g2g3_flip)
            # try:
            #     gcode = f'{cline.command[0]}{cline.command[1]}'
            # except Exception as e:
            #     LOG.info(f'Gcode command parse issue: {e}')
            #     gcode = ''
            self.set_active_g_modal(cline.token)
            cline.save_g_modal_group(self.active_g_modal_grps)
            self._parsed.append(cline)

    def dump_raw(self):
        LOG.debug('Dump raw gcode to stdio')
        for line in self._orig_gcode:
            print(line, file=sys.stdout, end="")
            sys.stdout.flush()
            

    def dump_parsed(self):
        LOG.debug('Dump parsed gcode to stdio')
        for line in self._parsed:
            #print(f'{l.type}\t\t -- {l.command} \
            #    {l.params} {l.comment}')
            # build up line to go to stdout
            if line.is_hole:
                print('(---- Smart Hole Start ----)')
                line.hole_builder.generate_hole_gcode()
                print('(---- Smart Hole End ----)')
                print()
                continue
            if line.is_pierce:
                print('(---- Pierce ----)')
                line.pierce_builder.generate_pierce_gcode(line)
                continue
            if line.type in [Commands.COMMENT, Commands.MAGIC_MATERIAL]:
                out = line.comment
                if out == ';end post-amble':
                    out += """
                    
#<this_col> = [#<this_col> + 1]
o<count> if [#<this_col> EQ #<array_columns>]
    #<this_col> = 0
    #<this_row> = [#<this_row> + 1]
o<count> endif
o<loop> endwhile

G10 L2 P0 X[#<ucs_x_offset> * 1] Y[#<ucs_y_offset> * 1] R#<ucs_r_offset>
                    """
            elif line.type is Commands.OTHER:
                # Other at the moment means not recognised
                out = "; >>  "+line.raw
            elif line.type in [Commands.PASSTHROUGH, Commands.RAW]:
                out = line.raw
            elif line.type is Commands.REMOVE:
                # skip line as not to be used
                out = ''
                continue
            else:
                try:
                    out = f"{line.command[0]}{line.command[1]}"
                except Exception as e:
                    LOG.info(f'Gcode parse issue: {e}')
                    out = ''
                try:
                    for p in line.params:
                        vars = ''
                        if p == 'X':
                            vars = '#<blk_scale>*#<shape_mirror>'
                        elif p == 'Y':
                            vars = '#<blk_scale>*#<shape_flip>'
                        elif p == 'I':
                            vars = '#<blk_scale>*#<shape_mirror>'
                        elif p == 'J':
                            vars = '#<blk_scale>*#<shape_flip>'
                        if isinstance(line.params[p], float):
                            if line.params[p] < 0.001:
                                out += f' {p}[{line.params[p]:.6f}*{vars}]'
                            else:
                                out += f' {p}[{line.params[p]:.3f}*{vars}]'
                        else:
                            out += f' {p}{line.params[p]}'
                    out += f' {line.comment}'
                    out = out.strip()
                except Exception as e:
                    LOG.info(f'GCode parse issue: {e}')
                    out = ''
            #LOG.debug(f"Dump line >>> {out}")
            print(out, file=sys.stdout)
            sys.stdout.flush()

    def set_ui_hal_cutchart_pin(self):
        if self.active_cutchart is not None and self.active_cutchart != 99999:
            hal.set_p("qtpyvcp.cutchart-id", f"{self.active_cutchart}")
            LOG.debug(f'Set hal cutchart-id pin: {self.active_cutchart}')
        elif self.active_cutchart == 99999:
            # custom material type has been set via magic comment, configure
            # the DB entry and save, then update the cutchard ID pin to activate
            LOG.debug("Process for magic process tool 99999")
            q = PLASMADB.tool_id(99999)
            if q is not None:
                LOG.debug("Magic tool 99999 found. Updating")
                # find the linera system ID
                linear_systems = PLASMADB.linearsystems()
                for lsys in linear_systems:
                    if lsys.name == UNITS:
                        linear_sys_id = lsys.id
                        break
                    else:
                        linear_sys_id = None
                LOG.debug(f"Linear System ID = {linear_sys_id}")
                thicknesses_list = PLASMADB.thicknesses(measureid=linear_sys_id)
                LOG.debug(f"active thickness = {self.active_thickness}")
                for thick in thicknesses_list:
                    LOG.debug(f"thick.name: {thick.name}   thick.thickness: {thick.thickness}")
                    if thick.thickness == self.active_thickness:
                        thickness_id = thick.id
                        thickness_name = thick.name
                        break
                    else:
                        thickness_id = None
                        thickness_name = None
                LOG.debug(f"Thickness ID = {thickness_id}")
                # def updateCut(self, q, **args):
                #     Cutchart.update(self._session, q, \
                #             pierce_height = args['pierce_height'], \
                #             pierce_delay = args['pierce_delay'], \
                #             cut_height = args['cut_height'], 
                #             cut_speed = args['cut_speed'], \
                #             volts = args['volts'], \
                #             kerf_width = args['kerf_width'], \
                #             plunge_rate = args['plunge_rate'], \
                #             puddle_height = args['puddle_height'], \
                #             puddle_delay = args['puddle_delay'], \
                #             amps = args['amps'], \
                #             pressure = args['pressure'], \
                #             pause_at_end = args['pause_at_end'])
                PLASMADB.updateCut(q,
                                   name=f'Auto Material {thickness_name}',
                                   thicknessid=thickness_id,
                                   pierce_height=self.pierce_height,
                                   pierce_delay=self.pierce_delay,
                                   cut_height=self.cut_height,
                                   cut_speed=self.cut_speed,
                                   volts=self.volts,
                                   kerf_width=self.kerf_width,
                                   plunge_rate=self.plunge_rate,
                                   puddle_height=self.puddle_height,
                                   puddle_delay=self.puddle_delay,
                                   amps=self.amps,
                                   pressure=self.pressure,
                                   pause_at_end=self.pause_at_end)
                LOG.debug("Magic tool 99999 Updated.")
            else:
                # query for tool was empty so we need to create the magic
                LOG.debug("ISSUE: The Magic tool 99999 does not exist!")
            
            hal.set_p("qtpyvcp.cutchart-id", "99999")
            LOG.debug('Set hal cutchart-id pin: 99999')
            hal.set_p("qtpyvcp.cutchart-reload", "1")
        else:
            LOG.debug('No active cutchart')


def main():
    global PLASMADB

    try:
        inCode = sys.argv[1]
        LOG.debug(f'File to process: {inCode}')
    except Exception as e:
        # no arg found, probably being run from command line and someone forgot a file
        LOG.info(f'Arg call issue: {e}')
        print(__doc__)
        return

    if len(inCode) == 0 or '-h' == inCode:
        print(__doc__)
        return

    custom_config_yaml_file_name = normalizePath(path='custom_config.yml', base=os.getenv('CONFIG_DIR', '~/'))
    cfg_dic = load_config_files(custom_config_yaml_file_name)
    LOG.debug(f'Log custom config yaml file: {custom_config_yaml_file_name}')
    
    # we assume that things are sqlite unless we find custom_config.yml
    # pointing to different type of DB
    try:
        db_connect_str = cfg_dic['data_plugins']['plasmaprocesses']['kwargs']['connect_string']
        # if no error then we found a db connection string. Use it.
        PLASMADB = PlasmaProcesses(connect_string=db_connect_str)
        LOG.debug(f'Connected to NON SQLite DB: {db_connect_str}')
    except Exception as e:
        # no connect string found OR can't connect so assume sqlite on local machine
        LOG.debug(f'Connection issue to SQL DB: {e}')
        PLASMADB = PlasmaProcesses(db_type='sqlite')
        LOG.debug('Connected to SQLite DB')

    # Start cycling through each line of the file and processing it
    LOG.debug('Build preprocessor object and process gcode')
    p = PreProcessor(inCode)
    if not p.preparsed:
        p.parse()
        LOG.debug('Parsing done.')
    else:
        LOG.debug('File is Preparsed.')

    if not p.preparsed:
        # Holes flag
        try:
            do_holes = hal.get_value('qtpyvcp.plasma-hole-detect-enable.checked')
        except Exception as e:
            LOG.debug(f'Hal pin query issue: {e}')
            do_holes = False
        
        # Pierce only flag
        try:
            do_pierce = hal.get_value('qtpyvcp.plasma-pierce-only-enable.checked')
        except Exception as e:
            LOG.debug(f'Hal pin query issue: {e}')
            do_pierce = False
        
        if do_holes and not do_pierce:
            LOG.debug('Flag holes ...')
            p.flag_holes()
            LOG.debug('... Flag holes done')
        elif do_pierce:
            LOG.debug('Flag piercing ...')
            p.flag_pierce()
            LOG.debug('... Flag piercing done')
    
        # pass file to stdio and set any hal pins
        LOG.debug('Dump parsed file')
        p.dump_parsed()
        # Set hal pin on UI for cutchart.id
        LOG.debug('Set UI param data via cutchart pin')
        p.set_ui_hal_cutchart_pin()
    else:
        p.dump_raw()
    
    # Close out DB
    PLASMADB.terminate()
    LOG.debug('Plasma DB closed and end.')


if __name__ == '__main__':
    # to run from command line for debug purposes
    # must [1] start up an insitance of monokrom plasma
    # [2] set following env variables from the command line
    # where you plan to run the parse from:
    # export CONFIG_DIR=
    # export INIFILE_NAME=
    #
    # The easy way if using the monokrom sim is to cd to
    # the ~/linuxcnc/configs/sim.monokrom/plasmac/ and perform
    # export CONFIG_DIR=`pwd`
    # export INI_FILE_NAME=`pwd`/xyz.ini
    main()

