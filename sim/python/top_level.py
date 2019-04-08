#   This is a component of LinuxCNC
#   Copyright 2011, 2013, 2014 Dewey Garrett <dgarrett@panix.com>,
#   Michael Haberler <git@mah.priv.at>, Norbert Schechner <nieson@web.de>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import os
import sys

import emccanon
import interpreter

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket


def __init__(self):
    print("__init__")

    if hasattr(interpreter, 'this'):
        if self is not interpreter.this:
            print("__init__: self not is this")
    else:
        print("__init__: no 'this' attribute")

    port = 1337

    get_params = GetParams
    get_params.params = self.params

    server = SimpleWebSocketServer('', port, get_params)
    server.serveforever()


class GetParams(WebSocket):
    params = None

    def handleMessage(self):
        offset = int(self.data)
        data = str(self.params[offset])
        print(data)
        self.sendMessage(data.encode("UTF-8"))

    # def handleConnected(self):
    #     print(self.address, 'connected')
    #
    # def handleClose(self):
    #     print(self.address, 'closed')

