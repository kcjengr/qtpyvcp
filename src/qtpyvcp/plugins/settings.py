"""Settings Plugin"""

from qtpyvcp import SETTINGS, CONFIG
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.settings import addSetting
from qtpyvcp.plugins import DataPlugin, getPlugin

LOG = getLogger(__name__)


class Settings(DataPlugin):
    def __init__(self, **kwargs):
        super(Settings, self).__init__()

        self.channels = SETTINGS

        self.data_manager = getPlugin('persistent_data_manager')

        # load settings defined in YAML file
        for setting_name, kwargs in list(CONFIG['settings'].items()):
            addSetting(setting_name, **kwargs)

    def getChannel(self, url):

        try:
            chan_obj = SETTINGS[url]
            chan_exp = chan_obj.getValue
        except KeyError:
            return None, None

        return chan_obj, chan_exp

    def postGuiInitialise(self, window):
        settings = self.data_manager.getData('settings', {})

        for key, value in list(settings.items()):
            try:
                SETTINGS[key].setValue(value)
            except KeyError:
                
                LOG.error("########################## FAILED TO INITIALIZE SETTINGS")
                LOG.error(f"########################## {key}")
                pass

    def terminate(self):
        settings = {}
        for key, obj in list(SETTINGS.items()):
            LOG.debug(f"TERMINATE | KEY: {key} ,obj : {obj}")
            if obj.persistent == True:
                value = obj.getValue()
                if obj.default_value != value:
                    settings[key] = value

        self.data_manager.setData('settings', settings)
