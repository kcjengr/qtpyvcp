#!/usr/bin/env python3

import os
import sys

from tooldb import tooldb_callbacks # functions (g,p,l,u)
from tooldb import tooldb_tools     # list of tool numbers
from tooldb import tooldb_loop      # main loop

from qtpyvcp.lib.db_tool.base import Session, Base, engine
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool

# Catch unhandled exceptions
def excepthook(exc_type, exc_msg, exc_tb):
    print(exc_type, file=sys.stderr)
    print(exc_msg, file=sys.stderr)
    print(exc_tb, file=sys.stderr)


sys.excepthook = excepthook


class DataBaseManager():
    def __init__(self):
        super(DataBaseManager, self).__init__()
        self.session = None
        
        Base.metadata.create_all(engine)
        
        self.session = Session()
        
        tools = self.session.query(Tool).all()
        tool_list = list()

        for tool in tools:
            tool_list.append(tool.tool_no)
    
        tooldb_tools(tool_list)
        tooldb_callbacks(self.user_get_tool,
                         self.user_put_tool,
                         self.user_load_spindle,
                         self.user_unload_spindle)
            
        
        self.tool_list = tool_list
        
        self.tools = dict()

  
    def close(self):
        self.session.close()
    
    def apply_db_rules(self):
        # Apply database rules (typically when a tooldata reload requested)
        # Rule: For tools having identical diameter (within diameter_epsilon),
        #       lowest tool number is assigned to the pocket/parameters for
        #       the tool with the lowest operating time (in minutes).
        #
        #       So if t10diameter==t11diameter==t12diameter,
        #       t10 will select tool with lowest operating minutes
        #       ...
        #       t12 will select tool with most   operating minutes
        #
        # NOTE: Tooldata must be reloaded for computed updates.
        #       Use gui reload buttons or G10L0 in mdi or gcode programs
    
        #ewrite("APPLY_DB_RULES================================\n")
        diameter_epsilon = 0.001
        for tno in range(0, 12):
            CUR   = self.toolline_to_dict(self.tools[tno],all_letters)
            diam  = float(CUR["D"])
            if not 'M' in CUR: CUR['M'] = "0"
    
            for tryno in range(tno+1,  12):
                TRY = self.toolline_to_dict(tools[tryno],self.all_letters)
                if abs(diam - float(TRY["D"])) > diameter_epsilon: continue
                # found equal diameters
                #ewrite("MATCH: tno=%d tryno=%d diam=%s\n"%(tno,tryno,CUR["D"]))
                if not 'M' in TRY: TRY['M'] = "0.0"
                if float(TRY['M']) < float(CUR['M']):
                    CUR['T'] = str(tryno)
                    TRY['T'] = str(tno)
                    tools[tno]   = self.dict_to_toolline(TRY,self.all_letters)
                    tools[tryno] = self.dict_to_toolline(CUR,self.all_letters)
                    CUR = self.toolline_to_dict(self.tools[tno],self.all_letters)
                    # save_tools_to_file(db_savefile)
    
    def user_get_tool(self, tool_no):
        print(f"GET tool {tool_no}", file = sys.stderr)

        tool = self.session.query(Tool).filter(Tool.tool_no == tool_no).one()
        
        data = [f"T{tool.tool_no}",
                f"P{tool.pocket}",
                f"D{tool.diameter}",
                f"X{tool.x_offset}",
                f"Y{tool.y_offset}",
                f"Z{tool.z_offset}",
                f"A{tool.a_offset}",
                f"B{tool.b_offset}",
                f"C{tool.c_offset}",
                f"U{tool.u_offset}",
                f"V{tool.v_offset}",
                f"W{tool.w_offset}"]

        return " ".join(data)


    def user_put_tool(self, toolno, params):
        print(f"PUT tool {toolno} {params}", file = sys.stderr)
        # tno = int(toolno)
        # update_tool(tno,params.upper() )
        # save_tools_to_file(db_savefile)
        # tooltable = self.tool_table.getToolTable()
        # pprint(tooltable)
        #
        # tools = list()
        #
        # for k, tool in tooltable.items():
        #
        #     tools.append(Tool(
        #         remark=tool.get("R"),
        #         tool_no=k,
        #         pocket=tool.get("P"),
        #         x_offset=tool.get("X"),
        #         y_offset=tool.get("Y"),
        #         z_offset=tool.get("Z"),
        #         a_offset=tool.get("A"),
        #         b_offset=tool.get("B"),
        #         c_offset=tool.get("C"),
        #         u_offset=tool.get("U"),
        #         v_offset=tool.get("V"),
        #         w_offset=tool.get("W"),
        #         diameter=tool.get("D"),
        #         model_stl=tool.get("tool_holder")
        #     ))
        #
        # tool_table = ToolTable(name="Test Tool Table")
        #
        # tool_table.tools = tools
        #
        # # 9 - persists data
        # self.session.add(tool_table)
        # for tool in tools:
        #     self.session.add(tool)
        #
        # # 10 - commit and close session
        # self.session.commit()

    # examples cmds received for load_spindle and unload_spindle
    # NONRAN example:
    # t15m6 l T15  P0
    # t0 m6 u T0   P0
    #
    # t15m6 l T15  P0
    # t16m6 l T16  P0
    # t0 m6 u T0   P0
    
    # RAN example (two commands each step):
    # t15 m6 u T0   P16
    #        l T15  P0
    # t0  m6 u T15  P16
    #        l T0   P0
    #
    # t15 m6 u T0   P16
    #        l T15  P0
    # t16 m6 u T15  P17
    #        l T16  P0
    # t0  m6 u T16  P16
    #        l T0   P0
    
    def user_load_spindle(self, toolno, params):
        print(f"LOAD SPINDLE {toolno} {params}", file=sys.stderr)
        #
        # tno = int(toolno)
        #
        # TMP = toolline_to_dict(params,['T','P'])
        # if TMP['P'] != "0": umsg("user_load_spindle_nonran_tc P=%s\n"%TMP['P'])
        # if tno      ==  0:  umsg("user_load_spindle_nonran_tc tno=%d\n"%tno)
        #
        # # save restore_pocket as pocket may have been altered by apply_db_rules()
        # D   = toolline_to_dict(self.tools[tno],all_letters)
        # restore_pocket[tno] = D['P']
        # D['P'] = "0"
        #
        # if p0tool != -1:  # accrue time for prior tool:
        #     stop_tool_timer(p0tool)
        #     RESTORE = toolline_to_dict(self.tools[p0tool],all_letters)
        #     RESTORE['P'] = restore_pocket[p0tool]
        #     self.tools[p0tool] = dict_to_toolline(RESTORE,all_letters)
        #
        # p0tool = tno
        # D['T'] = str(tno)
        # D['P'] = "0"
        # start_tool_timer(p0tool)
        # self.tools[tno] = dict_to_toolline(D,all_letters)
        # save_tools_to_file(db_savefile)
    
    def user_unload_spindle(self, toolno, params):
        print(f"UNLOAD SPINDLE {toolno} {params}", file=sys.stderr)
        #
        # tno = int(toolno)
        #
        # if p0tool == -1: return # ignore
        # TMP = toolline_to_dict(params,['T','P'])
        # if tno       !=  0:  umsg("user_unload_spindle_nonran_tc tno=%d\n"%tno)
        # if TMP['P']  != "0": umsg("user_unload_spindle_nonran_tc P=%s\n"%TMP['P'])
        #
        # stop_tool_timer(p0tool)
        # D = toolline_to_dict(self.tools[p0tool],all_letters)
        # D['T'] = str(p0tool)
        # D['P'] = restore_pocket[p0tool]
        # self.tools[p0tool] = dict_to_toolline(D,all_letters)
        #
        # p0tool = -1
        # save_tools_to_file(db_savefile)


def main():
    
    tool_db_man = DataBaseManager()
    
    try:
        tooldb_loop()  # loop forever, use callbacks
    except Exception as e:
        print(f"Exception = {e}", file=sys.stderr)
    
    tool_db_man.close()

if __name__ == "__main__":
    main()
