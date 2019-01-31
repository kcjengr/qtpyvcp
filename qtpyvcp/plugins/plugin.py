from qtpy.QtCore import QObject, Signal
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

class DataPlugin(QObject):
    """DataPlugin."""

    def __init__(self):
        super(DataPlugin, self).__init__()

        self.channels = {chan: getattr(self, chan) for chan in dir(self) if
                         isinstance(getattr(self, chan), DataChannel)}

    def getChannel(self, url):
        """Get data channel from URL.

        Args:
            url (str) : The URL of the channel to get.

        Returns:
            tuple : (chan_obj, chan_exp)
        """

        chan, sep, query = url.partition('?')
        raw_args = query.split('&')

        print url, chan, raw_args

        args = []
        kwargs = {}
        for arg in [a for a in raw_args if a != '']:
            if '=' in arg:
                key, val = arg.split('=')
                kwargs[key] = val
            else:
                args.append(arg)

        print chan, args, kwargs

        try:
            chan_obj = self.channels[chan]
            if len(args) > 0 and args[0] in ('string', 'text', 'str'):
                chan_exp = lambda: chan_obj.getString(*args[1:], **kwargs)
            else:
                chan_exp = lambda: chan_obj.getValue(*args, **kwargs)

        except (KeyError, SyntaxError):
            return None, None

        return chan_obj, chan_exp

    def initialise(self):
        """Initialize the data plugin.

        This method is called after the main event loop has started. Any timers
        or threads used by the plugin should be started here.
        """
        pass

    def terminate(self):
        """Terminate the data plugin.

        This is called right before the main event loop exits. Any cleanup
        of the plugin should be done here, such as saving persistent data.
        """
        pass


class DataChannel(QObject):

    _signal = Signal(object)

    def __init__(self, fget=None, fset=None, fstr=None, data=None, settable=False,
                 doc = None):
        super(DataChannel, self).__init__()

        self.fget = fget
        self.fset = fset
        self.fstr = fstr

        self._data = data

        self.settable = settable

        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def getValue(self, *args, **kwargs):
        """Channel data getter method."""
        if self.fget is None:
            return self._data
        return self.fget(self, *args, **kwargs)

    def getString(self, *args, **kwargs):
        """Channel data getter method."""
        if self.fstr is None:
            return str(self._data)
        return self.fstr(*args, **kwargs)

    def setValue(self, value):
        """Channel data setter method."""
        if self.fset is None:
            if self.settable:
                self._data = value
                self._signal.emit(value)
            else:
                raise AttributeError('Channel is read only')
        else:
            self.fset(value)

    def getter(self, fget):
        def inner(*args, **kwargs):
            fget(self, *args, **kwargs)

        self.fget = inner
        return self

    def setter(self, fset):
        def inner(*args, **kwargs):
            fset(*args, **kwargs)
            self._signal.emit(self._data)

        self.fset = inner
        return self

    def tostring(self, fstr):
        def inner(*args, **kwargs):
            return fstr(self, *args, **kwargs)

        self.fstr = inner
        return self

    def notify(self, slot):
        # print 'Connecting %s to slot %s' % (self._signal, slot)
        self._signal.connect(slot)

    # fixme
    onValueChanged = notify

    def __call__(self, *args, **kwargs):
        return self.getValue(*args, **kwargs)

    def __set__(self, instance, value):
        return self.setValue(value)

    def __getitem__(self, item):
        return self._data[item]

    # def __str__(self):
    #     return self.getString()
