"""
GCodeProperties
--------

This plugin provides the information about sizes and times

This plugin is not loaded by default, so to use it you will first
need to add it to your VCPs YAML config file.

YAML configuration:

.. code-block:: yaml

    data_plugins:
      gcode_properties:
        provider: qtpyvcp.plugins.gcode_properties:GCodeProperties

"""
import os
import pprint
import shutil
import gcode
import linuxcnc

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import DataPlugin, DataChannel

LOG = getLogger(__name__)
STATUS = getPlugin('status')
INFO = Info()

INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))


from twisted.internet import reactor, protocol


class Echo(protocol.Protocol):
    """This is just about the simplest possible protocol"""

    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print(data)
        self.transport.write(data)



class LinuxcncParams(DataPlugin):
    """LinuxcncParams Plugin"""
    def __init__(self):
        super(LinuxcncParams, self).__init__()

        inifile = os.getenv("INI_FILE_NAME")
        self.stat = STATUS
        self.ini = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        self.config_dir = os.path.dirname(inifile)



    @DataChannel
    def params_example(self, chan):
        """The current file name.

        Args:
            None

        Returns:
            The current open file name as a string.

        Channel syntax::

            gcode_properties:file_name

        """

        return chan.value

    def initialise(self):
        
        factory = protocol.ServerFactory()
        factory.protocol = Echo
        reactor.listenTCP(8000, factory)
        reactor.run()

    def terminate(self):
        pass