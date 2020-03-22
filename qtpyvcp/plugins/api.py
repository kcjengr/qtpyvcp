#   Copyright (c) 2020 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.


from thread import *

from wsgiref.simple_server import make_server
import falcon

from qtpyvcp import PLUGINS
from qtpyvcp.plugins import DataPlugin
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


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

        api = falcon.API()

        for name, obj in PLUGINS.iteritems():
            setattr(self, name, Channel(obj))
            api.add_route('/{}'.format(name), getattr(self, name))

        host = "0.0.0.0"
        port = 1337

        self.httpd = make_server(host, port, api)
        LOG.info('listening on {}:{}'.format(host, port))

    def initialise(self):
        # Serve until process is killed
        start_new_thread(self.threaded, ())

    def threaded(self):
        self.httpd.serve_forever()
