from qtpyvcp import SETTINGS
from qtpyvcp.plugins import DataPlugin, DataChannel


class Settings(DataPlugin):
    def __init__(self):
        super(Settings, self).__init__()

        self.channels = SETTINGS

    def getChannel(self, url):

        try:
            chan_obj = SETTINGS[url]
            chan_exp = chan_obj.getValue
        except KeyError:
            return None, None

        return chan_obj, chan_exp

    def initialise(self):
        for name, obj in SETTINGS.items():
            print name, obj
