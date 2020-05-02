"""Storage Device Manager Plugin"""

import os

import psutil

from collections import defaultdict

from pyudev.pyqt5 import MonitorObserver
from pyudev import Context, Monitor, Devices

from qtpy.QtCore import Signal

from qtpyvcp import SETTINGS, CONFIG
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

LOG = getLogger(__name__)


def dictDiff(d1, d2):
    return set(d2.keys()) - set(d1.keys())


class StorageDeviceManger(DataPlugin):

    # removable_devices = DataChannel(dict)
    # removableDeviceAdded = DataChannel()
    # removableDeviceRemoved = DataChannel()

    def __init__(self, **kwargs):
        super(StorageDeviceManger, self).__init__()

        self._device_list = dict()

        self.context = None
        self.monitor = None
        self.observer = None

    @DataChannel
    def removable_devices(self, chan):
        return chan.value or {}

    def _onDeviceEvent(self, device):

        if device.action == "add":
            if device['DEVTYPE'] == 'partition':
                print "Adding device: ", device.device_node
                # mount new partition
                os.system("udisksctl mount --block-device {}".format(device.device_node))
                self.updateRemovableDevices()

        elif device.action == "remove":
            if device['DEVTYPE'] == 'partition':
                print "Removing device: ", device.device_node
                self.updateRemovableDevices()

    def updateRemovableDevices(self):

        disks = [disk for disk in
                   self.context.list_devices(subsystem='block', DEVTYPE='disk') if
                   disk.attributes.asstring('removable') == "1"]

        removable_devices = dict()
        for disk in disks:
            partitions = [partition.device_node for partition in
                          self.context.list_devices(subsystem='block',
                                                    DEVTYPE='partition',
                                                    parent=disk)]

            for partition in psutil.disk_partitions():
                if partition.device in partitions and not partition.mountpoint == '/':
                    info = {'path': partition.mountpoint,
                            'disk': disk.device_node,
                            'device': partition.device,
                            'label': os.path.basename(partition.mountpoint),
                            'removable': True}

                    removable_devices[partition.device] = info

        self.removable_devices.setValue(removable_devices)

    def ejectDevice(self, device):

        device_info = self.removable_devices.value.get(device, {})
        if device_info.get('removable', False):
            device = device_info['device']
            os.system("udisksctl unmount --block-device {}".format(device))
            os.system("udisksctl power-off --block-device {}".format(device))

    def initialise(self):
        print "Initializing Removable Storage Device Manager..."

        self.context = Context()

        self.monitor = Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')

        self.observer = MonitorObserver(self.monitor)
        self.observer.deviceEvent.connect(self._onDeviceEvent)
        self.monitor.start()

        self.updateRemovableDevices()

        # print self.removable_devices

    def terminate(self):
        pass
