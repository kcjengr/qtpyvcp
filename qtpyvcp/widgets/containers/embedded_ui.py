"""
Embedded UI
-----------

This widget allows embedding UI files into a VCP. This makes it possible to
repeat and reuse layouts throughout a VCP. Useful for things like DROs that
might be repeated many times in a single VCP.

A file system watcher is used to automatically update the embedded display
when the embedded UI file is edited.
"""

import os

from qtpy import uic
from qtpy.QtCore import Property, QFileSystemWatcher
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel

from qtpyvcp.widgets.base_widgets.base_widget import VCPWidget


class EmbeddedUI(QWidget, VCPWidget):
    """Embedded UI

    Creates a widget from a layout defined in a separate UI file.

    Args:
        parent (QWidget) : The widgets parent. Defaults to None.
        embed_file (str) : The path to the file to embed. Defaults to None.
    """

    def __init__(self, parent=None, embed_file=None):
        super(EmbeddedUI, self).__init__(parent)

        self.layout = QVBoxLayout(self)
        self.label = QLabel('No UI file specified to embed')
        self.layout.addWidget(self.label)

        self.embedded_filename = embed_file
        self.embedded_widget = None

        self.fs_watcher = QFileSystemWatcher()
        self.fs_watcher.fileChanged.connect(self.onFileUpdated)

    def loadUI(self, fname):
        if self.embedded_widget is not None:
            self.layout.removeWidget(self.embedded_widget)
            self.embedded_widget.deleteLater()

        if os.path.isfile(fname):
            self.label.hide()
            self.embedded_widget = uic.loadUi(fname)
            self.layout.addWidget(self.embedded_widget)
        else:
            self.label.show()

    def onFileUpdated(self, fname):
        print 'reloading after UI file edited: ', fname
        self.loadUI(fname)

    @Property(str)
    def FileName(self):
        """The file name of the UI file to embed.

        ToDo:
            This should be a path relative to the embedding UI file.
        """
        if self.embedded_filename is None:
            return ""
        return self.embedded_filename

    @FileName.setter
    def FileName(self, fname):
        fname = os.path.realpath(os.path.expanduser(fname))

        if self.embedded_filename is not None:
            self.fs_watcher.removePath(self.embedded_filename)

        self.embedded_filename = fname

        if os.path.isfile(fname):
            self.fs_watcher.addPath(fname)
            self.loadUI(fname)
