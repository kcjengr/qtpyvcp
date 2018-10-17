#!/usr/bin/env python

#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
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

import linuxcnc, time, threading, subprocess, os, json
from qtpy.QtCore import QObject, QTimer, Signal

# Setup logging
try:
    from qtpyvcp.utilities import logger
    log = logger.getLogger(__name__)
    log.setLevel('WARNING')
except Exception as e:
    print e
    import logging as log
    FORMAT = "[%(levelname)s]: %(message)s (%(filename)s:%(lineno)d)"
    log.basicConfig(level=log.DEBUG, format=FORMAT)


#==============================================================================
# Status Monitor
#==============================================================================

class StatusItem(QObject):
    """docstring for StatusItem"""

    valueChanged = Signal('PyQt_PyObject')

    def __init__(self, attr_name, index=None, key=None, stat=None):
        super(StatusItem, self).__init__()
        """StatusItem monitor class

        Args:
            attr_name (str):        the name of the `linuxcnc.status` attribute to monitor
            index (None, optional): the index of the array item to monitor, used with `joint`, `axis` and `tool_table` attributes.
            key (None, optional):   the key of the dict item to monitor, used with `joint`, `axis` and `tool_table` attributes.
        """

        self.attr_name = attr_name
        self.index = index
        self.key = key
        self.stat = stat

        self.value = None
        self.log_change = False
        self.formated_name = self.getFormatedName()

    def __hash__(self):
        return hash((self.attr_name, self.index, self.key))

    def __eq__(self, other):
        return type(self) == type(other) and (self.attr_name, self.index, self.key) == (other.attr_name, other.index, other.key)

    def __ne__(self, other):
        # Needed to avoid having both x==y and x!=y True at the same time!
        return not(self == other)

    def update(self):
        val = getattr(self.stat, self.attr_name)
        if val == self.value:
            return
        if self.index is not None:
            val = val[self.index]
            if self.key is not None:
                val = val[self.key]

        if val != self.value:
            self.value = val

            # emit the signal
            self.valueChanged.emit(self.value)

            if self.log_change:
                log.debug("'{}' valueChanged => {}".format(self.formated_name, self.value))


    def connect(self, slot, log_change=False):
        log.debug("Connecting '{}' valueChanged signal to {}".format(self.formated_name, slot.__name__))
        self.valueChanged.connect(slot)
        self.log_change = log_change

    def disconnect(self, slot=''):
        if slot is not None:
            try:
                self.valueChanged.disconnect(slot)
            except Exception as e:
                log.warning("Failed to disconnect slot: {}".format(slot), exc_info=e)
        elif slot == '':
            # remove all slots from signal it not slot given
            self.valueChanged.disconnect()

    def getValue(self):
        try:
            self.stat.poll() # get fresh data
        except Exception as e:
            log.exception(e)
            return
        val = getattr(self.stat, self.attr_name)
        if self.index is not None:
            val = val[self.index]
            if self.key is not None:
                val = val[self.key]
        return val

    def forceUpdate(self):
        self.value = self.getValue()
        self.valueChanged.emit(self.value)

    def setLogChange(self, log_change):
        self.log_change = log_change

    def getLogChange(self):
        return self.log_change

    def getFormatedName(self):
        index = key = ''
        if self.index is not None:
            index = '[{}]'.format(self.index)
        if self.key is not None:
            key = '[{}]'.format(self.key)
        return "stat.{}{}{}".format(self.attr_name, index, key)


class StatusPoller(QObject):
    """docstring for StatusPoller"""

    stat = linuxcnc.stat()
    timer = QTimer()

    def __init__(self):
        super(StatusPoller, self).__init__()

        self.status_items = {}

        # Start the timer
        self._cycle_time = 75
        self.timer.timeout.connect(self._poll)
        self.timer.start(self._cycle_time)

    def _poll(self):
        # s = time.time()
        try:
            self.stat.poll()
        except Exception as e:
            log.warning("Status polling failed, is LinuxCNC running?", exc_info=e)
            self.timer.stop()
            return
        for status_item in self.status_items.values():
            try:
                status_item.update()
            except Exception as e:
                log.exception(e)
                del self.status_items[hash(status_item)]
        # print time.time() - s

    def getStatAttr(self, name, index=None, key=None, stat_class=StatusItem):
        si = self.status_items.get(hash((name, index, key)))
        if si is None:
            si = stat_class(name, index=index, key=key, stat=self.stat)
            log.debug("Adding new StatusItem for '{}'".format(si.formated_name))
            self.status_items[hash(si)] = si
        return si

