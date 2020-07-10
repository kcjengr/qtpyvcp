import os

from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import Plugin

LOG = getLogger(__name__)


class PersistentDataManager(Plugin):
    def __init__(self, serialization_method='pickle', persistence_file=None):
        super(PersistentDataManager, self).__init__()

        self.serialization_method = serialization_method

        if not persistence_file:
            persistence_file = '.vcp_persistent_data.' + serialization_method

        if serialization_method == 'json':
            import json
            self.serializer = json
        else:
            import pickle
            self.serializer = pickle

        self.data = {}
        self.persistence_file = normalizePath(path=persistence_file,
                                              base=os.getenv('CONFIG_DIR', '~/'))

    def getData(self, name, default=None):
        return self.data.get(name, default)

    def setData(self, name, data):
        self.data[name] = data

    def initialise(self):
        if os.path.isfile(self.persistence_file):
            with open(self.persistence_file, 'r') as fh:
                try:
                    self.data = self.serializer.loads(fh.read())
                except:
                    LOG.exception("Error reading persistent data from file: %s",
                                  self.persistence_file)

    def terminate(self):
        LOG.debug("Writing persistent data to file: %s", self.persistence_file)
        if self.serialization_method == 'json':
            str_data = self.serializer.dumps(self.data, indent=4, sort_keys=True)
        else:
            str_data = self.serializer.dumps(self.data,
                                             protocol=self.serializer.HIGHEST_PROTOCOL)

        with open(self.persistence_file, 'w') as fh:
            fh.write(str_data)
