"""
Main QtPyVCP Application Module

Contains the VCPApplication class with core function and VCP loading logic.
"""
import os
import sys
import imp
import inspect

from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory, qApp

# initialize logging. If a base logger was already initialized in a startup
# script (e.g. vcp_launcher.py), then that logger will be returned, otherwise
# this will initialise a base logger with default log level of DEBUG
from QtPyVCP.utilities import logger
LOG = logger.initBaseLogger('QtPyVCP')

from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

class VCPApplication(QApplication):

    def __init__(self, vcp=None, ini=None, perfmon=False, stylesheet=None,
                theme=None, command_line_args=[], window_kwargs={},):
        super(VCPApplication, self).__init__(command_line_args)

        qApp = QApplication.instance()

        from QtPyVCP.core import Status, Action, Prefs, Info
        from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

        self.info = Info()
        self.prefs = Prefs()
        self.status = Status()
        self.action = Action()

        if theme is not None:
            self.setStyle(QStyleFactory.create(theme))

        if stylesheet is not None and os.path.exists(stylesheet):
            LOG.info("Using QSS stylesheet file: yellow<{}>".format(qss_file))
            with open(qss_file, 'r') as fh:
                self.setStyleSheet(fh.read())

        print vcp, command_line_args
        if vcp is not None:
            self.loadVCP(vcp, args=[], kwargs=window_kwargs)

        # Performance monitoring
        if perfmon:
            import psutil
            self.perf = psutil.Process()
            self.perf_timer = QTimer()
            self.perf_timer.setInterval(2000)
            self.perf_timer.timeout.connect(self.logPerformance)
            self.perf_timer.start()

        self.aboutToQuit.connect(self.status.onShutdown)

    def loadVCP(self, vcp, args=[], kwargs={}):
        """
        Load a VCP defined by a Qt .ui file, a Python .py file, or from
        a VCP python package.

        Parameters
        ----------
        vcp : str
            The path to a VCP to load.
        args : list, optional
            A list of arguments to pass to the VCP.
        kwargs : dict, optional
            A dict of keyword arguments to pass to the VCP.

        Returns
        -------
        QtPyVCP.VCPMainWindow instance
        """
        ui_file = None
        if not os.path.exists(vcp):
            LOG.critical("Specified VCP does not exist: yellow<{}>".format(vcp))
            sys.exit()
        vcp_path = os.path.realpath(vcp)
        if os.path.isfile(vcp_path):
            directory, filename = os.path.split(vcp_path)
            name, ext = os.path.splitext(filename)
            if ext == '.ui':
                LOG.info("Loading VCP from UI file: yellow<{}>".format(vcp))
                window = VCPMainWindow(ui_file=vcp_path)
                window.show()
                self.window = window
            elif ext == '.py':
                LOG.info("Loading VCP from PY file: yellow<{}>".format(vcp))
                window = self.loadPyFile(vcp_path, args, kwargs)
                window.show()
                self.window = window
        elif os.path.isdir(vcp_path):
            LOG.info("VCP is a directory")

    def loadPyFile(self, pyfile, args, kwargs):
        """
        Load a .py file, performs some sanity checks to try and determine
        if the file actually contains a valid VCPMainWindow subclass, and if
        the checks pass, create and return an instance.

        This is an internal method, users will usually want to use `loadVCP` instead.

        Parameters
        ----------
        pyfile : str
            The path to a .py file to load.
        args : list
            A list of arguments to pass to the
            loaded VCPMainWindow subclass.
        kwargs : dict
            A dict of keyword arguments to pass to the
            loaded VCPMainWindow subclass.

        Returns
        -------
        QtPyVCP.VCPMainWindow instance
        """
        # Add the pyfile module directory to the python path, so that submodules can be loaded
        module_dir = os.path.dirname(os.path.abspath(pyfile))
        sys.path.append(module_dir)

        # Load the module. It's attributes can be accessed via `python_vcp.attr`
        module = imp.load_source('python_vcp', pyfile)

        classes = [obj for name, obj in inspect.getmembers(module) \
                if inspect.isclass(obj) \
                and issubclass(obj, VCPMainWindow) \
                and obj != VCPMainWindow]
        if len(classes) == 0:
            raise ValueError("Invalid File Format." \
            " {} has no class inheriting from VCPMainWindow.".format(pyfile))
        if len(classes) > 1:
            LOG.warn("More than one VCPMainWindow class in file yellow<{}>." \
            " The first occurrence (in alphabetical order) will be used: {}" \
            .format(pyfile, classes[0].__name__))
        cls = classes[0]

        return cls(*args, **kwargs)

    @pyqtSlot()
    def logPerformance(self):
        """
        Logs total CPU usage (in percent), as well as per-thread usage.
        """
        with self.perf.oneshot():
            total_percent = self.perf.cpu_percent(interval=None)
            total_time = sum(self.perf.cpu_times())
            usage = [total_percent * ((t.system_time + t.user_time) / total_time) for t in self.perf.threads()]
        LOG.info("Performance:\n    Total CPU usage: {tot}\n    Per Thread: {percpu}" \
            .format(tot=total_percent, percpu=usage))