class Status(QObject):
    """Ensures only one instance of StatusPoller exists per python interpretor.
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = StatusPoller()
        return cls._instance


#==============================================================================
# HAL Status Monitor
#==============================================================================

class HALPin(QObject):
    """HALPin object, represents a single LinuxCNC HAL pin, enables reading.
        writing and connecting slots to be called when the HAL pin value changes.

    Attributes:
        log_change (bool):      whether to log changes to selfs value
        pin_name (str):         the name of the HAL pin self represents
        settable (bool):        weather the HAL pin is writable
        type (type):            the python type of the HAL pins value
        value (varies):         the value of the HAL pin as of last check
        valueChanged (QtSignal): signal emitted when the HAL pin value changes
    """

    valueChanged = Signal([bool], [float], [int])

    def __init__(self, pin_name, pin_type, pin_direction, pin_value):
        super(HALPin, self).__init__()
        """Initializes a new HALPin object

        Args:
            pin_name (str):      the HAL pin name
            pin_type (str):      the HAL type for the pin, float, u32, s32 or bit
            pin_direction (str): the pin direction, IN, OUT, or I/O
            pin_value (str):     the initial value of the HAL pin
        """

        self.pin_name = pin_name
        type_map = {'float': float, 's32': int, 'u32': int, 'bit': bool}
        self.type = type_map.get(pin_type)
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


class HALPoller(QObject):
    """docstring for StatusPoller"""
    def __init__(self):
        super(HALPoller, self).__init__()

        self.cycle_time = 50
        self.linuxcnc_is_alive = False

        self.status_items = {}
        self.pin_dict = {}
        self.sig_dict = {}

        # Create a thread for checking the HAL pins and sigs
        self.hal_mutex = threading.Lock()
        self.hal_thread = threading.Thread(target=self.hal_poll_thread)
        self.hal_thread.daemon = True
        self.hal_thread.start()


    # halcmd can take 200ms or more to run, so run poll updates in a thread so as not to slow the server
    # requests for hal pins and sigs will read the results from the most recent update
    def hal_poll_thread(self):

        while True:
            # s = time.time()

            # first, check if linuxcnc is running at all
            if not os.path.isfile( '/tmp/linuxcnc.lock' ):
                self.hal_mutex.acquire()
                try:
                    if self.linuxcnc_is_alive:
                        log.debug("LinuxCNC has stopped.")
                    self.linuxcnc_is_alive = False
                    self.pin_dict = {}
                    self.sig_dict = {}
                finally:
                    self.hal_mutex.release()
                time.sleep(self.cycle_time/1000.0)
                continue
            else:
                if not self.linuxcnc_is_alive:
                    log.debug("LinuxCNC has started.")
                self.linuxcnc_is_alive = True

            self.p = subprocess.Popen( ['halcmd', '-s', 'show', 'pin'] , stderr=subprocess.PIPE, stdout=subprocess.PIPE )
            rawtuple = self.p.communicate()
            if len(rawtuple[0]) <= 0:
                time.sleep(self.cycle_time/1000.0)
                continue
            raw = rawtuple[0].split('\n')

            pins = [ filter( lambda a: a != '', [x.strip() for x in line.split(' ')] ) for line in raw ]

            # UPDATE THE DICTIONARY OF PIN INFO
            # Acquire the mutex so we don't step on other threads
            self.hal_mutex.acquire()
            try:
                pin_dict = {}
                sig_dict = {}

                for p in pins:
                    if len(p) > 5:
                        # if there is a signal listed on this pin, make sure
                        # that signal is in our signal dictionary
                        sig_dict[ p[6] ] = p[3]
                    if len(p) >= 5:
                        pin_dict[ p[4] ] = p[3]
            finally:
                self.hal_mutex.release()

            changed_items = set(pin_dict.items()) - set(self.pin_dict.items())
            # for item in changed_items:
            #     print 'HAL pin Changed: {} => {}'.format(item[0], item[1])

            self.pin_dict = pin_dict
            self.sig_dict = sig_dict

            for changed_item in changed_items:
                if changed_item[0] in self.status_items:
                    self.status_items[changed_item[0]].update(changed_item[1])

            # print time.time() - s
            # print json.dumps(pin_dict, indent=4, sort_keys=True)

            # before starting the next check, sleep a little so we don't use all the CPU
            time.sleep(self.cycle_time/1000.0)

    def getHALPin(self, pin_name):
        si = self.status_items.get(pin_name)
        if si is None:
            raw = subprocess.check_output(['halcmd', '-s', 'show', 'pin', pin_name]).strip()
            if len(raw.split('\n')) > 1: # more than one pin name matches
                raise ValueError("HAL pin red<{}> does not exist".format(pin_name))
            pin_data = raw.split()
            if len(pin_data) == 0: # no pin names match
                raise ValueError("HAL pin red<{}> does not exist".format(pin_name))
                return
            if pin_name != pin_data[4]: # name is not complete, but only one pin could match
                raise ValueError("HAL pin red<{}> does not exist, did you mean green<{}>?".format(pin_name, pin_data[4]))
            pin_type = pin_data[1].strip()
            pin_direction = pin_data[2].strip()
            pin_value = pin_data[3].strip()
            log.debug("Adding new HALStatusItem for pin '{}'".format(pin_name))
            si = HALPin(pin_name, pin_type, pin_direction, pin_value)
            self.status_items[pin_name] = si
        return si

class HALStatus(QObject):
    """Ensures only one instance of StatusPoller exists per python interpretor.
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = HALPoller()
        return cls._instance


