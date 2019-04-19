
import hal
import subprocess

from qtpy.QtCore import QObject, Signal

class QPin(QObject):
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

    def __init__(self, *args, **kwargs):
        pass

    def __init__(self, pin_name, pin_type, pin_direction, pin_value):
        super(QPin, self).__init__()
        """Initializes a new QPin object

        Args:
            pin_name (str):      the HAL pin name
            pin_type (str):      the HAL type for the pin, float, u32, s32 or bit
            pin_direction (str): the pin direction, IN, OUT, or I/O
            pin_value (str):     the initial value of the HAL pin
        """

        self.pin_name = pin_name
        type_map = {'float': float, 's32': int, 'u32': int, 'bit': bool}
        self.type = type_map.get(pin_type.lower())
        self.settable = pin_direction in ['IN', 'I/O']
        self.value = self.type(pin_value)

        self.log_change = False

    def __hash__(self):
        return hash(self.pin_name)

    def __eq__(self, other):
        return type(self) == type(other) and hash(self.pin_name) == hash(other.pin_name)

    def __ne__(self, other):
        # Needed to avoid having both x==y and x!=y True at the same time!
        return not(self == other)

    def update(self, value):
        self.value = self.convertType(value)
        if self.log_change:
            log.debug("HAL value changed: {} => {}".format(self.pin_name, self.value))
        self.valueChanged[self.type].emit(self.value)

    def connect(self, slot, log_change=False):
        log.debug("Connecting '{}' valueChanged signal to {}".format(self.pin_name, slot))
        self.valueChanged[self.type].connect(slot)
        self.log_change = log_change

    def disconnect(self, slot=''):
        if slot is not None:
            try:
                self.valueChanged[self.type].disconnect(slot)
            except Exception as e:
                log.warning("Failed to disconnect slot: {}".format(slot), exc_info=e)
        elif slot == '':
            # remove all slots from signal it not slot given
            self.valueChanged[self.type].disconnect()

    def getValue(self):
        data = subprocess.check_output(['halcmd', '-s', 'show', 'pin', self.pin_name]).split()
        return self.convertType(data[3])

    def setValue(self, value):
        if self.settable:
            return subprocess.call(['halcmd', 'setp', self.pin_name, str(value)])
        raise TypeError("setValue failed, HAL pin '{}' is read only".format(self.pin_name))

    def getSettable(self):
        return self.settable

    def forceUpdate(self):
        self.value = self.getValue()
        self.valueChanged[self.type].emit(self.value)

    def setLogChange(self, log_change):
        self.log_change = log_change

    def getLogChange(self):
        return self.log_change

    def convertType(self, value):
        if self.type == bool:
            return value.lower() in ['true', '1']
        return self.type(value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if x < 0:
            self._value = 0
        elif x > 1000:
            self._value = 1000
        else:
            self._value = value

def setPin(pin_name, value):
    pass

def getPin(pin_name):
    pass

def newPin(pin_name, hal_type, direction):
    pass

def getSignal(pin_name):
    raw = subprocess.check_output(['halcmd', '-s', 'show', 'pin', pin_name]).split('\n')[0].split()
    # return sig name or None


def main():
    print QPin('test.in', 'BIT', 'IN', 'BOOL')


if __name__ == '__main__':
    main()
