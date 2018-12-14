"""Main QtPyVCP Application Module

Contains the VCPApplication class with core function and VCP loading logic.
"""
import os
import sys
import imp
import inspect
from pkg_resources import iter_entry_points

from qtpy import API
from qtpy.QtCore import QTimer, Slot
from qtpy.QtWidgets import QApplication, QStyleFactory

import qtpyvcp

from qtpyvcp.utilities.logger import initBaseLogger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow

# initialize logging. If a base logger was already initialized in a startup
# script (e.g. vcp_launcher.py), then that logger will be returned, otherwise
# this will initialise a base logger with default log level of DEBUG
LOG = initBaseLogger('qtpyvcp')

# Needed to silence this PySide2 warning:
#    Qt WebEngine seems to be initialized from a plugin. Please set
#    Qt::AA_ShareOpenGLContexts using QCoreApplication::setAttribute
#    before constructing QGuiApplication.
if API == 'pyside2':
    from qtpy.QtCore import Qt
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)


class VCPApplication(QApplication):

    def __init__(self, vcp_file=None, stylesheet=None):
        super(VCPApplication, self).__init__(qtpyvcp.OPTIONS.command_line_args or [])

        opts = qtpyvcp.OPTIONS

        qApp = QApplication.instance()

        from qtpyvcp.core import Prefs, Info
        self.info = Info()
        self.prefs = Prefs()
        self.status = getPlugin('status')

        self.initialiseDataPlugins()

        if opts.theme is not None:
            self.setStyle(QStyleFactory.create(opts.theme))

        stylesheet = opts.stylesheet or stylesheet
        if stylesheet is not None:
            self.loadStylesheet(stylesheet)

        # self.window = self.loadVCPMainWindow(opts, vcp_file)
        # if self.window is not None:
        #     self.window.show()

        # Performance monitoring
        if opts.perfmon:
            import psutil
            self.perf = psutil.Process()
            self.perf_timer = QTimer()
            self.perf_timer.setInterval(2000)
            self.perf_timer.timeout.connect(self.logPerformance)
            self.perf_timer.start()

        self.aboutToQuit.connect(self.terminateDataPlugins)

    def loadVCPMainWindow(self, opts, vcp_file=None):
        """
        Loads a VCPMainWindow instance defined by a Qt .ui file, a Python .py
        file, or from a VCP python package.

        Parameters
        ----------
        vcp_file : str
            The path or name of the VCP to load.
        opts : OptDict
            A OptDict of options to pass to the VCPMainWindow subclass.

        Returns
        -------
        VCPMainWindow instance
        """
        vcp = opts.vcp or vcp_file
        if vcp is None:
            return

        if os.path.exists(vcp):

            vcp_path = os.path.realpath(vcp)
            if os.path.isfile(vcp_path):
                directory, filename = os.path.split(vcp_path)
                name, ext = os.path.splitext(filename)
                if ext == '.ui':
                    LOG.info("Loading VCP from UI file: yellow<{}>".format(vcp))
                    return VCPMainWindow(opts=opts, ui_file=vcp_path)
                elif ext == '.py':
                    LOG.info("Loading VCP from PY file: yellow<{}>".format(vcp))
                    return self.loadPyFile(vcp_path, opts)
            elif os.path.isdir(vcp_path):
                LOG.info("VCP is a directory")
                # TODO: Load from a directory if it has a __main__.py entry point
        else:
            try:
                entry_points = {}
                for entry_point in iter_entry_points(group='qtpyvcp.example_vcp'):
                    entry_points[entry_point.name] = entry_point
                for entry_point in iter_entry_points(group='qtpyvcp.vcp'):
                    entry_points[entry_point.name] = entry_point
                window = entry_points[vcp.lower()].load()
                return window(opts=opts)
            except:
                LOG.exception("Failed to load entry point")

        LOG.critical("VCP could not be loaded: yellow<{}>".format(vcp))
        sys.exit()

    def loadPyFile(self, pyfile, opts):
        """
        Load a .py file, performs some sanity checks to try and determine
        if the file actually contains a valid VCPMainWindow subclass, and if
        the checks pass, create and return an instance.

        This is an internal method, users will usually want to use `loadVCP` instead.

        Parameters
        ----------
        pyfile : str
            The path to a .py file to load.
        opts : OptDict
            A OptDict of options to pass to the VCPMainWindow subclass.

        Returns
        -------
        VCPMainWindow instance
        """
        # Add the pyfile module directory to the python path, so that submodules can be loaded
        module_dir = os.path.dirname(os.path.abspath(pyfile))
        sys.path.append(module_dir)

        # Load the module. It's attributes can be accessed via `python_vcp.attr`
        module = imp.load_source('python_vcp', pyfile)

        classes = [obj for name, obj in inspect.getmembers(module)
                   if inspect.isclass(obj)
                   and issubclass(obj, VCPMainWindow)
                   and obj != VCPMainWindow]
        if len(classes) == 0:
            raise ValueError("Invalid File Format."
                             " {} has no class inheriting from VCPMainWindow.".format(pyfile))
        if len(classes) > 1:
            LOG.warn("More than one VCPMainWindow class in file yellow<{}>."
                     " The first occurrence (in alphabetical order) will be used: {}"
            .format(pyfile, classes[0].__name__))
        cls = classes[0]

        # initialize and return the VCPMainWindow subclass
        return cls(opts=opts)

    def loadStylesheet(self, stylesheet):
        """Loads a QSS stylesheet file containing styles to be applied
        to specific Qt and/or QtPyVCP widget classes.

        Args:
            stylesheet (str) : Path to the .qss stylesheet to load.
        """
        LOG.info("Loading QSS stylesheet file: yellow<{}>".format(stylesheet))
        with open(stylesheet, 'r') as fh:
            self.setStyleSheet(fh.read())

    @Slot()
    def logPerformance(self):
        """Logs total CPU usage (in percent), as well as per-thread usage.
        """
        with self.perf.oneshot():
            total_percent = self.perf.cpu_percent(interval=None)
            total_time = sum(self.perf.cpu_times())
            usage = ["{:.3f}".format(total_percent * ((t.system_time + t.user_time) / total_time)) for t in self.perf.threads()]

        LOG.info("Performance:\n"
                 "    Total CPU usage (%): {}\n"
                 "    Per Thread: {}\n"
                 .format(total_percent, ' '.join(usage)))


    def initialiseDataPlugins(self):
        for plugin in qtpyvcp.PLUGINS.itervalues():
            plugin.initialise()

    def terminateDataPlugins(self):
        for plugin in qtpyvcp.PLUGINS.itervalues():
            plugin.terminate()
