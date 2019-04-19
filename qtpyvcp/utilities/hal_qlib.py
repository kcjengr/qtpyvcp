"""QPin"""

import signal
import _hal
import hal

from qtpy.QtCore import QObject, Signal, QTimer


class QPin(QObject):
    valueChanged = Signal(object)
    valueIncreased = Signal(object)
    valueDecreased = Signal(object)

    def __init__(self, comp, name, typ, dir):
        super(QPin, self).__init__()

        self._pin = _hal.component.newpin(comp, name, typ, dir)
        self._val = self._pin.get()

        self.startTimer(100)

    def timerEvent(self, timer):
        tmp = self._pin.get()
        if tmp != self._val:
            self.valueChanged.emit(tmp)
            if tmp > self._val:
                self.valueIncreased.emit(tmp)
            else:
                self.valueDecreased.emit(tmp)
            self._val = tmp

    @property
    def value(self):
        return self._pin.get()

    @value.setter
    def value(self, val):
        self._pin.set(val)


class QComponent(QObject):
    def __init__(self, comp_name):
        super(QComponent, self).__init__()

        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.type_map = {
            'float': hal.HAL_FLOAT,
            's32': hal.HAL_S32,
            'u32': hal.HAL_U32,
            'bit': hal.HAL_BIT
        }

        self.dir_map = {
            'in': hal.HAL_IN,
            'out': hal.HAL_OUT,
            'io': hal.HAL_IO
        }

        self._comp = _hal.component(comp_name)
        self._pins = {}

    def newPin(self, name, type, direction):

        pin_type = self.type_map.get(type.lower())
        pin_dir = self.dir_map.get(direction.lower())

        pin = QPin(self._comp, name, pin_type, pin_dir)
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

    def __getitem__(self, item):
        return self._pins[item]


def main():
    from qtpy.QtWidgets import QApplication

    app = QApplication([])

    def printChange(new_val):
        print("Value Changed", new_val)

    c = QComponent('test')
    c.newPin('input', "s32", "in")
    c.newPin('float_in', "s32", "in")
    c['input'].valueChanged.connect(printChange)
    c.ready()

    app.exec_()


if __name__ == "__main__":
    main()
