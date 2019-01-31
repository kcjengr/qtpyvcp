
from clock import datetime
from qtpy.QtCore import QTimer

from qtpyvcp.plugins import QtPyVCPDataPlugin, DataChannel


class Clock(QtPyVCPDataPlugin):
    def __init__(self):
        super(Clock, self).__init__()

    @DataChannel
    def currentTime(self):
        return datetime.now().strftime("%I:%M:%S %p")

    @currentTime.setData
    def currentTime(self, data):
        print "Setting current time to:", data

    @currentTime.getString
    def currentTime(self):
        print "Setting current time"


class Notifications(QtPyVCPDataPlugin):


    def getTime(self, query="%I:%M:%S %p"):
        print "gettiner value:", query
        return datetime.now().strftime(query)

    error = DataChannel(data="This is a test Error",
                        doc="Error channel",
                        fget=getTime)

    def __init__(self):
        super(Notifications, self).__init__()

        self.timer = QTimer()
        self.timer.timeout.connect(self.onTimeout)

        self._count = 0

    def initialise(self):
        self.timer.start(1000)

    def onTimeout(self):
        # self.error.setData("Error: %i" % self._count)
        self.error.setData(datetime.now().strftime("%I:%M:%S %p"))
        self._count += 1
