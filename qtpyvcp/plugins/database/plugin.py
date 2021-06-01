import os
from pprint import pprint

from qtpyvcp.plugins.database.base import Session, Base, engine
from qtpyvcp.plugins.database.tool_table import ToolTable, Tool
from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import Plugin, getPlugin

LOG = getLogger(__name__)


class DataBaseManager(Plugin):
    def __init__(self):
        super(DataBaseManager, self).__init__()
        self.session = None

        self.tool_table = getPlugin("tooltable")

        Base.metadata.create_all(engine)

    def getData(self, name, default=None):
        tool_tables = self.session.query(ToolTable).all()

        for tool_table in tool_tables:
            for tools in tool_table.tools:
                print(tools.id, tools.remark, tools.x_offset, tools.y_offset)

        return tool_tables

    def setData(self):

        tooltable = self.tool_table.getToolTable()
        pprint(tooltable)

        tools = list()

        for k, tool in tooltable.items():

            tools.append(Tool(
                remark=tool.get("R"),
                tool_no=k,
                pocket=tool.get("P"),
                x_offset=tool.get("X"),
                y_offset=tool.get("Y"),
                z_offset=tool.get("Z"),
                a_offset=tool.get("A"),
                b_offset=tool.get("B"),
                c_offset=tool.get("C"),
                u_offset=tool.get("U"),
                v_offset=tool.get("V"),
                w_offset=tool.get("W"),
                diameter=tool.get("D")
            ))

        tool_table = ToolTable(name="Test Tool Table")

        tool_table.tools = tools

        # 9 - persists data
        self.session.add(tool_table)
        for tool in tools:
            self.session.add(tool)

        # 10 - commit and close session
        self.session.commit()

    def initialise(self):
        self.session = Session()

    def terminate(self):
        self.session.close()


class PlasmaDataBaseManager(Plugin):
    def __init__(self):
        super(PlasmaDataBaseManager, self).__init__()
        self.session = None

        self.plasma_table = None

        Base.metadata.create_all(engine)

    def getData(self, name, default=None):
        tool_tables = self.session.query(ToolTable).all()

        for tool_table in tool_tables:
            for tools in tool_table.tools:
                print(tools.id, tools.remark, tools.x_offset, tools.y_offset)

        return tool_tables

    def setData(self):

        tooltable = self.tool_table.getToolTable()
        pprint(tooltable)

        tools = list()

        for k, tool in tooltable.items():

            tools.append(Tool(
                remark=tool.get("R"),
                tool_no=k,
                pocket=tool.get("P"),
                x_offset=tool.get("X"),
                y_offset=tool.get("Y"),
                z_offset=tool.get("Z"),
                a_offset=tool.get("A"),
                b_offset=tool.get("B"),
                c_offset=tool.get("C"),
                u_offset=tool.get("U"),
                v_offset=tool.get("V"),
                w_offset=tool.get("W"),
                diameter=tool.get("D")
            ))

        tool_table = ToolTable(name="Test Tool Table")

        tool_table.tools = tools

        # 9 - persists data
        self.session.add(tool_table)
        for tool in tools:
            self.session.add(tool)

        # 10 - commit and close session
        self.session.commit()

    def initialise(self):
        self.session = Session()

    def terminate(self):
        self.session.close()
