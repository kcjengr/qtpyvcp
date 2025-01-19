# coding=utf-8

import os
import sys

import re

from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool, ToolProperties
from qtpyvcp.utilities.logger import getLogger


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from _pytest.outcomes import exit
from pprint import pprint




LOG = getLogger(__name__)

def main():
    
    argv = sys.argv
    
    if len(argv) > 2:
        filename = argv[1]
        ini_filename = argv[2]
    else:
        
        print(f"usage: tbl2sql tools.tbl config.ini")
        exit(1)

    if not os.path.isfile(filename):
        print(f"file {filename} not found!")
        exit(1)
        
    if not os.path.isfile(ini_filename):
        print(f"file {filename} not found!")
        exit(1)
        
    os.environ['INI_FILE_NAME'] = ini_filename
    
    # we need INI environment variable first from arguments
    from qtpyvcp.lib.db_tool.base import Base, Session, engine
    
    if not database_exists(engine.url):
        create_database(engine.url)
    
        
    Base.metadata.create_all(engine)
    
    session = Session()
    
    print("Importing tool data to database")

    with open(filename, 'r') as tt_file:
        tt_tools = [line.strip() for line in tt_file.readlines()]

    
    
    tools_data = list()
    tools_properties_data = list()
    
    
    
    
    for index, tt_tool in enumerate(tt_tools):

        print(index, tt_tool)
        
        if index == 0:
            print("Add tool 0 (No tool)")
            
            tool = Tool(
                remark="No tool",
                tool_no=0,
                pocket=0,
                x_offset=0.0,
                y_offset=0.0,
                z_offset=0.0,
                a_offset=0.0,
                b_offset=0.0,
                c_offset=0.0,
                i_offset=0.0,
                j_offset=0.0,
                q_offset=0,
                u_offset=0.0,
                v_offset=0.0,
                w_offset=0.0,
                diameter=0.0,
                tool_table_id=1,
            )
            
        
            tool_properties = ToolProperties(
                tool_no=0,
                max_rpm=0.0,
                wear_factor=0.0,
                bullnose_radious=0.0,
                model="NONE",
                atc=False,
                tool_table_id=1,
            )
            
            tools_data.append(tool)
            tools_properties_data.append(tool_properties)
            
        else:
            
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
    
                tool = Tool(
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
                    tool_table_id=1,
                )
                
                tool_properties = ToolProperties(
                    tool_no=tool_data['T'],
                    max_rpm=0.0,
                    wear_factor=0.0,
                    bullnose_radious=0.0,
                    model="NONE",
                    atc=False,
                    tool_table_id=1,
                )
                
                tools_data.append(tool)
                
                tools_properties_data.append(tool_properties)
                




    tool_table = ToolTable(name="Tool Table")

    tool_table.tools = tools_data
    tool_table.tool_properties = tools_properties_data

    session.add(tool_table)

    session.commit()
    session.close()
    
    print("Done.")

if "__main__" == __name__:
    main()