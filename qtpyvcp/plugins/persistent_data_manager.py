import os
import json

from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin

LOG = getLogger(__name__)


class PersistentDataManager(DataPlugin):
    def __init__(self, persistence_file='.vcp_data.json'):
        super(PersistentDataManager, self).__init__()

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
                    self.data = json.loads(fh.read())
                except:
                    LOG.exception("Error reading persistent data from file: %s",
                                  self.persistence_file)

    def terminate(self):
        LOG.debug("Writing persistent data to file: %s", self.persistence_file)
        with open(self.persistence_file, 'w') as fh:
            fh.write(json.dumps(self.data, indent=4, sort_keys=True))
