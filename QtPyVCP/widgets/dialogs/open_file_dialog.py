#!/usr/bin/env python

import os
import sys

from PyQt5 import Qt

from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.core import Status, Action, Prefs, Info
STATUS = Status()
ACTION = Action()
PREFS = Prefs()
INFO = Info()

class _OpenFileDialog(Qt.QFileDialog):
    """docstring for OpenFileDialog"""
    def __init__(self, parent=None):
        super(_OpenFileDialog, self).__init__(parent)

        nc_file_dir = INFO.getProgramPrefix()
        nc_file_types = INFO.getQtFilefilter()

        self.setDirectory(nc_file_dir)
        self.setNameFilters(nc_file_types.split(';;'))

        self.setOption(self.DontUseNativeDialog)

        urls = self.sidebarUrls()
        urls.append(Qt.QUrl.fromLocalFile(nc_file_dir))
        self.setSidebarUrls(urls)

    def accept(self):
        path = self.selectedFiles()[0]
        stats = Qt.QFileInfo(path)
        if stats.isDir():
            self.setDirectory(path)
            return
        if not stats.exists():
            return
        ACTION.loadProgram(path)
        self.hide()

class OpenFileDialog(_OpenFileDialog):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = _OpenFileDialog(*args, **kwargs)
        return cls._instance
