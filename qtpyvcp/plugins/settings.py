import os
import json

from qtpyvcp import SETTINGS, CONFIG
from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.settings import addSetting
from qtpyvcp.plugins import DataPlugin, DataChannel

LOG = getLogger(__name__)


class Settings(DataPlugin):
    def __init__(self, persistence_file='.settings.json'):
        super(Settings, self).__init__()

        self.channels = SETTINGS
        self.settings = {}

        # load settings defined in YAML file
        for setting_name, kwargs in CONFIG['settings'].items():
            addSetting(setting_name, **kwargs)

        self.persistence_file = normalizePath(path=persistence_file,
                                              base=os.getenv('CONFIG_DIR', '~/'))

    def getChannel(self, url):

        try:
            chan_obj = SETTINGS[url]
            chan_exp = chan_obj.getValue
        except KeyError:
            return None, None

        return chan_obj, chan_exp

    def initialise(self):
        if os.path.isfile(self.persistence_file):
            with open(self.persistence_file, 'r') as fh:
                try:
                    self.settings = json.loads(fh.read())
                except:
                    LOG.exception("Error loading persistent settings from %s",
                                  self.persistence_file)

        for key, value in self.settings.items():
            try:
                SETTINGS[key].setValue(value)
            except KeyError:
                pass

    def terminate(self):
        LOG.debug("Saving persistent settings to %s", self.persistence_file)
        settings = {}
        for key, obj in SETTINGS.items():
            if obj.persistent == True:
                value = obj.getValue()
                if obj.default_value != value:
                    settings[key] = value

        with open(self.persistence_file, 'w') as fh:
            fh.write(json.dumps(settings, indent=4, sort_keys=True))
