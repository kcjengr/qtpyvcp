import threading

from flask import Flask, request
from flask_restful import Resource, Api

from qtpyvcp import WINDOWS
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin


# Helper function

def getWidget(name):
    """Searches for a widget by name in the application windows.

    Args:
        name (str) : ObjectName of the widget.

    Returns: QWidget
    """
    for win_name, obj in list(WINDOWS.items()):
        if hasattr(obj, name):
            return getattr(obj, name)

    raise AttributeError("Could not find widget with name: %s" % name)


# Threading

class ApiServer(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        app = Flask(__name__)

        api = Api(app)
        api.add_resource(Tools, '/tool_table')
        api.add_resource(Tool, '/tool/<tool_no>')
        api.add_resource(ToolData, '/tool_data/<tool_no>/<element>')
        api.add_resource(AtcRotate, '/atc/rotate/<steps>/<direction>')
        api.add_resource(AtcMessage, '/atc/msg/<msg>')
        api.add_resource(AtcStore, '/atc/store/<pocket>/<tool>')

        app.run(host="127.0.0.1", port=5002, debug=False, use_reloader=False)


# Server

class RestApi(DataPlugin):
    """GCodeProperties Plugin"""

    def __init__(self):
        super(RestApi, self).__init__()

        self.api = ApiServer()
        self.api.daemon = True
        self.api.start()


########################################################################################################################
#
#  ATC
#
########################################################################################################################

class AtcRotate(Resource):

    def get(self, steps, direction):
        atc_widget = getWidget("dynatc")
        atc_widget.rotate(steps, direction)
        return 200


class AtcMessage(Resource):

    def get(self, msg):
        atc_widget = getWidget("dynatc")
        atc_widget.atc_message(msg)
        return 200


class AtcStore(Resource):

    def get(self, pocket, tool):
        atc_widget = getWidget("dynatc")
        atc_widget.store_tool(int(pocket), int(tool))
        return 200


########################################################################################################################
#
#  Tools
#
########################################################################################################################

class Tools(Resource):

    def get(self):
        tooltable_plugin = getPlugin('tooltable')
        tool_table = tooltable_plugin.getToolTable()
        return tool_table


class Tool(Resource):

    def get(self, tool_no):
        tooltable_plugin = getPlugin('tooltable')
        tool_table = tooltable_plugin.getToolTable()

        tool = tool_table.get(int(tool_no))

        return {f"tool {tool_no}": tool}


class ToolData(Resource):

    def get(self, tool_no, element):
        tooltable_plugin = getPlugin('tooltable')
        tool_table = tooltable_plugin.getToolTable()

        tool = tool_table.get(int(tool_no))
        data = tool.get(element)

        return {f"tool {tool_no}": data}

