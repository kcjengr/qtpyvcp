"""
Main Application Module

Contains the VCPApplication class with core function and VCP loading logic.
"""
import os
import sys

from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, qApp

class VCPApplication(QApplication):

    def __init__(self, vcp=None, ini=None, perfmon=False, stylesheet=None,
                command_line_args=[], window_kwargs={},):
        super(VCPApplication, self).__init__(command_line_args)

        qApp = QApplication.instance()

        from QtPyVCP.core import Status, Action, Prefs, Info
        from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

        self.status = Status()
        self.action = Action()
        self.prefs = Prefs()
        self.info = Info()

        print vcp, command_line_args

        ui_file = None
        if vcp is not None and os.path.exists(vcp):
            vcp_path = os.path.realpath(vcp)
            if os.path.isfile(vcp_path):
                directory, filename = os.path.split(vcp_path)
                name, ext = os.path.splitext(filename)
                if ext == '.ui':
                    print "is a UI file"
                    window = VCPMainWindow(ui_file=vcp_path)
                    window.show()
                    self.window = window
                elif ext == '.py':
                    print "is a python file"
            elif os.path.isdir(vcp_path):
                print "VCP is a directory"

        # Performance monitoring
        if perfmon:
            import psutil
            self.perf = psutil.Process()
            self.perf_timer = QTimer()
            self.perf_timer.setInterval(2000)
            self.perf_timer.timeout.connect(self.logPerformance)
            self.perf_timer.start()


    @pyqtSlot()
    def logPerformance(self):
        """
        Logs total CPU usage (in percent), as well as per-thread usage.
        """
        with self.perf.oneshot():
            total_percent = self.perf.cpu_percent(interval=None)
            total_time = sum(self.perf.cpu_times())
            usage = [total_percent * ((t.system_time + t.user_time) / total_time) for t in self.perf.threads()]
        print("Total: {tot}, Per Thread: {percpu}".format(tot=total_percent, percpu=usage))
