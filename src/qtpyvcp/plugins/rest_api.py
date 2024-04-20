import threading

from flask import Flask, request
# from flask_restful import Resource, Api

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


# API Server

class RestApi(DataPlugin):
    """RestApi Plugin"""

    def __init__(self):
        super(RestApi, self).__init__()
        self.app = None
        self.api_mutex = None
        self.api_thread = None

    def initialise(self):
        # Create a thread for checking the HAL pins and sigs
        self.api_mutex = threading.Lock()
        self.api_thread = threading.Thread(target=self.rest_api_thread, name="ApiThread")
        self.api_thread.daemon = True
        self.api_thread.start()

    def rest_api_thread(self):
        self.app = Flask('QtPyVcpAPI')

########################################################################################################################
#
#  ATC
#
########################################################################################################################

        @self.app.route('/atc')
        def _atc():

            print("################################# INIT #################################")

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
                return '400'
            
            print("################################# DONE #################################")
            return '200'
########################################################################################################################
#
#  Tools
#
########################################################################################################################

        @self.app.route('/tools')
        def _tools():
            tooltable_plugin = getPlugin('tooltable')
            tool_table = tooltable_plugin.getToolTable()
            return tool_table

        @self.app.route('/tool')
        def _tool():
            tool = request.args["tool"]
            tooltable_plugin = getPlugin('tooltable')
            tool_table = tooltable_plugin.getToolTable()

            tool_data = tool_table.get(int(float(tool)))

            return {f"tool {tool}": tool_data}

        @self.app.route('/tool_data')
        def _tool_data(tool_no, element):
            tool = request.args["tool"]
            element = request.args["element"]
            tooltable_plugin = getPlugin('tooltable')
            tool_table = tooltable_plugin.getToolTable()

            data = tool_table.get(int(tool))
            tool_data = data.get(element)

            return {f"tool {tool}": tool_data}

########################################################################################################################
#
#  Offset Table
#
########################################################################################################################

########################################################################################################################
#
#  Start the trhead
#
########################################################################################################################

        self.app.run(host="127.0.0.1", port=5002, threaded=False, processes=1)
        # self.app.run(host="127.0.0.1", port=5002, debug=False, use_reloader=False)

    def terminate(self):
        pass
