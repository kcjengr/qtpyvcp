# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer

from console import PythonConsole


class Wrapper(PythonConsole):
    def __init__(self, parent=None):
        super(Wrapper, self).__init__(parent)

        self.pyconsole_input_timer = QTimer()
        self.pyconsole_input_timer.timeout.connect(self.repl_nonblock)
        self.pyconsole_input_timer.start(0)

        self.show()
