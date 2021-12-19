#!/usr/bin/env python3
"""Tooltable Database interface

This tool supports the linuxcnc tool database interface standard to the
plasma_processes plug.

The intention is for the tool table for a particular table to be
dynamically supplied from the cut database managed by the plasma_processes
plug.

Each tool ID equates to a cutchart entry appropriate for the table based on
the plasma power source, unit of measure, material thickiness, process, gas,
material type etc.

Using this approach means a text update of the on disk tool table is not
required and better supports the central management of cut charts and loading
of correct details into the UI.
"""

import os
import sys

import linuxcnc
from tooldb import tooldb_callbacks # functions
from tooldb import tooldb_tools     # list of tool numbers
from tooldb import tooldb_loop      # main loop

from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.plugins.plasma_processes import PlasmaProcesses
from qtpyvcp.utilities.config_loader import load_config_files

#import pydevd;pydevd.settrace()


base_ini_file = os.environ['INI_FILE_NAME']
ini_file_name = normalizePath(path=base_ini_file, base=os.getenv('CONFIG_DIR', '~/'))
# ini_file_name = normalizePath(path='xyz.ini', base=os.getenv('CONFIG_DIR', '~/'))
INI_FILE = linuxcnc.ini(ini_file_name)
UNITS = INI_FILE.find('TRAJ', 'LINEAR_UNITS')
MACHINE = INI_FILE.find('PLASMAC', 'MACHINE')
PRESSURE = INI_FILE.find('PLASMAC', 'PRESSURE')

custom_config_yaml_file_name = normalizePath(path='custom_config.yml', base=os.getenv('CONFIG_DIR', '~/'))
cfg_dic = load_config_files(custom_config_yaml_file_name)

# we assume that things are sqlit unless we find custom_config.yml
# pointing to different type of DB
try:
    db_connect_str = cfg_dic['data_plugins']['plasmaprocesses']['kwargs']['connect_string']
    # if no error then we found a db connection string. Use it.
    PLASMADB = PlasmaProcesses(connect_string=db_connect_str)
except:
    # no connect string found OR can't connect so assume sqlite on local machine
    PLASMADB = PlasmaProcesses(db_type='sqlite')

TOOLS = {}
 
def build_tool_list():
    global TOOLS
    TOOLS = {}
    pocket = 1
    for t in PLASMADB.tool_list_for_lcnc( MACHINE, PRESSURE, UNITS):
        TOOLS[t.id] = [pocket, t.kerf_width, t.name]
        pocket += 1

def get_tool(toolno):
    return f'T{toolno} P{TOOLS[toolno][0]} D{TOOLS[toolno][1]} ;{TOOLS[toolno][2]}'

def put_tool(toolno, pocketno, **kwargs):
    pass


build_tool_list()
tooldb_tools(TOOLS.keys())
tooldb_callbacks(get_tool, put_tool)

try:
    tooldb_loop()  # loop forever, use callbacks
except Exception as e:
    PLASMADB.terminate()
    if sys.stdin.isatty():
        print(("exception=",e))
    else:
        pass # avoid messages at termination

PLASMADB.terminate()
