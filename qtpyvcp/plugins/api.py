# examples/things.py

# import thread module
from _thread import *
import threading

# Let's get this party started!

from wsgiref.simple_server import make_server
import falcon

from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin, loadDataPlugins
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


# Falcon follows the REST architectural style, meaning (among
# other things) that you think in terms of resources and state
# transitions, which map to HTTP verbs.
class Channel:
    def __init__(self, plugin):
        self.plugin = plugin

    def on_get(self, req, resp):
        """Handles GET requests"""

        channel = req.query_string

        resp_data = self.plugin.getChannel(channel)[0]



        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = str(resp_data)


class VcpApi(DataPlugin):
    def __init__(self):
        super(VcpApi, self).__init__()

        # falcon.API instances are callable WSGI apps
        # in larger applications the app is created in a separate file
        api = falcon.API()

        clock = getPlugin('clock')
        status = getPlugin('status')

        # Resources are represented by long-lived class instances
        self.clock = Channel(clock)
        self.status = Channel(status)

        # things will handle all requests to the '/things' URL path
        api.add_route('/clock', self.clock)
        api.add_route('/status', self.status)

        host = "0.0.0.0"
        port = 1337

        self.httpd = make_server(host, port, api)
        LOG.info('listening on {}:{}'.format(host, port))

    def initialise(self):
        # Serve until process is killed
        start_new_thread(self.threaded, ())

    def threaded(self):
        self.httpd.serve_forever()
