"""QtPyVCP HAL Interface"""

import signal
import _hal
import hal

from PySide6.QtCore import QObject, Signal, QTimer

import qtpyvcp
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

MAIN_WINDOW = qtpyvcp.WINDOWS.get("mainwindow")


class QPin(QObject):
    """QPin

    QPin is a QObject wrapper for a HAL pin and emits the valueChanged signal
    when the HAL pins value changes.

    Args:
        comp (_hal.component) : The HAL comp the pins should belong to.
        name (str) : The name of the HAL pin to create.
        typ (str) : The type of the HAL pin, one of `BOOL`, `FLOAT`, `U32` or `S32`.
        dir (str) : the direction of the HAL pin, one of `IN` or `OUT`.

    Properties:
        value (float | int | bool) : The the current value of the HAL pin.
        valueChanged (QSignal) : Signal that is emited when the value changes.
    """

    valueChanged = Signal(object)

    def __init__(self, comp, name, typ, dir, cycle_time=100):
        super(QPin, self).__init__(MAIN_WINDOW)

        self._pin = _hal.component.newpin(comp, name, typ, dir)
        self._val = self._pin.get()

        self.startTimer(cycle_time)

    def timerEvent(self, timer):
        tmp = self._pin.get()
        if tmp != self._val:
            self._val = tmp
            self.valueChanged.emit(tmp)

    @property
    def value(self):
        return self._pin.get()

    @value.setter
    def value(self, val):
        self._val = val
        self._pin.set(val)
        self.valueChanged.emit(val)


class QParam(QObject):
    """QParam
    TODO update desc.
    QParam is a QObject wrapper for a HAL namedparams and emits the valueChanged signal
    when the HAL param value changes.

    Args:
        comp (_hal.component) : The HAL comp the pins should belong to.
        name (str) : The name of the HAL pin to create.
        typ (str) : The type of the HAL pin, one of `BOOL`, `FLOAT`, `U32` or `S32`.
        dir (str) : the direction of the HAL pin, one of `IN` or `OUT`.

    Properties:
        value (float | int | bool) : The the current value of the HAL pin.
        valueChanged (QSignal) : Signal that is emited when the value changes.
    """

    valueChanged = Signal(object)

    def __init__(self, comp, name, pin_type=hal.HAL_BIT, access_mode=hal.HAL_RW, cycle_time=100):
        super(QParam, self).__init__(MAIN_WINDOW)
        self._param = _hal.component.newparam(comp, name, pin_type, access_mode)
        self._name = name
        self._val = self._param.get()

        self.startTimer(cycle_time)

    def timerEvent(self, timer):
        tmp = self._param.get()
        if tmp != self._val:
            self._val = tmp
            self.valueChanged.emit(tmp)

    @property
    def value(self):
        return self._param.get()

    @value.setter
    def value(self, val):
        self._val = val
        self._param.set(val)
        self.valueChanged.emit(val)

    @property
    def name(self):
        return self._name


class QComponent(QObject):
    """QComponent"""
    def __init__(self, comp_name):
        super(QComponent, self).__init__(MAIN_WINDOW)

        self.name = comp_name

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
        self.mode_map = {
            'ro': hal.HAL_RO,
            'rw': hal.HAL_RW
        }

        self._comp = _hal.component(comp_name)

        self._pins = {}
        self._params = {}

    def addPin(self, name, pin_type, direction):

        pin_type = self.type_map.get(pin_type.lower())
        pin_dir = self.dir_map.get(direction.lower())

        LOG.debug("Adding HAL pin: %s.%s (%s %s)", self.name, name, type, direction)

        pin = QPin(self._comp, name, pin_type, pin_dir)
        self._pins[name] = pin
        return pin

    def addParam(self, name, pin_type, access_mode):

        pin_type = self.type_map.get(pin_type.lower())
        access_mode = self.mode_map.get(access_mode.lower())
        LOG.debug("Adding PARAM params: %s %s", self.name, name)

        param = QParam(self._comp, name, pin_type, access_mode)
        self._params[name] = param
        return param

    def getParam(self, param_name):
        return self._params[param_name]
    
    def addParamsListener(self, name, *args):
        self._params[name].valueChanged.connect(*args)

    def removeParamsListener(self, name, *args):
        self._params[name].valueChanged.disconnect(*args)

    def getPin(self, pin_name):
        return self._pins[pin_name]

    def addListener(self, pin_name, *args):
        self._pins[pin_name].valueChanged.connect(*args)

    def removeListener(self, pin_name, *args):
        self._pins[pin_name].valueChanged.disconnect(*args)
        
    def addParamListener(self, param_name, *args):
        self._params[param_name].valueChanged.connect(*args)

    def removeParamListener(self, param_name, *args):
        self._params[param_name].valueChanged.disconnect(*args)

    def ready(self):
        self._comp.ready()

    def exit(self, *a, **kw):
        print(("Unloading '%s' HAL component ..." % self.name))
        return self._comp.exit(*a, **kw)

    def signal_handler(self, signal, frame):
        self.exit()

    def __getitem__(self, item):
        return self._pins[item]


# testing
def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    def printChange(new_val):
        print(("Value Changed", new_val))

    c = QComponent('test')
    c.addPin('input', "s32", "in")
    c.addPin('float_in', "s32", "in")
    c.getPin('input').valueChanged.connect(printChange)
    c.ready()

    app.exec()


if __name__ == "__main__":
    main()

