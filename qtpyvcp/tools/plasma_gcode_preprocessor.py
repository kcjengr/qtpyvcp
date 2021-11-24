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
import math
from enum import Enum, auto
from typing import List, Dict, Tuple, Union

import hal
from qtpyvcp.plugins.plasma_processes import PlasmaProcesses
from qtpyvcp.utilities.logger import initBaseLogger

#import pydevd;pydevd.settrace()


# Constrcut LOG from qtpyvcp standard logging framework
LOG = initBaseLogger('qtpyvcp.tools.plasma_gcode_preprocessor')

# force the python HAL lib to load/init. Not doing this causes a silent "crash"
# when trying to set a hal pin
try:
    h = hal.component('dummy')
    LOG.debug('Python HAL is available')
except:
    LOG.warn('Python HAL is NOT available')


# Define some globals that will be referenced from anywhere
# assumption is MM's is the base unit of reference.
UNITS_PER_MM = 1
PLASMADB = None

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
    MOVE_LINEAR                 = auto()
    MOVE_ARC                    = auto()
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
    DIGITAL_IN                  = auto()
    REMOVE                      = auto()



class CodeLine:
# Class to represent a single line of gcode

    def __init__(self, line, parent = None):
        """args:
        line:  the gcode line to be parsed
        mode: the model state. i.e. what G state has been set
        """
        self._parent = parent
        self.command = ()
        self.params = {}
        self.comment = ''
        self.raw = line
        self.errors = {}
        self.type = None
        self.is_hole = False
        self.token = ''
        self.active_g_modal_groups = {}
        self.cutchart_id = None
        self.hole_builder = None


        # token mapping for line commands
        tokens = {
            'G0':(Commands.MOVE_LINEAR, self.parse_linear),
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
            'G40':(Commands.CUTTER_COMP_OFF, self.placeholder),
            'G64':(Commands.PATH_BLENDING, self.parse_passthrough),
            'M52':(Commands.ADAPTIVE_FEED, self.parse_passthrough),
            'M3':(Commands.SPINDLE_ON, self.parse_passthrough),
            'M5':(Commands.SPINDLE_OFF, self.parse_passthrough),
            'M190':(Commands.MATERIAL_CHANGE, self.parse_passthrough),
            'M66':(Commands.DIGITAL_IN, self.parse_passthrough),
            'F#':(Commands.FEEDRATE_MATERIAL, self.parse_passthrough),
            'F':(Commands.FEEDRATE_LINE, self.parse_feedrate),
            '#<holes>':(Commands.HOLE_MODE, self.placeholder),
            '#<h_diameter>':(Commands.HOLE_DIAM, self.placeholder),
            '#<h_velocity>':(Commands.HOLE_VEL, self.placeholder),
            '#<oclength>':(Commands.HOLE_OVERCUT, self.placeholder),
            '#<pierce-only>':(Commands.PIERCE_MODE, self.placeholder),
            #'#<keep-z-motion>':Commands.KEEP_Z,
            ';':(Commands.COMMENT, self.parse_comment),
            '(':(Commands.COMMENT, self.parse_comment),
            'T':(Commands.TOOLCHANGE, self.parse_toolchange)
            #'(o=':Commands.MAGIC_MATERIAL
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
            # we have multiple codes on the line
            self.type = Commands.PASSTHROUGH
            # scan for possible 'bad' codes
            for code in multi_codes:
                if code in ('G41','G42','G41.1','G42.1'):
                    # we have an error state
                    self.cutter_comp_error()
            # look for Tx M6 combo
            f = re.findall("T\s*\d+|M6", line.upper().strip())
            if len(f) == 2:
                # we have a tool change combo. Assume in form Tx M6
                self.parse_toolchange(combo=True)
        else:
            # not a multi code on single line situation so process line
            # to set line type
            for k in tokens:
                # do regex searches to find exact matches of the token patterns
                pattern = r"^"+k + r"{1}"
                if k == '(':
                    # deal with escaping the '(' which is special char in regex
                    pattern = r"^\({1}"
                r = re.search(pattern, line.upper())
                if r != None:
                    # since r is NOT None we must have found something
                    self.type = tokens[k][0]
                    self.token = k
                    # call the parser method bound to this key
                    tokens[k][1]()
                    # check for an inline comment if the entire line is not a comment
                    if self.type is not Commands.COMMENT:
                        self.parse_inline_comment()
                    # break out of the loop, we found a match
                    break
                else:
                    # nothing of interest just mark the line for pass through processing
                    self.type = Commands.PASSTHROUGH
            if self.type is Commands.PASSTHROUGH:
                # If the result was seen as 'OTHER' do some further checks
                # As soon as we shift off being type OTHER, exit the method
                # 1. is it an XY line
                self.parse_XY_line()
                #if self.type is not Commands.OTHER: return


    def strip_inline_comment(self, line):
        s = re.split(";|\(", line, 1)
        try:
            return s[0].strip()
        except:
            return line

    def save_g_modal_group(self, grp):
        self.active_g_modal_groups = grp.copy()


    def parse_comment(self):
        self.comment = self.raw
        self.command = (';', None)
        self.params = {}


    def parse_inline_comment(self):
        # look for possible inline comment
        s = re.split(";|\(",self.raw[1:],1)
        robj = re.search(";|\(",self.raw[1:])
        if robj != None:
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
        pass

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
        line = self.raw.upper().strip()
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
        # split the raw line at the token and then look for X/Y/I/J/P existence
        line = self.strip_inline_comment(self.raw).upper().split(self.token,1)[1].strip()
        tokens = re.finditer(r"X[\d\+\.-]*|Y[\d\+\.-]*|I[\d\+\.-]*|J[\d\+\.-]*|P[\d\+\.-]*", line)
        for token in tokens:
            params = re.findall(r"X|Y|I|J|P|[\d\+\.-]+", token.group())
            # this is now a list which can be added to the params dictionary
            if len(params) == 2:
                self.params[params[0]] = float(params[1])

    def parse_toolchange(self, combo=False):
        # A tool change is deemed a process change.
        # The Tool Number is to be the unique ID of a Process combination from
        # the CustChart table. This will need to be supported by the
        # CAM having a loading of tools where the tool #  is the ID from this table
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
        cut_process = PLASMADB.cut_by_id(tool)
        if len(cut_process) == 0:
            # rewrite the raw line as an error comment
            self.raw = f"; ERROR: Invalid Cutchart ID. Check CAM Tools: {self.raw}"
            LOG.warn(f'Tool {tool} not a valid cut process in DB')
        else:
            self.cutchart_id = tool
            self._parent.active_cutchart = tool
            self._parent.active_feedrate = cut_process[0].cut_speed


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
        print(f'ERROR:CUTTER_COMP:INVALID GCODE FOUND',file=sys.stderr)
        sys.stderr.flush()
        self.type = Commands.REMOVE


    def placeholder(self):
        LOG.debug(f'Type PLACEHOLDER -- {self.token} -- found - this code is not handled or considered')
        pass


class HoleBuilder:
    def __init__(self):
        self.elements = []

    def degrees(self, rad):
        #convert radians to degrees to help decipher the angles
        return(rad *(180/math.pi))

    def line_length(self, x1, y1, x2, y2):
        a = (x2 - x1)**2
        b = (y2 - y1)**2
        s = a + b
        rtn = math.sqrt(s)
        return rtn

    def create_ccw_arc_gcode(self, x, y, rx, ry):
        return {
            "code": "g03",
            "x": x,
            "y": y,
            "i": rx,
            "j": ry
        }

    def create_cw_arc_gcode(self, x, y, rx, ry):
        return {
            "code": "g02",
            "x": x,
            "y": y,
            "i": rx,
            "j": ry
        }

    def create_line_gcode(self, x, y, rapid):
        return {
            "code": "g00" if rapid else "g01",
            "x": x,
            "y": y
        }

    def create_cut_on_off_gcode(self, cut_on):
        return {
            "code": "m03" if cut_on else "m05"
        }

    def create_kerf_off_gcode(self):
        return {
            "code": "g40"
        }

    def create_comment(self, txt):
        return {
            "code": f"({txt})"
        }

    def create_dwell(self, t):
        # add a G4 Pn dwell between segments
        return {
             "code": f"g4 P{t}"
        }
    
    def create_absolute_arc(self):
        return {
            "code": "g90.1"
        }

    def create_relative_arc(self):
        return {
            "code": "g91.1"
        }


    def element_to_gcode_line(self, e):
        if 'i' in e:
            line = '{} x{:.2f} y{:.2f} i{:.2f} j{:.2f}'.format(e['code'], e['x'], e['y'], e['i'], e['j'])
        elif 'x' in e:
            line = '{} x{:.2f} y{:.2f}'.format(e['code'], e['x'], e['y'])
        else:
            line = e['code']
        return line


    def plasma_hole(self, x, y, d, kerf, leadin_radius, splits=[]):
        # Params:
        # x:              Hole Centre X position
        # y:              Hole Centre y position
        # d:              Hole diameter
        # kerf:           Kerf width for cut
        # leadin_radius:  Radius for the lead in arc
        # splits[]:       List of length segments. Segments will support different speeds
        #                 and starting positions of the circle. Including overburn
        LOG.debug('Build smart hole')
        #kerf compensation
        # often code is already compensated. We need to be able to tell the script if it is
        #changed the radius parameter to be ad diameter which is more in keeping with the hole data methodology

        r = float(d)/2.00
        kc = float(kerf) / 2
        # kerf larger than hole -> hole disappears
        if kc > r:
            self.elements = []
            return
        # convert split distances to angles (in radians)
        split_angles = []
        full_circle = math.pi * 2  # 360 degrees. We need to use this for a segment moving to 12 O'clock
        crossed_origin = False
        for spt in splits:
            # using the relationship of arc_length/circumfrance = angle/360 if you work the algebra you find:
            # angle = arc_length/radius (in radians)
            tmp_ang = float(spt) / float(r)     # need to typecast to prevent Python from truncating to whole values, maybe should be double?
            this_ang = full_circle + tmp_ang    # Accoding to Juha, all angles are from 0 degrees, -ve angles to the right, +ve angles to the left
            if (this_ang > full_circle) and (crossed_origin == False):
                # Has this split got to the 0deg/360 deg  origin?
                # when we cross the origin, add a 360 degree keep it in the correct order
                split_angles.append(full_circle)
                this_ang = tmp_ang
                crossed_origin = True
            split_angles.append(this_ang)
        #Sorting is not helpful with splits becasue the smaller values come befor ethe first segment.
        #We need to keep ssegments in order
        #sort angles, smallest first

        # compensate hole radius and leadin radius if not already compensated code
        # TODO: allow for uncompensated code
        r = r - kc
        leadin_radius = leadin_radius -kc

        # the first real point of the hole (after leadin)
        arc_x0 = x
        arc_y0 = y + r

        self.elements = []

        self.elements.append(self.create_absolute_arc())
        self.elements.append(self.create_comment('Leadin...'))
        # done nothing here

        # leadin radius too small or greater (or equal) than r.
        # --> use straight leadin from the hole center.
        if leadin_radius < 0 or leadin_radius >= r:
            self.elements.append(self.create_comment('too small'))
            self.elements.append(self.create_line_gcode(x, y, True))
            self.elements.append(self.create_kerf_off_gcode())
            self.elements.append(self.create_cut_on_off_gcode(True))
            self.elements.append(self.create_line_gcode(arc_x0, arc_y0, False))

        # leadin radius <= r / 2.
        # --> use half circle leadin
        # done nothing here
        elif leadin_radius <= (r / 2):
            self.elements.append(self.create_comment('half circle radius'))
            self.elements.append(self.create_line_gcode(x, arc_y0 - 2 * leadin_radius, True))
            self.elements.append(self.create_kerf_off_gcode())
            self.elements.append(self.create_cut_on_off_gcode(True))
            self.elements.append(self.create_ccw_arc_gcode(x + leadin_radius, arc_y0 - leadin_radius, x, arc_y0 - leadin_radius))
            self.elements.append(self.create_ccw_arc_gcode(arc_x0, arc_y0, x, arc_y0 - leadin_radius))

        # r/2 < leadin radius < r.
        # --> use combination of leadin arc and a smaller arc from the hole center
        else:
            # TODO:
            self.elements.append(self.create_comment('use combination of leadin arc and a smaller arc from the hole center'))
            leadin_diameter =  (leadin_radius + kc) * 2
            from_centre = leadin_diameter - (r + kc)  # distance from centre
            start1_x = x
            start1_y = r + from_centre  + kc # Y coordinate of start position
            self.elements.append(self.create_line_gcode(x, y-d/2 , True))
            if abs(from_centre) < (kerf * 2):
                 # no room for arc, use straight segment from hole centre
                self.elements.append(self.create_comment('no room for arc, use straight segment from hole centre...'))
                self.elements.append(self.create_line_gcode(start1_x, start1_y, False))
            elif start1_y < r:
                # leadin diameter is shorter than hole radius, Use G2 for first arc
                self.elements.append(self.create_comment('leadin diameter is shorter than hole radius, Use G2 for first arc...'))
                self.elements.append(self.create_cw_arc_gcode(start1_x , start1_y, x, start1_y - from_centre))
            else:
                #leadin diameter is longer than hole radius, Use G3 for first arc
                self.elements.append(self.create_comment('leadin diameter is longer than hole radius, Use G3 for first arc...'))
                self.elements.append(self.create_ccw_arc_gcode(x , -(leadin_diameter) , x, -(start1_y - from_centre/2)))
            self.elements.append(self.create_ccw_arc_gcode(x , y - kc, x, -(leadin_diameter-(leadin_diameter - kc)/2)))

        self.elements.append(self.create_comment('Hole...'))
        #this has been reworked quite a bit. The original code was referring to the cursor X & Y positions and they needed to be the hole centre
        # TODO: not happy with this as it only works where x = 0 I think. Nees to be more robust
        cx = x
        cy =  y

        if len(split_angles) > 0:
            for sang in split_angles:
                end_angle = sang
                end_x = ( cx+ r * math.cos(end_angle))
                end_y = ( cy +r * math.sin(end_angle))
                if sang == full_circle:
                    #reset coordinates to 0,0 if angle = 360 degrees. We want the next segments to refer to 0 degrees
                    end_x = x
                    end_y = y + r
                if sang < split_angles[0] and sang > 0.00:
                    #conditional to coordinate positive angles
                    end_x = (cx - r * math.cos(end_angle))
                    end_y = (cy - r * math.sin(end_angle))
                #comment the code
                ourcomment = 'Settings: angle = ' + str(sang) + ' end_angle ' + str(end_angle) +' radians ' + str(self.degrees(end_angle)) + ' degrees'
                self.elements.append(self.create_comment(ourcomment))
                self.elements.append(self.create_ccw_arc_gcode(end_x, end_y, cx, cy))
                if (end_x == 0.00 and end_y == 0.00) == False:
                    #if not 12 O'clock, dwell for 0.5 sec so we have a visual indicator of each segment
                    # we need to insert a call to a procedure that creates the required gcode actions at the end of each segment
                    self.elements.append(self.create_dwell('0.5'))

        else:
            # create hole as four arcs. no overburn or anything special.
            self.elements.append(self.create_ccw_arc_gcode(x-r, y, x, y))
            self.elements.append(self.create_ccw_arc_gcode(x, y-r, x, y))
            self.elements.append(self.create_ccw_arc_gcode(x+r, y, x, y))
            self.elements.append(self.create_ccw_arc_gcode(x, y+r, x, y))

        self.elements.append(self.create_relative_arc())
        # cut off
        self.elements.append(self.create_cut_on_off_gcode(False))

    def generate_hole_gcode(self):
        for e in self.elements:
            print(self.element_to_gcode_line(e), file=sys.stdout)
            sys.stdout.flush()

class PreProcessor:
    def __init__(self, inCode):
        self._new_gcode = []
        self._parsed = []
        self._line = ''
        self._line_num = 0
        self._line_type = 0
        self._orig_gcode = None
        self.active_g_modal_grps = {}
        self.active_m_modal_grps = {}
        self.active_cutchart = None
        self.active_feedrate = None

        openfile= open(inCode, 'r')
        self._orig_gcode = openfile.readlines()
        openfile.close()

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
        except:
            return None


    def flag_holes(self):
        # old school loop so we can easily peek forward or back of the current
        # record being processed.
        i = 0
        while i < len(self._parsed):
            line = self._parsed[i]
            if len(line.command) == 2:
                if line.command[0] == 'G' and line.command[1] in (2,3):
                    # this could be a hole, test for it
                    #[1] find the last X and Y position while grp 1 was either G0 or G1
                    j = i-1
                    for j in range(j, -1, -1):
                        prev = self._parsed[j]
                        # is there an X or Y in the line
                        if 'X' in prev.params.keys() and prev.active_g_modal_groups[1] in ('G0','G1'):
                            lastx = prev.params['X']
                            break
                    j = i-1
                    for j in range(j, -1, -1):
                        prev = self._parsed[j]
                        # is there an X or Y in the line
                        if 'Y' in prev.params.keys() and prev.active_g_modal_groups[1] in ('G0','G1'):
                            lasty = prev.params['Y']
                            break
                    endx = line.params['X'] if 'X' in line.params.keys() else lastx
                    endy = line.params['Y'] if 'Y' in line.params.keys() else lasty
                    if endx == lastx and endy == lasty:
                        line.is_hole = True
                    else:
                        line.is_hole = False

                    # if line is a hole then prepare to replace with "smart" holes
                    if line.is_hole:
                        line.hole_builder = HoleBuilder()
                        arc_i = line.params['I']
                        arc_j = line.params['J']
                        centre_x = endx + arc_i
                        centre_y = endy + arc_j
                        radius = line.hole_builder.line_length(centre_x, endx, centre_y, endy)
                        diameter = 2 * math.fabs(radius)
                        # Params:
                        # x:              Hole Centre X position
                        # y:              Hole Centre y position
                        # d:              Hole diameter
                        # kerf:           Kerf width for cut
                        # leadin_radius:  Radius for the lead in arc
                        # splits[]:       List of length segments. Segments will support different speeds. +ve is left of 12 o'clock
                        #                 -ve is right of 12 o'clock
                        #                 and starting positions of the circle. Including overburn
                        line.hole_builder.plasma_hole(centre_x, centre_y, diameter, 1.5, 4.0, [-3,3])
                        
                        # scan forward and back to mark the M3 and M5 as Coammands.REMOVE
                        j = i-1
                        for j in range(j, -1, -1):
                            prev = self._parsed[j]
                            # find and mark for removal the first M3
                            if prev.token.startswith('M3'):
                                prev.type = Commands.REMOVE
                                break
            i += 1

    def parse(self):
        for line in self._orig_gcode:
            self._line_num += 1
            self._line = line.strip()
            l = CodeLine(self._line, parent=self)
            try:
                gcode = f'{l.command[0]}{l.command[1]}'
            except:
                gcode = ''
            self.set_active_g_modal(gcode)
            l.save_g_modal_group(self.active_g_modal_grps)
            self._parsed.append(l)



    def dump_parsed(self):
        LOG.debug('Dum parsed gcode to stdio')
        for l in self._parsed:
            #print(f'{l.type}\t\t -- {l.command} \
            #    {l.params} {l.comment}')
            # build up line to go to stdout
            if l.is_hole:
                print('(---- Smart Hole Start ----)')
                l.hole_builder.generate_hole_gcode()
                print('(---- Smart Hole End ----)')
                continue
            if l.type is Commands.COMMENT:
                out = l.comment
            elif l.type is Commands.OTHER:
                # Other at the moment means not recognised
                out = "; >>  "+l.raw
            elif l.type is Commands.PASSTHROUGH:
                out = l.raw
            elif l.type is Commands.REMOVE:
                # skip line as not to be used
                out = ''
                continue
            else:
                try:
                    out = f"{l.command[0]}{l.command[1]}"
                except:
                    out = ''
                try:
                    for p in l.params:
                        out += f' {p}{l.params[p]}'
                    out += f' {l.comment}'
                    out = out.strip()
                except:
                    out = ''
            print(out, file=sys.stdout)
            sys.stdout.flush()

    def set_ui_hal_cutchart_pin(self):
        if self.active_cutchart is not None:
            rtn = hal.set_p("qtpyvcp.cutchart-id", f"{self.active_cutchart}")
            LOG.debug('Set hal cutchart-id pin')
        else:
            LOG.debug('No active cutchart')


def main():
    global PLASMADB

    try:
        inCode = sys.argv[1]
    except:
        # no arg found, probably being run from command line and someone forgot a file
        print(__doc__)
        return

    if len(inCode) == 0 or '-h' == inCode:
        print(__doc__)
        return

    PLASMADB = PlasmaProcesses(db_type='sqlite')

    # Start cycling through each line of the file and processing it
    p = PreProcessor(inCode)
    p.parse()
    # Holes processing
    p.flag_holes()
    # pass file to stdio and set any hal pins
    p.dump_parsed()
    # Set hal pin on UI for cutchart.id
    p.set_ui_hal_cutchart_pin()
    # Close out DB
    PLASMADB.terminate()


if __name__ == '__main__':
    main()
