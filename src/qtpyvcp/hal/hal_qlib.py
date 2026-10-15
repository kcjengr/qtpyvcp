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
        typ (str) : The type of the HAL pin, one of `BOOL`, `REAL`, `UINT` or `SINT`.
        dir (str) : the direction of the HAL pin, one of `IN` or `OUT`.

    Properties:
        value (float | int | bool) : The current pin value. For HAL_PORT this is
            the buffered byte count; use the port methods to transfer payloads.
        valueChanged (QSignal) : Signal that is emited when the value changes.
    """

    valueChanged = Signal(object)

    def __init__(self, comp, name, typ, dir, cycle_time=100):
        super(QPin, self).__init__(MAIN_WINDOW)

        self._pin = _hal.component.newpin(comp, name, typ, dir)
        self._is_port = (hasattr(hal, 'HAL_PORT') and typ == hal.HAL_PORT)
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
        if self._is_port:
            raise TypeError("HAL_PORT is a byte queue; use write() instead of setting value")
        self._val = val
        self._pin.set(val)
        self.valueChanged.emit(val)

    def write(self, data):
        """Write bytes/string data to a HAL_PORT pin."""
        if not self._is_port:
            raise TypeError("write() is only available for HAL_PORT pins")
        return self._pin.write(data)

    def read(self, count):
        """Read up to *count* bytes from a HAL_PORT pin."""
        if not self._is_port:
            raise TypeError("read() is only available for HAL_PORT pins")
        return self._pin.read(count)

    def peek(self, count):
        """Read without consuming bytes from a HAL_PORT pin."""
        if not self._is_port:
            raise TypeError("peek() is only available for HAL_PORT pins")
        return self._pin.peek(count)

    def peek_commit(self, count):
        """Consume bytes previously inspected with ``peek``."""
        if not self._is_port:
            raise TypeError("peek_commit() is only available for HAL_PORT pins")
        return self._pin.peek_commit(count)

    def readable(self):
        if not self._is_port:
            raise TypeError("readable() is only available for HAL_PORT pins")
        return self._pin.readable()

    def writable(self):
        if not self._is_port:
            raise TypeError("writable() is only available for HAL_PORT pins")
        return self._pin.writable()

    def clear(self):
        if not self._is_port:
            raise TypeError("clear() is only available for HAL_PORT pins")
        return self._pin.clear()

    def size(self):
        if not self._is_port:
            raise TypeError("size() is only available for HAL_PORT pins")
        return self._pin.size()


class QParam(QObject):
    """QParam
    TODO update desc.
    QParam is a QObject wrapper for a HAL namedparams and emits the valueChanged signal
    when the HAL param value changes.

    Args:
        comp (_hal.component) : The HAL comp the pins should belong to.
        name (str) : The name of the HAL pin to create.
        typ (str) : The type of the HAL pin, one of `BOOL`, `REAL`, `UINT` or `SINT`.
        dir (str) : the direction of the HAL pin, one of `IN` or `OUT`.

    Properties:
        value (float | int | bool) : The the current value of the HAL pin.
        valueChanged (QSignal) : Signal that is emited when the value changes.
    """

    valueChanged = Signal(object)

    def __init__(self, comp, name, pin_type=hal.HAL_BOOL, access_mode=hal.HAL_RW, cycle_time=100):
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
            'bool': hal.HAL_BOOL,
            'bit': hal.HAL_BOOL,
            'real': hal.HAL_REAL,
            'float': hal.HAL_REAL,
            'sint': hal.HAL_SINT,
            's32': hal.HAL_SINT,
            's64': hal.HAL_SINT,
            'signed': hal.HAL_SINT,
            'uint': hal.HAL_UINT,
            'u32': hal.HAL_UINT,
            'u64': hal.HAL_UINT,
            'unsigned': hal.HAL_UINT,
        }
        # HAL_PORT was added in LinuxCNC master and is pin-only.
        if hasattr(hal, 'HAL_PORT'):
            self.type_map['port'] = hal.HAL_PORT

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
        self._closed = False

        self._pins = {}
        self._params = {}

    def addPin(self, name, pin_type, direction):
        type_name = str(pin_type).strip().lower()
        try:
            pin_type = self.type_map[type_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported HAL pin type: {pin_type!r}") from exc
        pin_dir = self.dir_map.get(direction.lower())

        LOG.debug("Adding HAL pin: %s.%s (%s %s)", self.name, name, type, direction)

        pin = QPin(self._comp, name, pin_type, pin_dir)
        self._pins[name] = pin
        return pin

    def addParam(self, name, pin_type, access_mode):
        type_name = str(pin_type).strip().lower()
        if type_name == 'port':
            raise ValueError("HAL_PORT is supported for pins, not parameters")
        try:
            pin_type = self.type_map[type_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported HAL parameter type: {pin_type!r}") from exc
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
        if self._closed or self._comp is None:
            return None

        print(("Unloading '%s' HAL component ..." % self.name))

        try:
            return self._comp.exit(*a, **kw)
        except RuntimeError as err:
            if "closed HAL component" in str(err):
                LOG.debug("HAL component '%s' already closed", self.name)
                return None
            raise
        finally:
            self._closed = True
            self._comp = None

    def signal_handler(self, signal, frame):
        try:
            self.exit()
        except Exception:
            LOG.debug("Ignoring HAL exit error during signal handling", exc_info=True)

    def __getitem__(self, item):
        return self._pins[item]


# testing
def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    def printChange(new_val):
        print(("Value Changed", new_val))

    c = QComponent('test')
    c.addPin('input', "sint", "in")
    c.addPin('float_in', "sint", "in")
    c.getPin('input').valueChanged.connect(printChange)
    c.ready()

    app.exec()


if __name__ == "__main__":
    main()
