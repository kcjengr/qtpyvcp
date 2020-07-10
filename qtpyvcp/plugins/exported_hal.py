"""Exported HAL Plugin

This plugin exposes specific machine or program functions via HAL.
This is a framework level exposure which means a VCP does not
need to do anything specific other than enable the plugin
to have a number of standard Linuxcnc functions exposed via the
linuxcnc python bindings exposed via HAL.

ToDO: look to further yaml configuration options
"""

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import Plugin

from qtpyvcp import hal
from qtpyvcp.actions.machine_actions import feed_override, rapid_override
from qtpyvcp.actions.spindle_actions import override as spindle_override


LOG = getLogger(__name__)


class ExportedHal(Plugin):
    def __init__(self, **kwargs):
        super(ExportedHal, self).__init__()

    def initialiseFrameworkExposedHalPins(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = 'feed-override'
        self._feed_override_reset = comp.addPin(obj_name + ".reset", "bit", "in")
        self._feed_override_reset.valueChanged.connect(feed_override.reset)
        obj_name = 'rapid-override'
        self._rapid_override_reset = comp.addPin(obj_name + ".reset", "bit", "in")
        self._rapid_override_reset.valueChanged.connect(rapid_override.reset)
        obj_name = 'spindle-override'
        self._spindle_override_reset = comp.addPin(obj_name + ".reset", "bit", "in")
        self._spindle_override_reset.valueChanged.connect(spindle_override.reset)

    def initialise(self):
        LOG.debug('Initalizing framework exposed HAL pins')
        self.initialiseFrameworkExposedHalPins()
        self._initialized = True

    def terminate(self):
        pass
