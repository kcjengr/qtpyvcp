import threading

from flask import Flask, request
from flask_restful import Resource, Api

from qtpyvcp import WINDOWS
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin


# Helper functions

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
        super(ApiServer, self).__init__()

    def run(self):
        app = Flask('QtPyVcpAPI')

        api = Api(app)

        # params example
        # api.add_resource(UserAPI, '/<userId>', '/<userId>/<username>', endpoint='user')

        api.add_resource(Tools, '/tool_table')
        api.add_resource(Tool, '/tool/<tool_no>')
        api.add_resource(ToolData, '/tool_data/<tool_no>/<element>')
        api.add_resource(Atc, '/atc')

        app.run(host="127.0.0.1", port=5002, threaded=True, debug=False, use_reloader=False)


# API Server

class RestApi(DataPlugin):
    """RestApi Plugin"""

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

class Atc(Resource):

    def get(self):

        atc_widget = getWidget("dynatc")

        mode = request.args["mode"]

        if mode == "spin":  # Rotate ATC
            # curl http://127.0.0.1:5002/atc\?mode\=spin\&steps\=5\&direction\=cw
            steps = request.args["steps"]
            direction = request.args["direction"]
            atc_widget.rotate(steps, direction)
        elif mode == "message":  # Message
            # curl http://127.0.0.1:5002/atc\?mode\=message\&message\=hola
            message = request.args["message"]
            atc_widget.atc_message(message)
        elif mode == "store":  # Store tool in pocket
            # curl http://127.0.0.1:5002/atc\?mode\=store\&pocket\=5\&tool\=7
            pocket = request.args["pocket"]
            tool = request.args["tool"]
            atc_widget.store_tool(int(pocket), int(tool))
        else:
            return 400

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


########################################################################################################################
#
#  Offset Table
#
########################################################################################################################
