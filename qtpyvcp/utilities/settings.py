from qtpy.QtCore import QObject, Signal
from qtpyvcp import SETTINGS


def getSetting(id, default=None):
    return SETTINGS.get(id, default)


def setSetting(id, value):
    try:
        SETTINGS[id].setValue(value)
    except KeyError:
        raise ValueError("The setting '%s' does not exist" % id)


def addSetting(id, **kwargs):
    SETTINGS[id] = Setting(**kwargs)


class Setting(QObject):

    signal = Signal(object)

    def __init__(self, fget=None, fset=None, freset=None, default_value=False,
                 max_value=None, min_value=None, persistent=True, description=None):
        super(Setting, self).__init__()

        self.fget = fget
        self.fset = fset
        self.freset = freset

        self.value_type = type(default_value)

        self.max_value = max_value
        self.min_value = min_value

        self.value_type = type(default_value)
        self.value = self.default_value = default_value

        self.persistent = persistent

        self.instance = None

        if description is None and fget is not None:
            description = fget.__doc__
        self.__doc__ = description

    def getValue(self, *args, **kwargs):
        """Setting value get method."""
        if self.fget is None:
            return self.value
        return self.fget(self.instance, self, *args, **kwargs)

    def setValue(self, value):
        """Setting value set method."""
        if self.fset is None:
            value = self.value_type(value)
            if self.value_type in (int, float):
                self.value = self.clampValue(value)
            self.signal.emit(value)
        else:
            self.fset(self.instance, self, value)

    def resetValue(self):
        """Setting value reset method."""
        if self.freset is None:
            self.setValue(self.default_value)
        else:
            self.freset(self.instance, self, self.default_value)

    def clampValue(self, value):
        if self.max_value is not None:
            value = min(value, self.max_value)
        if self.min_value is not None:
            value = max(value, self.min_value)
        return value

    def normalizeValue(self, value):
        if type(value) != self.value_type:
            try:
                value = self.value_type(value)
            except ValueError:
                value = self.value

        return self.clampValue(value)

    def getter(self, fget):
        def inner(*args, **kwargs):
            fget(*args, **kwargs)

        self.fget = inner
        return self

    def setter(self, fset):
        def inner(*args, **kwargs):
            if args[0] is None:
                return fset(*args[1:], **kwargs)
            fset(*args, **kwargs)

        self.fset = inner
        return self

    def resetter(self, freset):
        def inner(*args, **kwargs):
            if args[0] is None:
                return freset(*args[1:], **kwargs)
            freset(*args, **kwargs)

        self.freset = inner
        return self

    def notify(self, slot):
        # print 'Connecting %s to slot %s' % (self._signal, slot)
        self.signal.connect(slot)

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        return self.getValue(*args, **kwargs)

    def __set__(self, instance, value):
        return self.setValue(value)

    def __str__(self):
        return str(self.value)


def setting(id, default_value=False, max_value=None, min_value=None, persistent=True):
    def wrapper(func):
        obj = Setting(default_value=default_value,
                      max_value=max_value,
                      min_value=min_value,
                      persistent=persistent,
                      description=func.__doc__)

        SETTINGS[id] = obj
        return obj
    return wrapper


if __name__ == "__main__":

    def printChanged(val):
        print "Setting changed:", val

    s = Setting(default_value=9)
    s.notify(printChanged)
    print repr(s)
    print s.value
    s.setValue(34)
    print s.value


    @setting('jog.speed', default_value=10.0, persistent=False)
    def speed(setting_obj):
        return setting_obj.value

    @speed.setter
    def speed(setting_obj, val):
        print 'in speed setter'
        print setting_obj, val
        setting_obj.value = val
        setting_obj.signal.emit(val)



    print SETTINGS
    print repr(speed)
    speed.setValue(12.0)
    print speed.value
    speed.setValue(13.0)
    print speed.value
    speed.setValue(14.0)
    print speed.value


    class Test(QObject):
        def __init__(self):
            print "inited"


        @setting('test.setting', False, True)
        def on(self, setting_obj):
            return setting_obj.value

        @on.setter
        def on(self, setting_obj, val):
            print "in settter", val
            setting_obj.value = val
            setting_obj.signal.emit(val)

    t = Test()
    print t

    t.on.notify(printChanged)


    print t.on.value
    t.on.setValue(True)
    print t.on.value

    print "resenting"
    t.on.resetValue()
    print t.on.value

    print SETTINGS

    SETTINGS['test.setting'].setValue(False)
    print t.on.value

    SETTINGS['jog.speed'].setValue(42.0)
    print SETTINGS['jog.speed'].value
