#   Copyright (c) 2018 Kurt Jacobson
#         <kcjengr@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time, threading, subprocess, os
from qtpy.QtCore import QObject, Signal

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin

LOG = getLogger(__name__)

HAL_TYPE_MAP = {
    'float': float,
    'bit': bool,
    's32': int,
    'u32': int
}


def toPythonTypedValue(hal_type, value):
    return HAL_TYPE_MAP[hal_type](value)


def getHalStatus():
    output = subprocess.check_output(['halcmd', '-s', 'show', 'pin']).strip()
    pins = [pin.split() for pin in output.split('\n')]
    pin_dict = {p[4]: HAL_TYPE_MAP[p[1]](p[3]) for p in pins}
    return pin_dict


class HalPin(QObject):
    """HalPin object, represents a single LinuxCNC HAL pin, enables reading.
        writing and connecting slots to be called when the HAL pin value changes.

    Attributes:
        log_change (bool):      whether to LOG changes to selfs value
        pin_name (str):         the name of the HAL pin self represents
        settable (bool):        weather the HAL pin is writable
        type (type):            the python type of the HAL pins value
        value (varies):         the value of the HAL pin as of last check
        valueChanged (QtSignal): signal emitted when the HAL pin value changes
    """

    valueChanged = Signal([bool], [float], [int])

    def __init__(self, pin_name, pin_type, pin_direction, pin_value):
        """Initializes a new HalPin object

        Args:
            pin_name (str):      the HAL pin name
            pin_type (str):      the HAL type for the pin, float, u32, s32 or bit
            pin_direction (str): the pin direction, IN, OUT, or I/O
            pin_value (str):     the initial value of the HAL pin
        """
        super(HalPin, self).__init__()

        self.pin_name = pin_name
        self.type = HAL_TYPE_MAP.get(pin_type)
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
            LOG.debug("HAL value changed: {} => {}".format(self.pin_name, self.value))
        self.valueChanged[self.type].emit(self.value)

    def connect(self, slot, log_change=False):
        LOG.debug("Connecting '{}' valueChanged signal to {}".format(self.pin_name, slot))
        self.valueChanged[self.type].connect(slot)
        self.log_change = log_change

    notify = connect

    def disconnect(self, slot=''):
        if slot is not None:
            try:
                self.valueChanged[self.type].disconnect(slot)
            except Exception as e:
                LOG.warning("Failed to disconnect slot: {}".format(slot), exc_info=e)
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


class HalStatus(DataPlugin):
    """docstring for StatusPoller"""
    def __init__(self):
        super(HalStatus, self).__init__()

        self.cycle_time = 100
        self.linuxcnc_is_alive = False

        self.status_items = {}
        self.pin_dict = {}

        # Create a thread for checking the HAL pins and signals
        self.hal_mutex = threading.Lock()
        self.hal_thread = threading.Thread(target=self.hal_poll_thread)
        self.hal_thread.daemon = True
        self.hal_thread.start()

        # self.channels = {p: self.getHALPin(p) for p in getHalStatus()}
        self.channels = {pin: None for pin in self.pin_dict}

    def getChannel(self, url):
        """Get data channel from URL.

        halpin:halui.machine.is-on

        Args:
            url (str) : The URL of the channel to get.

        Returns:
            tuple : (chan_obj, chan_exp)
        """

        chan, sep, query = url.partition('?')
        raw_args = query.split('&')

        # print url, chan, raw_args

        pin = self.getHALPin(url)

        return pin, pin.getValue

    # halcmd can take 200ms or more to run, so run poll updates in a thread
    def hal_poll_thread(self):

        while True:
            # s = time.time()

            # first, check if linuxcnc is running at all
            if not os.path.isfile( '/tmp/linuxcnc.lock' ):
                self.hal_mutex.acquire()
                try:
                    if self.linuxcnc_is_alive:
                        LOG.debug("LinuxCNC has stopped.")
                    self.linuxcnc_is_alive = False
                    self.pin_dict = {}
                finally:
                    self.hal_mutex.release()
                time.sleep(self.cycle_time/1000.0)
                continue
            else:
                if not self.linuxcnc_is_alive:
                    LOG.debug("LinuxCNC has started.")
                self.linuxcnc_is_alive = True

            try:
                # UPDATE THE DICTIONARY OF PIN INFO
                # Acquire the mutex so we don't step on other threads
                self.hal_mutex.acquire()

                pin_dict = getHalStatus()
                if len(pin_dict) == 0:
                    time.sleep(self.cycle_time/1000.0)
                    continue

            finally:
                self.hal_mutex.release()

            changed_items = set(pin_dict.items()) - set(self.pin_dict.items())
            # for item in changed_items:
            #     print 'HAL pin Changed: {} => {}'.format(item[0], item[1])

            self.pin_dict = pin_dict

            for changed_item in changed_items:
                if changed_item[0] in self.status_items:
                    self.status_items[changed_item[0]].update(changed_item[1])

            # print time.time() - s
            # print json.dumps(pin_dict, indent=4, sort_keys=True)

            # before starting the next check, sleep a little so we don't use all the CPU
            time.sleep(self.cycle_time/1000.0)

    def getHALPin(self, pin_name):
        si = self.status_items.get(pin_name)
        pin_name = 'halui.machine.is-on'
        print subprocess.check_output(['halcmd', '-s', 'show', 'pin'])
        if si is None:
            print pin_name
            raw = subprocess.check_output(['halcmd', '-s', 'show', 'pin', pin_name]).strip()
            print raw
            # if len(raw.split('\n')) > 1:  # more than one pin name matches
            #     raise ValueError("HAL pin name %s is not unique" % pin_name)
            pin_data = raw.split()
            print pin_data
            if len(pin_data) == 0: # no pin names match
                raise ValueError("HAL pin %s does not exist" % pin_name)
            if pin_name != pin_data[4]: # name is not complete, but only one pin could match
                raise ValueError("HAL pin %s does not exist, did you mean %s?"
                                 % (pin_name, pin_data[4]))
            pin_type = pin_data[1].strip()
            pin_direction = pin_data[2].strip()
            pin_value = pin_data[3].strip()
            LOG.debug("Adding new HALStatusItem for pin '{}'".format(pin_name))
            si = HalPin(pin_name, pin_type, pin_direction, pin_value)
            self.status_items[pin_name] = si
        return si
