"""
DateTime
--------

This plugin provides the Date and Time

This plugin is not loaded by default, so to use it you will first
need to add it to your VCPs YAML config file.

YAML configuration:

.. code-block:: yaml

    data_plugins:
      clock:
        provider: qtpyvcp.plugins.clock:Clock

"""

from datetime import datetime

from qtpy.QtCore import QTimer
from qtpyvcp.plugins import DataPlugin, DataChannel


class Clock(DataPlugin):
    """Clock Plugin"""
    def __init__(self):
        super(Clock, self).__init__()

        # set initial values
        self.time.setValue(datetime.now())
        self.date.setValue(datetime.now())

        # make the clock tick
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

    @DataChannel
    def time(self, chan):
        """The current time, updated every second.

        Args:
            format (str) : Format spec. Defaults to ``%I:%M:%S %p``.
                See http://strftime.org for supported formats.

        Returns:
            The current time as a formatted string. Default HH:MM:SS AM

        Channel syntax::

            clock:time
            clock:time?string
            clock:time?string&format=%S

        """
        return chan.value

    @time.tostring
    def time(self, chan, format="%I:%M:%S %p"):
        return chan.value.strftime(format)

    @DataChannel
    def date(self, chan):
        """The current date, updated every second.

        Args:
            format (str) : Format spec. Defaults to ``%m/%d/%Y``.
                See http://strftime.org for supported formats.

        Returns:
            The current date as a formatted string. Default MM/DD/YYYY

        Channel syntax::

            clock:date
            clock:date?string
            clock:date?string&format=%Y

        """
        return chan.value

    @date.tostring
    def date(self, chan, format="%m/%d/%Y"):
        return chan.value.strftime(format)

    def initialise(self):
        self.timer.start(1000)

    def tick(self):
        self.time.setValue(datetime.now())
        self.date.setValue(datetime.now())


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])

    c = Clock()
    c.initialise()

    def onTimeChanged(val):
        print c.time
        print c.date

    c.time.notify(onTimeChanged)

    app.exec_()
