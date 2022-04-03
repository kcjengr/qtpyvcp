# coding=utf-8

from datetime import date

from .tool_table import ToolTable, Tool
from .base import Session, engine, Base

from qtpyvcp.plugins import getPlugin

tooltable_plugin = getPlugin('tooltable')

print(tooltable_plugin.getToolTable())


Base.metadata.create_all(engine)

session = Session()




tool_1 = Tool(
    remark = "tool 1",
    tool_no = 1,
    pocket = 1,
    x_offset = 1.0,
    y_offset = 1.0,
    z_offset = 1.0,
    a_offset = 1.0,
    b_offset = 1.0,
    c_offset = 1.0,
    u_offset = 1.0,
    v_offset = 1.0,
    w_offset = 1.0,
    diameter = 1.0
    )


tool_2 = Tool(
    remark = "tool 2",
    tool_no = 2,
    pocket = 2,
    x_offset = 1.0,
    y_offset = 1.0,
    z_offset = 1.0,
    a_offset = 1.0,
    b_offset = 1.0,
    c_offset = 1.0,
    u_offset = 1.0,
    v_offset = 1.0,
    w_offset = 1.0,
    diameter = 1.0
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
