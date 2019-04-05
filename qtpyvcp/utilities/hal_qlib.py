"""QPin"""


import signal
import _hal
import hal

from qtpy.QtCore import QObject, Signal, QTimer


class QPin(QObject):

    valueChanged = Signal(object)

    def __init__(self, comp, name, typ, dir):
        super(QPin, self).__init__()

        self._pin = _hal.component.newpin(comp, name, typ, dir)
        self._val = self._pin.get()

        self.startTimer(100)

    def timerEvent(self, timer):
        tmp = self._pin.get()
        print(tmp, type(tmp))
        if tmp != self._val:
            self.valueChanged.emit(tmp)
            self._val = tmp

    @property
    def value(self):
        return self._pin.get()

    @value.setter
    def value(self, val):
        pass


class QComponent(QObject):
    def __init__(self, comp_name):
        super(QComponent, self).__init__()

        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self._comp = _hal.component(comp_name)
        self._pins = {}

    def newPin(self, name, typ, dir):
        pin = QPin(self._comp, name, typ, dir)
        self._pins[name] = pin

    def getPin(self, *a, **kw):
        return QPin(self.getpin(*a, **kw))

    def ready(self):
        self._comp.ready()

    def exit(self, *a, **kw):
        print("exit")
        return self._comp.exit(*a, **kw)

    def signal_handler(self, signal, frame):
        self.exit()


def main():
    from qtpy.QtWidgets import QApplication

    app = QApplication([])

    c = QComponent('test')
    c.newPin('input', hal.HAL_BIT, hal.HAL_IN)
    c.ready()

    app.exec_()


if __name__ == "__main__":
    main()
