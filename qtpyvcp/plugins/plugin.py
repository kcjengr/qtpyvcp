import inspect
from qtpy.QtCore import QObject, Signal
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


def isDataChan(obj):
    return isinstance(obj, DataChannel)


class DataPlugin(QObject):
    """DataPlugin."""

    def __init__(self):
        super(DataPlugin, self).__init__()

        self.channels = {name: obj for name, obj in
                         inspect.getmembers(self, isDataChan)}

    def getChannel(self, url):
        """Get data channel from URL.

        Args:
            url (str) : The URL of the channel to get.

        Returns:
            tuple : (chan_obj, chan_exp)
        """

        chan, sep, query = url.partition('?')
        raw_args = query.split('&')

        # print url, chan, raw_args

        args = []
        kwargs = {}
        for arg in [a for a in raw_args if a != '']:
            if '=' in arg:
                key, val = arg.split('=')
                kwargs[key] = val
            else:
                args.append(arg)

        # print chan, args, kwargs

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

    signal = Signal(object)

    def __init__(self, fget=None, fset=None, fstr=None, data=None, settable=False,
                 doc = None):
        super(DataChannel, self).__init__()

        self.fget = fget
        self.fset = fset
        self.fstr = fstr

        self.value = data

        self.settable = settable
        self.instance = None

        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def getValue(self, *args, **kwargs):
        """Channel data getter method."""
        if self.fget is None:
            return self.value
        return self.fget(self.instance, self, *args, **kwargs)

    def getString(self, *args, **kwargs):
        """Channel data getter method."""
        if self.fstr is None:
            return str(self.value)
        return self.fstr(self.instance, self, *args, **kwargs)

    def setValue(self, value):
        """Channel data setter method."""
        if self.fset is None:
            self.value = value
            self.signal.emit(value)
        else:
            self.fset(self.instance, self, value)

    def getter(self, fget):
        def inner(*args, **kwargs):
            fget(*args, **kwargs)

        self.fget = inner
        return self

    def setter(self, fset):
        def inner(*args, **kwargs):
            fset(*args, **kwargs)

        self.fset = inner
        return self

    def tostring(self, fstr):
        def inner(*args, **kwargs):
            return fstr(*args, **kwargs)

        self.fstr = inner
        return self

    def notify(self, slot, *args, **kwargs):
        # print 'Connecting %s to slot %s' % (self._signal, slot)
        if len(args) == 0 and len(kwargs) == 0:
            self.signal.connect(slot)
        else:
            if args[0] in ['string', 'str']:
                self.signal.connect(lambda: slot(self.getString(*args[1:], **kwargs)))
            else:
                self.signal.connect(lambda: slot(self.getValue(*args, **kwargs)))

    # fixme
    onValueChanged = notify

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        return self.getValue(*args, **kwargs)

    def __set__(self, instance, value):
        return self.setValue(value)

    def __getitem__(self, item):
        return self.value[item]

    def __str__(self):
        return self.getString()
