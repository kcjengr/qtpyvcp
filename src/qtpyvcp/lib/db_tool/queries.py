# coding=utf-8
"""Example: list every tool in the database (schema v1)."""

from .tool_table import Tool
from .base import Session

session = Session()

for tool in session.query(Tool).order_by(Tool.tool_no).all():
    print(tool.tool_no, tool.remark, tool.x_offset, tool.y_offset)

session.close()
