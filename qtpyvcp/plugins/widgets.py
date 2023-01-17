"""
Widgets
--------

This plugin provides the access to all the UI widgets

This plugin is not loaded by default, so to use it you will first
need to add it to your VCPs YAML config file.

YAML configuration:

.. code-block:: yaml

    data_plugins:
      widgets:
        provider: qtpyvcp.plugins.widgets:Widgets

"""

from qtpyvcp import WINDOWS

from qtpy.QtCore import QTimer
from qtpyvcp.plugins import DataPlugin, DataChannel

# Setup logging
from qtpyvcp.utilities import logger

LOG = logger.getLogger("QtPyVCP." + __name__)


class Widgets(DataPlugin):
    """Widgets Plugin"""

    def __init__(self):
        super(Widgets, self).__init__()

        widget_list = dict()
        self.widget_level = 0
        self.tab = "\t"

    def postGuiInitialise(self, window):
        for name, window in list(WINDOWS.items()):
            LOG.debug(f"Window = {name}")
            self.widget_level = 1
            self.getChilds(window)

    def getChilds(self, widget):
        for child in widget.children():
            LOG.debug(f"{self.tab*self.widget_level}{child}")
            self.widget_level += 1
            if child.children():
                self.getProperties(child)
                self.getChilds(child)  # Warning recursivity!!
            else:
                self.widget_level = 1

    def getProperties(self, widget):

        # properties_names = widget.dynamicPropertyNames()
        # if properties_names:
        #
        #     for property_name in properties_names:
        #         # Decode the QByteArray into a string.
        #         name: str = str(property_name, 'utf-8')
        #         # Get the property value
        #         value: str = widget.property(name)
        #
        #         LOG.debug(f"{self.tab*self.widget_level}{name} : {value}")
        #
        #     #     properties.append({'name': name, 'value': value})
        #     #
        #     # print(properties)

        widget_properties = widget.metaObject()
        count = widget_properties.propertyCount()

        for i in range(0, count - 1):
            property = widget_properties.property(i)
            name = property.name()
            value = widget.property(name)

            LOG.debug(f"{self.tab*self.widget_level}{name} : {value}")

