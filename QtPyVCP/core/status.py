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
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot

# Setup logging
try:
    from QtPyVCP.core import logger
    log = logger.get(__name__)
    log.setLevel('WARNING')
except:
    import logging as log
    FORMAT = "[%(levelname)s]: %(message)s (%(filename)s:%(lineno)d)"
    log.basicConfig(level=log.DEBUG, format=FORMAT)


#==============================================================================
# Status Monitor
#==============================================================================

class StatusAttr(QObject):
    """docstring for StatusAttr"""

    valueChanged = pyqtSignal('PyQt_PyObject')

    def __init__(self, attr_name, index=None, key=None, stat=None):
        super(StatusAttr, self).__init__()
        """StatusAttr monitor class

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

    def update(self, status):
        val = getattr(status, self.attr_name)
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
        log.debug("Connecting '{}' valueChanged signal to {}".format(self.formated_name, slot))
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
                status_item.update(self.stat)
            except Exception as e:
                log.exception(e)
                del self.status_items[status_item]
        # print time.time() - s

    def getStatAttr(self, attribute, index=None, key=None):
        si = self.status_items.get(hash((attribute, index, key)))
        if si is None:
            si = StatusAttr(attribute, index=index, key=key, stat=self.stat)
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

    valueChanged = pyqtSignal('PyQt_PyObject')

    """docstring for HALPin"""
    def __init__(self, pin_name):
        super(HALPin, self).__init__()
        """HALPin monitor class

        Args:
            name (str):                     the name of the HAL pin to monitor
        """
        self.pin_name = pin_name

        pin_data = subprocess.check_output(['halcmd', '-s', 'show', 'pin', self.pin_name]).split()
        hal_type_map = {'float': float, 's32': int, 'u32': int, 'bit': self.toBool}
        self.type = hal_type_map.get(pin_data[1].strip())

        self.log_change = False
        self.value = self.type(pin_data[3])

    def __hash__(self):
        return hash(self.pin_name)

    def __eq__(self, other):
        return type(self) == type(other) and hash(self.pin_name) == hash(other.pin_name)

    def __ne__(self, other):
        # Needed to avoid having both x==y and x!=y True at the same time!
        return not(self == other)

    def update(self, value):
        self.value = self.type(value)
        if self.log_change:
            log.debug("HAL value changed: {} => {}".format(self.pin_name, self.value))
        self.valueChanged.emit(self.value)

    def connect(self, slot, log_change=False):
        log.debug("Connecting '{}' valueChanged signal to {}".format(self.pin_name, slot))
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
        data = subprocess.check_output(['halcmd', '-s', 'show', 'pin', self.pin_name]).split()
        return self.type(data[3])

    def forceUpdate(self):
        self.value = self.getValue()
        self.valueChanged.emit(self.value)

    def setLogChange(self, log_change):
        self.log_change = log_change

    def getLogChange(self):
        return self.log_change

    def toBool(self, value):
        if value.lower() in ['true', '1']:
            return True
        return False

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
            s = time.time()

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
            log.debug("Adding new HALStatusItem for pin '{}'".format(pin_name))
            si = HALPin(pin_name)
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
# For standalone testing
#==============================================================================

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QVBoxLayout

    app = QApplication(sys.argv)
    dro = QLabel()
    dro.resize(250,50)
    dro.setMargin(30)

    stat = Status()
    stat.getStatAttr('position', index=0).valueChanged.connect((lambda v: dro.setNum(v)))
    stat.getStatAttr('position', index=0).setLogChange(True)

    # hal_stat = HALStatus()
    # hal_stat.getHALPin('joint.0.pos-cmd').connect((lambda v: dro.setNum(v)))
    # hal_stat.getHALPin('joint.0.pos-cmd').setLogChange(True)

    dro.show()

    sys.exit(app.exec_())
