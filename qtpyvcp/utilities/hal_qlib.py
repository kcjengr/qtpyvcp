"""QPin"""

import _hal, hal
from qtpy.QtCore import QObject, Signal


class QPin(QObject, hal.Pin):
    """QPin object, represents a single HAL pin.
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

    def __init__(self, item):
        super(QPin, self).__init__(item=item)
        print "##################"
        # self._item_wrap(self._item)
        self._prev = None

        # start the QPin update timer
        self.startTimer(100)

    # @classmethod
    # def update_all(self):
    #     if not self.UPDATE:
    #         return
    #     kill = []
    #     for p in self.REGISTRY:
    #         try:
    #             p.update()
    #         except:
    #             kill.append(p)
    #             print "Error updating pin %s; Removing" % p
    #     for p in kill:
    #         self.REGISTRY.remove(p)
    #     return self.UPDATE

    def timerEvent(self, timer):
        print "Timout"
        # tmp = self.get()
        # if tmp != self._prev:
        #     self.valueChanged.emit(tmp)
        # self._prev = tmp


class QHalComponent(_hal.component):
    def __init__(self, comp_name):
        super(QHalComponent, self).__init__(comp_name)

    def newPin(self, *a, **kw):
        return QPin(self.newpin(*a, **kw))

    def getPin(self, *a, **kw):
        return QPin(self.getpin(*a, **kw))

    # def exit(self, *a, **kw):
    #     return self.exit(*a, **kw)
    #
    # def __getitem__(self, k):
    #     return self.comp[k]
    #
    # def __setitem__(self, k, v):
    #     self.comp[k] = v


class QTestPin(QObject):
    def __init__(self):
        super(QTestPin, self).__init__()

        self.startTimer(100)

    def timerEvent(self, timer):
        print "timout"


def main():
    from qtpy.QtWidgets import QApplication

    app = QApplication([])

    c = QHalComponent('test')
    c.newPin('input', hal.HAL_BIT, hal.HAL_IN)
    c.ready()

    print c

    app.exec_()


if __name__ == "__main__":
    main()
