# coding=utf-8
"""Example: seed a couple of tools directly via the ORM (schema v1).

Run `run_migrations(get_engine())` first (or via the plugin/backend) so the
tables exist before this script inserts into them.
"""

from qtpyvcp.lib.db_tool.tool_table import Tool
from qtpyvcp.lib.db_tool.base import Session, get_engine, configure_database
from qtpyvcp.lib.db_tool.migrate import run_migrations

configure_database('db.sqlite')
run_migrations(get_engine())

session = Session()

tool_1 = Tool(
    tool_no=1,
    remark="Example Tool",
    pocket=0,
    diameter=2.0,
)

session.add(tool_1)
session.commit()
session.close()
