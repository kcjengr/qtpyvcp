from datetime import datetime

from qtpy.QtCore import QTimer
from qtpyvcp.plugins import DataPlugin, DataChannel


class Clock(DataPlugin):
    def __init__(self):
        super(Clock, self).__init__()

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

    @DataChannel
    def current_time(chan):
        """The current date/time, updated every second.

        Args:
            format (str) : Format spec. Defaults to "%I:%M:%S %p".
                See http://strftime.org for supported formats.

        Returns:
            The current date time as a formatted string. Default HH:MM:SS AM

        Example:

            ``clock:current_time?string&format=%S``
        """
        return datetime.now()

    @current_time.tostring
    def current_time(chan, format="%I:%M:%S %p"):
        return datetime.now().strftime(format)

    def initialise(self):
        self.timer.start(1000)

    def tick(self):
        self.current_time._signal.emit(datetime.now())


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])

    c = Clock()
    c.initialise()

    def onTimeChanged():
        print c.current_time

    c.current_time.notify(onTimeChanged)

    app.exec_()
