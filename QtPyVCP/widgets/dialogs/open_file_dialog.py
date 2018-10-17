#!/usr/bin/env python

import os
import sys


from qtpy import QtCore
from qtpy.QtGui import QIcon
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox, QFileDialog

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.core import Info
INFO = Info()

from qtpyvcp.actions.program_actions import load as loadProgram

class _OpenFileDialog(QFileDialog):
    """docstring for OpenFileDialog"""
    def __init__(self, parent=None):
        super(_OpenFileDialog, self).__init__(parent)

        nc_file_dir = INFO.getProgramPrefix()
        nc_file_types = INFO.getQtFilefilter()

        self.setDirectory(nc_file_dir)
        self.setNameFilters(nc_file_types.split(';;'))

        self.setOption(self.DontUseNativeDialog)

        urls = self.sidebarUrls()
        urls.append(QtCore.QUrl.fromLocalFile(nc_file_dir))
        self.setSidebarUrls(urls)

    def accept(self):
        path = self.selectedFiles()[0]
        stats = QtCore.QFileInfo(path)
        if stats.isDir():
            self.setDirectory(path)
            return
        if not stats.exists():
            return
        loadProgram(path)
        self.hide()

class OpenFileDialog(_OpenFileDialog):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = _OpenFileDialog(*args, **kwargs)
        return cls._instance
