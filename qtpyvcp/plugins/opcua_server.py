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

from opcua import Server
from opcua.common.events import Event

# from IPython import embed

from qtpyvcp import PLUGINS
from qtpyvcp.plugins import DataPlugin
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


class OpcUA(DataPlugin):
    def __init__(self):
        super(OpcUA, self).__init__()

        # https://github.com/FreeOpcUa/freeopcua/blob/master/python/examples/server.py

        # setup our server
        self.server = Server()

        address = '0.0.0.0'
        port = 4840

        self.endpoint = "opc.tcp://{}:{}/qtpyvcp/server/".format(address, port)

        self.server.set_endpoint(self.endpoint)

        self.server.set_server_name("QtPyVCP OpcUa Server")

        # setup our own namespace, not really necessary but should as spec
        uri = "http://qtpyvcp.com/"
        self.idx = self.server.register_namespace(uri)

        # get Objects node, this is where we should put our nodes
        self.objects = self.server.get_objects_node()

        LOG.debug("objects folder: {}".format(self.objects))
        for name, obj in PLUGINS.items():
            myobject = self.objects.add_object(self.idx, name)
            # myvar = myobject.add_variable(idx, "MyVariable", [16, 56])
            # myprop = myobject.add_property(idx, "myprop", 9.9)
            # myfolder = myobject.add_folder(idx, "myfolder")

        # uncomment next lines to subscribe to changes on server side
        # sclt = SubHandler()
        # sub = server.create_subscription(100, sclt)
        # handle = sub.subscribe_data_change(myvar) #keep handle if you want to delete the particular subscription later

        ev = Event()        # start ipython shell so users can test things
        # embed()

    def initialise(self):
        LOG.debug("Starting OPC UA server at: %s", self.endpoint)
        self.server.start()

    def terminate(self):
        LOG.debug("Stopping OPC UA server...")
        self.server.stop()
