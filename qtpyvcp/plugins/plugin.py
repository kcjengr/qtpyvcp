from qtpy.QtCore import QObject, Signal
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

class DataPlugin(QObject):
    """QtPyVCPDataPlugin."""

    def __init__(self):
        super(DataPlugin, self).__init__()

        self.channels = {chan: getattr(self, chan) for chan in dir(self) if
                         isinstance(getattr(self, chan), DataChannel)}

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

    def __init__(self, fget=None, fset=None, fstr=None, sig=None, doc=None):
        super(DataChannel, self).__init__()
        print 'fget:', fget

        self.fget = fget
        self.fset = fset
        self.fstr = fstr

        if sig is not None:
            self._signal = sig

        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

        self._data = None

    def getData(self, *args, **kwargs):
        if self.fget is None:
            return self._data
        return self.fget(self, *args, **kwargs)

    def getter(self, fget):
        print 'fget:', fget

        def inner(*args, **kwargs):
            fget(self, *args, **kwargs)

        self.fget = inner
        return self
        return type(self)(fget=inner, fset=self.fset, fstr=self.fstr,
                          sig=self._signal, doc=self.__doc__)

    def setData(self, *args, **kwargs):
        if self.fset is None:
            if self.__doc__ is not None:
                print self.__doc__.split('\n')[0].strip()
            raise AttributeError('Channel is read only')
        self.fset(self, *args, **kwargs)

    def setter(self, fset):
        print 'fset:', fset

        def inner(*args, **kwargs):
            fset(*args, **kwargs)
            self._signal.emit(self._data)

        self.fset = inner
        return self
        return type(self)(fget=self.fget, fset=inner, fstr=self.fstr,
                          sig=self._signal, doc=self.__doc__)

    def __str__(self, *args, **kwargs):
        if self.fstr is None:
            print "fstr is none"
            return str(self._data)
        return self.fstr(self, *args, **kwargs)

    def tostring(self, fstr):
        print 'fstr:', fstr

        def inner(*args, **kwargs):
            return fstr(*args, **kwargs)

        self.fstr = inner
        return self
        return type(self)(fget=self.fget, fset=self.fset, fstr=inner,
                          sig=self._signal, doc=self.__doc__)

    def notify(self, slot):
        print 'Connecting %s to slot %s' % (self._signal, slot)
        self._signal.connect(slot)

    # fixme
    onValueChanged = notify

    def __getitem__(self, item):
        return self._data[item]

    def __call__(self, *args, **kwargs):
        return self.getData(*args, **kwargs)
