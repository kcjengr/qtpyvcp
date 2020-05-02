"""Storage Device Manager Plugin"""

import os

import psutil

from pyudev.pyqt5 import MonitorObserver
from pyudev import Context, Monitor, Device

from qtpyvcp import SETTINGS, CONFIG
from qtpyvcp.widgets.dialogs import askQuestion
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

from qtpyvcp.actions.program_actions import clear as loadEmptyProgram

LOG = getLogger(__name__)


def dictDiff(d1, d2):
    return set(d2.keys()) - set(d1.keys())


class StorageDeviceManger(DataPlugin):
    def __init__(self, **kwargs):
        super(StorageDeviceManger, self).__init__()

        self._device_list = dict()

        self.context = None
        self.monitor = None
        self.observer = None

        self.status = getPlugin('status')

    @DataChannel
    def removable_devices(self, chan):
        return chan.value or {}

    def _onDeviceEvent(self, device):

        if device.action == "add":
            if device['DEVTYPE'] == 'partition':
                LOG.debug("Adding device: s%", device.device_node)
                # mount new partition
                os.system("udisksctl mount --block-device {}".format(device.device_node))
                self.updateRemovableDevices()

        elif device.action == "remove":
            if device['DEVTYPE'] == 'partition':
                LOG.debug("Removing device: %s", device.device_node)
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
            device_path = device_info.get('path', '')
            loaded_program = self.status.stat.file
            if loaded_program and loaded_program.startswith(device_path):
                title = "WARNING: Device in use!"
                msg = "The currently loaded G-Code file is located on the device " \
                      "you are tyring to eject. If you continue the file will be " \
                      "unloaded before trying to eject the device.\n\n" \
                      "Do you want to continue?"

                if not askQuestion(title, msg):
                    return

                loadEmptyProgram()

            device = device_info['device']
            os.system("udisksctl unmount --block-device {}".format(device))
            os.system("udisksctl power-off --block-device {}".format(device))

    def initialise(self):
        self.context = Context()

        self.monitor = Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')

        self.observer = MonitorObserver(self.monitor)
        self.observer.deviceEvent.connect(self._onDeviceEvent)
        self.monitor.start()

        self.updateRemovableDevices()

    def terminate(self):
        pass
