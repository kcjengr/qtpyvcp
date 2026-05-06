"""Settings Plugin"""

import os

from qtpyvcp import SETTINGS, CONFIG
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.settings import addSetting
from qtpyvcp.plugins import DataPlugin, getPlugin

IN_DESIGNER = os.getenv('DESIGNER', False)
SETTINGS_TRACE_ENABLED = str(os.getenv('QTPYVCP_SETTINGS_TRACE', '')).strip().lower() in (
    '1', 'true', 'yes', 'on'
)

LOG = getLogger(__name__)


class Settings(DataPlugin):
    def __init__(self, **kwargs):
        super(Settings, self).__init__()

        self.channels = SETTINGS

        self.data_manager = getPlugin('persistent_data_manager')

        # load settings defined in YAML file
        if 'settings' in CONFIG:
            for setting_name, kwargs in list(CONFIG['settings'].items()):
                addSetting(setting_name, **kwargs)

        # add default settings for designer mode
        if IN_DESIGNER and not SETTINGS:
            addSetting('dro.display-units', default_value=0, options=['Auto', 'Inch', 'Metric'])
            addSetting('dro.lathe-radius-mode', default_value=0, options=['Auto', 'Radius', 'Diameter'])
            addSetting('dro.inch-format', default_value='%9.4f', value_type=str)
            addSetting('dro.millimeter-format', default_value='%9.3f', value_type=str)
            addSetting('dro.degree-format', default_value='%9.2f', value_type=str)
            addSetting('touch-probe.diameter-offset', default_value=0.123123, persistent=True, min_value=0, max_value=1)

    def getChannel(self, url):

        try:
            chan_obj = SETTINGS[url]
            chan_exp = chan_obj.getValue
        except KeyError:
            return None, None

        return chan_obj, chan_exp

    def initialise(self):
        settings = self.data_manager.getData('settings', {})

        if SETTINGS_TRACE_ENABLED:
            if 'drill.feed-mode' in settings:
                LOG.info("[settings-trace] initialise persistent drill.feed-mode=%r", settings.get('drill.feed-mode'))
            else:
                LOG.info("[settings-trace] initialise no persistent drill.feed-mode entry")

        for key, value in list(settings.items()):
            try:
                SETTINGS[key].setValue(value)
                if SETTINGS_TRACE_ENABLED and key == 'drill.feed-mode':
                    LOG.info("[settings-trace] initialise applied drill.feed-mode=%r", SETTINGS[key].getValue())
            except KeyError:
                pass

    def terminate(self):
        settings = {}
        for key, obj in list(SETTINGS.items()):
            if obj.persistent == True:
                value = obj.getValue()
                if obj.default_value != value:
                    settings[key] = value

        if SETTINGS_TRACE_ENABLED and 'drill.feed-mode' in SETTINGS:
            current = SETTINGS['drill.feed-mode'].getValue()
            default = SETTINGS['drill.feed-mode'].default_value
            saved = settings.get('drill.feed-mode', '<not-saved>')
            LOG.info(
                "[settings-trace] terminate drill.feed-mode current=%r default=%r saved=%r",
                current,
                default,
                saved,
            )

        self.data_manager.setData('settings', settings)
