from qtpy.QtCore import QObject, Signal
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

class QtPyVCPDataPlugin(QObject):
    """QtPyVCPDataPlugin."""

    protocol = None

    def __init__(self):
        super(QtPyVCPDataPlugin, self).__init__()

    def initialise(self):
        """Initialize the data plugin.

        This method is called after the main event loop has started. Any timers
        or threads used by the plugin should be started here.
        """
        pass

    def terminate(self):
        """Terminate the data plugin.

        This is called right before the main event loop exits. Any cleanup
        of the plugin should be done here, such as saving data to a file.
        """
        pass


class QtPyVCPDataChannel(QObject):
    """QtPyVCPChannel.

    Args:
        description (str) : A human readable description of the item.
    """

    valueChanged = Signal(object)

    def __init__(self, description=''):
        super(QtPyVCPDataChannel, self).__init__()

        self.description = description

    def handleQuery(self, query):
        """Query channel value.

        Args:
            query (str) : The name of the value to query. If no query
                is passed or it is an empty string the current value of
                the ``value`` property will be returned.

        Returns:
            The queried value, or None.
        """
        try:
            return getattr(self, query or 'value')
        except AttributeError:
            LOG.exception("Failed to handle query: {}".format(query))
            return None

    def handleAssigment(self, attr, value):
        raise NotImplemented
        # setattr(self, attr, value)

    @property
    def value(self):
        """Channel value property.

        In a channel implementation the `value` property should return the
        current value of the channel. If getting the value is reasonably
        fast and light (e.g. dict lookup) then that can be done here, but if
        it may take some time (e.g. over a network), then this method should
        return a cashed value that is updated periodically.
        """
        pass

    def onValueChanged(self, slot):
        """Connect a callback to the valueChanged signal.

        Args:
            slot : The method to call when the value changes.
        """
        self.valueChanged.connect(slot)