#==============================================================================
# Demo and code for standalone testing
#==============================================================================

if __name__ == '__main__':
    import sys
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QCheckBox, QTextEdit, QApplication, QMainWindow, QVBoxLayout, QGridLayout

    app = QApplication(sys.argv)

    win = QWidget()
    win.resize(300, 100)
    win.setWindowTitle("Status Demo")

    #==========================================================================
    # Status example usage
    #==========================================================================

    # Status label and DRO
    stat_pos_label = QLabel("stat.position[0] =")
    stat_pos_dro = QLabel("0.1234")

    # Initialize the status object
    stat = Status()

    # retrieve/initialize StatAttr objects
    #   `stat.position` is a tuple with 9 values for each axis, setting
    #   the index=0 specifies that we want the position value of the x-axis
    stat_pos_attr = stat.getStatAttr('position', index=0)

    # set the StatAttr object to log changes to its value, used for debuging
    stat_pos_attr.setLogChange(True)

    # connect the pos valueChanged signal to update the label
    stat_pos_attr.valueChanged.connect((lambda v: stat_pos_dro.setNum(v)))

    #==========================================================================
    # HAL Status example usage
    #==========================================================================

    # HAL Label and DRO
    hal_pos_label = QLabel("joint.0.pos-cmd =")
    hal_pos_dro = QLabel("0.12345")

    # Initialize the HALStatus object
    hal_stat = HALStatus()

    # retrieve/initialize HALPin objects
    hal_pos_pin = hal_stat.getHALPin('joint.0.pos-cmd')
    hal_pos_pin.setLogChange(True)
    hal_pos_pin.connect((lambda v: hal_pos_dro.setNum(v)))

    #==========================================================================
    # HAL setting and reading values Status example usage
    #==========================================================================

    # retrieve/initialize HALPin objects
    flood_on_pin = hal_stat.getHALPin('halui.flood.on')
    flood_off_pin = hal_stat.getHALPin('halui.flood.off')
    flood_is_on_pin = hal_stat.getHALPin('halui.flood.is-on')

    # method to set flood ON/OFF
    def setFloodOn(state):
        flood_on_pin.setValue(state)
        flood_off_pin.setValue(not state)

    # check button for turning flood ON/OFF
    flood_toggle = QCheckBox("Flood ON")
    flood_toggle.setChecked(flood_is_on_pin.getValue())

    # keep checkbox in sync with HALs value, e.g. if flood was turned on from a UI
    flood_is_on_pin.connect((lambda v: flood_toggle.setChecked(v)))

    # connect button toggled signal to our method
    flood_toggle.toggled.connect(setFloodOn)

    # set HALPin object to log changes to its value
    flood_is_on_pin.setLogChange(True)

    # initialize out flood state label with the current state
    flood_state_label = QLabel(str(flood_is_on_pin.getValue()))

    # connect the `halui.flood.is-on` state changes signal to our label
    flood_is_on_pin.connect((lambda v: flood_state_label.setText(str(v))))


    # setup the window
    mainLayout = QGridLayout()
    win.setLayout(mainLayout)

    # status stuff
    mainLayout.addWidget(stat_pos_label, 0, 0, Qt.AlignRight)
    mainLayout.addWidget(stat_pos_dro, 0, 1)

    # HAL stuff
    mainLayout.addWidget(hal_pos_label, 1, 0, Qt.AlignRight)
    mainLayout.addWidget(hal_pos_dro, 1, 1)

    mainLayout.addWidget(flood_toggle, 2, 0, Qt.AlignRight)
    mainLayout.addWidget(flood_state_label, 2, 1)

    win.show()
    sys.exit(app.exec_())
