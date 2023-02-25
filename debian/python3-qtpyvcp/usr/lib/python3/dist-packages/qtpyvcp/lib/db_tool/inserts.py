# coding=utf-8

from datetime import date

from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool
from qtpyvcp.lib.db_tool.base import Session, engine, Base

from qtpyvcp.plugins import getPlugin
#
# tooltable_plugin = getPlugin('tooltable')
#
# print(tooltable_plugin.getToolTable())


Base.metadata.create_all(engine)

session = Session()




tool_1 = Tool(
    id = 0,
    remark = "no tool",
    tool_no = 0,
    pocket = 0,
    x_offset = 0.0,
    y_offset = 0.0,
    z_offset = 0.0,
    a_offset = 0.0,
    b_offset = 0.0,
    c_offset = 0.0,
    i_offset = 0.0,
    j_offset = 0.0,
    q_offset = 0.0,
    u_offset = 0.0,
    v_offset = 0.0,
    w_offset = 0.0,
    diameter = 0.0
)


tool_2 = Tool(
    id = 1,
    remark = "Example Tool",
    tool_no = 1,
    pocket = 0,
    x_offset = 0.0,
    y_offset = 0.0,
    z_offset = 0.0,
    a_offset = 0.0,
    b_offset = 0.0,
    c_offset = 0.0,
    i_offset = 0.0,
    j_offset = 0.0,
    q_offset = 0.0,
    u_offset = 0.0,
    v_offset = 0.0,
    w_offset = 0.0,
    diameter = 2.0
)


tool_table = ToolTable(name="Test Tool Table")

tool_table.tools = [tool_1, tool_2]

# 9 - persists data
session.add(tool_table)

session.add(tool_1)
session.add(tool_2)

# 10 - commit and close session
session.commit()
session.close()
