# coding=utf-8

import os
import sys

import re

from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool, ToolProperties
from qtpyvcp.lib.db_tool.base import Session, engine, Base
from qtpyvcp.utilities.logger import getLogger


LOG = getLogger(__name__)

LOADING_CHARS = ['-', '\\', '|', '/', '-', '\\', '|', '/']

def main():
    
    argv = sys.argv
    
    if len(argv) > 1:
        filename = argv[1]
    else:
        filename = "tool.tbl"
    
    if not os.path.isfile(filename):
        
        print(f"file {filename} not found!")
        exit(1)
    
    print("Importing tool data to db.sqlite")

    with open(filename, 'r') as tt_file:
        tt_tools = [line.strip() for line in tt_file.readlines()]

    
    loading_step = 0
    
    tools_data = list()
    tools_properties_data = list()
    for index, tt_tool in enumerate(tt_tools):
        data, sep, comment = tt_tool.partition(';')
        items = re.findall(r"([A-Z]+[0-9.+-]+)", data.replace(' ', ''))

        tool_data = dict()

        tool_data['T'] = 0
        tool_data['P'] = 0
        tool_data['X'] = 0.0
        tool_data['Y'] = 0.0
        tool_data['Z'] = 0.0
        tool_data['A'] = 0.0
        tool_data['B'] = 0.0
        tool_data['C'] = 0.0
        tool_data['U'] = 0.0
        tool_data['J'] = 0.0
        tool_data['Q'] = 0
        tool_data['U'] = 0.0
        tool_data['V'] = 0.0
        tool_data['W'] = 0.0
        tool_data['D'] = 0.0

        if len(items):
            for item in items:
                descriptor = item[0]
                if descriptor in 'TPXYZABCUVWDIJQR':
                    value = item[1:]
                    if descriptor in ('T', 'P', 'Q'):
                        try:
                            tool_data[descriptor] = int(value)
                        except:
                            LOG.error('Error converting value to int: {}'.format(value))
                            break
                    else:
                        try:
                            tool_data[descriptor] = float(value)
                        except:
                            LOG.error('Error converting value to float: {}'.format(value))
                            break

            tool = Tool(id=index,
                        remark=comment.strip(),
                        tool_no=tool_data['T'],
                        pocket=tool_data['P'],
                        x_offset=tool_data['X'],
                        y_offset=tool_data['Y'],
                        z_offset=tool_data['Z'],
                        a_offset=tool_data['A'],
                        b_offset=tool_data['B'],
                        c_offset=tool_data['C'],
                        i_offset=tool_data['U'],
                        j_offset=tool_data['J'],
                        q_offset=tool_data['Q'],
                        u_offset=tool_data['U'],
                        v_offset=tool_data['V'],
                        w_offset=tool_data['W'],
                        diameter=tool_data['D'],
            )
            
            tool_properties = ToolProperties(id=index,
                        tool_no=tool_data['T']
            )
            
            tools_data.append(tool)
            
            tools_properties_data.append(tool_properties)
            

    tool_table = ToolTable(name="Tool Table")

    tool_table.tools = tools_data
    tool_table.tool_properties = tools_properties_data

    Base.metadata.create_all(engine)

    session = Session()
    session.add(tool_table)

    session.commit()
    session.close()
    
    print("Done.")

if "__main__" == __name__:
    main()