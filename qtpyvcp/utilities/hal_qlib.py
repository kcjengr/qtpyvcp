import _hal, hal
import linuxcnc

from qtpy.QtCore import QObject, Signal

class QPin(QObject, hal.Pin):
    """QPin object, represents a single LinuxCNC HAL pin, enables reading.
        writing and connecting slots to be called when the HAL pin value changes.

    Attributes:
        log_change (bool):      whether to log changes of pin's value
        pin_name (str):         the name of the HAL pin
        settable (bool):        weather the HAL pin is writable
        type (type):            the python type of the HAL pin
        value (varies):         the value of the HAL pin as of last check
        valueChanged (QtSignal): signal emitted when the HAL pin value changes
    """

    valueChanged = Signal([bool], [float], [int])

    REGISTRY = []
    UPDATE = False

    def __init__(self, *a, **kw):
        QObject.__init__(self)
        hal.Pin.__init__(self, *a, **kw)
        self._item_wrap(self._item)
        self._prev = None
        self.REGISTRY.append(self)
        self.update_start()

    def update(self):
        tmp = self.get()
        if tmp != self._prev:
            self.emit('value-changed')
        self._prev = tmp

    @classmethod
    def update_all(self):
        if not self.UPDATE:
            return
        kill = []
        for p in self.REGISTRY:
            try:
                p.update()
            except:
                kill.append(p)
                print "Error updating pin %s; Removing" % p
        for p in kill:
            self.REGISTRY.remove(p)
        return self.UPDATE

    @classmethod
    def update_start(self, timeout=100):
        if GPin.UPDATE:
            return
        GPin.UPDATE = True
        gobject.timeout_add(timeout, self.update_all)

    @classmethod
    def update_stop(self, timeout=100):
        GPin.UPDATE = False

class GComponent:
    def __init__(self, comp):
        if isinstance(comp, GComponent):
            comp = comp.comp
        self.comp = comp

    def newpin(self, *a, **kw): return GPin(_hal.component.newpin(self.comp, *a, **kw))
    def getpin(self, *a, **kw): return GPin(_hal.component.getpin(self.comp, *a, **kw))

    def exit(self, *a, **kw): return self.comp.exit(*a, **kw)

    def __getitem__(self, k): return self.comp[k]
    def __setitem__(self, k, v): self.comp[k] = v
