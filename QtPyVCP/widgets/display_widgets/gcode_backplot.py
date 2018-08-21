#!/usr/bin/env python
# coding: utf-8
#
#    Copyright 2016 Chris Morley
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# PyQt5 widget for plotting gcode.


import sys
import os
import gcode
import time

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor

from QtPyVCP.widgets.base_widgets.qbackplot import QBackPlot

from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.core import Status, Action, Info
STATUS = Status()
ACTION = Action()
INFO = Info()


class  GcodeBackplot(QBackPlot):

    line_selected = pyqtSignal(int)
    gcode_error = pyqtSignal(str)

    def __init__(self, parent=None, standalone=False):
        super(GcodeBackplot, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None and not standalone:
            return

        self.show_overlay = False  # no DRO or DRO overlay
        self._reload_filename = None

        # Add loading progress bar and abort button
        self.progressBar = QtWidgets.QProgressBar(visible=False)
        self.progressBar.setFormat("Loading backplot: %p%")
        self.abortButton = QtWidgets.QPushButton('Abort', visible=False)

        hBox = QtWidgets.QHBoxLayout()
        hBox.addWidget(self.progressBar)
        hBox.addWidget(self.abortButton)

        vBox = QtWidgets.QVBoxLayout(self)
        vBox.addStretch()
        vBox.addLayout(hBox)

        self.abortButton.clicked.connect(self.abort)


        STATUS.actual_position.connect(self.update)
        STATUS.joint_actual_position.connect(self.update)
        STATUS.homed.connect(self.update)
        STATUS.g5x_offset.connect(self.update)
        STATUS.g92_offset.connect(self.update)
        STATUS.limit.connect(self.update)
        STATUS.tool_in_spindle.connect(self.update)
        STATUS.motion_mode.connect(self.update)
        STATUS.current_vel.connect(self.update)

        # Connect status signals
        STATUS.file_loaded.connect(self.loadBackplot)
        STATUS.reload_backplot.connect(self.reloadBackplot)
        STATUS.program_units.connect(lambda v: self.setMetricUnits(v==2))

    def loadBackplot(self, fname):
        LOG.debug('load the display: {}'.format(fname.encode('utf-8')))
        self._reload_filename = fname
        self.load(fname)

    def reloadBackplot(self):
        LOG.debug('reload the display: {}'.format(self._reload_filename))
        dist = self.get_zoom_distance()
        try:
            self.loadBackplot(self._reload_filename)
            self.set_zoom_distance(dist)
        except:
            LOG.warning("Problem reloading backplot file: {}".format(self._reload_filename), exc_info=True)

    #==========================================================================
    #  Override QBackPlot methods
    #==========================================================================

    def set_view(self, value):
        view = str(value).lower()
        if self.lathe_option:
            if view not in ['p', 'y', 'y2']:
                return False
        elif view not in ['p', 'x', 'y', 'z', 'z2']:
            return False
        self.current_view = view
        if self.initialised:
            self.set_current_view()

    def report_loading_started(self):
        self.progressBar.show()
        self.abortButton.show()
        self.start = time.time()

    def report_progress_percentage(self, percentage):
        QApplication.processEvents()
        self.progressBar.setValue(percentage)

    def report_loading_finished(self):
        print time.time() - self.start
        self.progressBar.hide()
        self.abortButton.hide()

    # overriding functions
    def report_gcode_error(self, result, seq, filename):
        error = gcode.strerror(result)
        file = os.path.basename(filename)
        line = seq - 1
        msg = "G-code error in '{}' near line {}: {}".format(file, line, error)
        LOG.error(msg)
        STATUS.backplot_gcode_error.emit(msg)

    # Override gremlin's / glcannon.py function so we can emit a GObject signal
    def update_highlight_variable(self, line):
        self.highlight_line = line
        if line is None:
            line = -1
        STATUS.backplot_line_selected.emit(line)


#==============================================================================
#  QtDesigner property setters/getters
#==============================================================================

    def setView(self, view):
        view = str(value).lower()
        if self.lathe_option:
            if view not in ['p', 'y', 'y2']:
                return False
        elif view not in ['p', 'x', 'y', 'z', 'z2']:
            return False
        self.current_view = view
        if self.initialised:
            self.set_current_view()
    def getView(self):
        return self.current_view
    defaultView = pyqtProperty(str, getView, setView)

    # DRO
    def setdro(self, state):
        self.enable_dro = state
        self.updateGL()
    def getdro(self):
        return self.enable_dro
    _dro = pyqtProperty(bool, getdro, setdro)

    # DTG
    def setdtg(self, state):
        self.show_dtg = state
        self.updateGL()
    def getdtg(self):
        return self.show_dtg
    _dtg = pyqtProperty(bool, getdtg, setdtg)

    # METRIC
    def setMetricUnits(self, metric):
        self.metric_units = metric
        self.updateGL()
    def getMetricUnits(self):
        return self.metric_units
    metricUnits = pyqtProperty(bool, getMetricUnits, setMetricUnits)



    def setProgramAlpha(self, alpha):
        self.program_alpha = alpha
        self.updateGL()
    def getProgramAlpha(self):
        return self.program_alpha
    renderProgramAlpha = pyqtProperty(bool, getProgramAlpha, setProgramAlpha)


    def setBackgroundColor(self, color):
        self.colors['back'] = color.getRgbF()[:3]
        self.updateGL()
    def getBackgroundColor(self):
        r, g, b = self.colors['back']
        color = QColor()
        color.setRgbF(r, g, b, 1.0)
        return color
    backgroundColor = pyqtProperty(QColor, getBackgroundColor, setBackgroundColor)



# For testing purposes, include code to allow a widget to be created and shown
# if this file is run.
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget =  GcodeBackPlot(standalone=True)
    widget.show()
    sys.exit(app.exec_())
