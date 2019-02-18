"""
DateTime
--------

DataPlugin that provides the current date and time.
"""

from datetime import datetime

from qtpy.QtCore import QTimer
from qtpyvcp.plugins import DataPlugin, DataChannel


class Clock(DataPlugin):
    """Clock Plugin"""
    def __init__(self):
        super(Clock, self).__init__()

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

    @DataChannel
    def time(self, chan):
        """The current date/time, updated every second.

        Args:
            format (str) : Format spec. Defaults to "%I:%M:%S %p".
                See http://strftime.org for supported formats.

        Returns:
            The current date time as a formatted string. Default HH:MM:SS AM

        Example:

            ``datetime:time?format=%S``
        """
        return datetime.now()

    @time.tostring
    def time(self, chan, format="%I:%M:%S %p"):
        return datetime.now().strftime(format)

    @DataChannel
    def date(self, chan, format="%x"):
        return datetime.now().strftime(format)

    def initialise(self):
        self.timer.start(1000)

    def tick(self):
        self.time.signal.emit(datetime.now())


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])

    c = Clock()
    c.initialise()

    def onTimeChanged(val):
        print c.time
        print c.time.getValue()
        print c.time.getString(format='%S')
        # c.time.setValue(datetime.now())

    c.time.notify(onTimeChanged)

    app.exec_()
