#!/usr/bin/env python

#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSlot, pyqtProperty
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QAction, QMessageBox, QFileDialog

from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.core import Status, Action, Prefs, Info
STATUS = Status()
ACTION = Action()
PREFS = Prefs()
INFO = Info()

from QtPyVCP.widgets.dialogs.open_file_dialog import OpenFileDialog


class VCPMainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VCPMainWindow, self).__init__(parent=None)

        # QtDesigner settable vars
        self.prompt_at_exit = True

        # Variables
        self.recent_file_actions = []
        self.recent_files = []

        self.log_file_path = ''

        self.open_file_dialog = OpenFileDialog(self)

        self.initUi()

    def initUi(self):
        self.initRecentFileMenu()

        if hasattr(self, 'actionToggle_Power'):
            action = getattr(self, 'actionToggle_Power')
            STATUS.estop.connect(lambda v:action.setEnabled(not bool(v)))

            # STATUS.forceUpdate()

    def closeEvent(self, event):
        """Catch close event and show confirmation dialog if set to"""
        if self.prompt_at_exit:
            quit_msg = "Are you sure you want to exit LinuxCNC?"
            reply = QMessageBox.question(self, 'Exit LinuxCNC?',
                             quit_msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        # super(VCPMainWindow, self).keyPressEvent(event)
        if event.key() == Qt.Key_Up:
            print 'Move Up'
        elif event.key() == Qt.Key_Down:
            print 'Move Down'
        elif event.key() == Qt.Key_Left:
            print 'Move Left'
        elif event.key() == Qt.Key_Right:
            print 'Move Right'
        else:
            print 'Unhandled key press event '

    def mousePressEvent(self, event):
        print 'Button press'
        focused_widget = self.focusWidget()
        if focused_widget is not None:
            focused_widget.clearFocus()


        # focused_widget = QtGui.QApplication.focusWidget()
        # if isinstance(focused_widget, MyLineEdit):
        #     focused_widget.clearFocus()
        # QtGui.QMainWindow.mousePressEvent(self, event)


#==============================================================================
#  menu action slots
#==============================================================================

    # File menu

    @pyqtSlot()
    def on_actionOpen_triggered(self):
        self.open_file_dialog.show()

    @pyqtSlot()
    def on_actionExit_triggered(self):
        self.close()

    #==========================================================================
    # Machine menu
    #==========================================================================

    @pyqtSlot()
    def on_actionToggle_E_stop_triggered(self):
        ACTION.toggleEmergencyStop()

    @pyqtSlot()
    def on_actionToggle_Power_triggered(self):
        ACTION.toggleMachinePower()

    @pyqtSlot()
    def on_actionRun_Program_triggered(self):
        ACTION.runProgram()

    @pyqtSlot()
    def on_actionHome_All_triggered(self):
        ACTION.homeJoint(-1)

    @pyqtSlot()
    def on_actionHome_X_triggered(self):
        ACTION.homeJoint(1)

    @pyqtSlot(bool)
    def on_actionReport_Actual_Position_toggled(self, report_actual):
        STATUS.setReportActualPosition(report_actual)


#==============================================================================
# menu functions
#==============================================================================

    def initRecentFileMenu(self):
        if hasattr(self, 'menuRecentFiles'):

            # remove any actions that were added in QtDesigner
            for action in self.menuRecentFiles.actions():
                self.menuRecentFiles.removeAction(action)

            # add new actions
            for i in range(STATUS.max_recent_files):
                action = QAction(self, visible=False,
                                 triggered=(lambda:ACTION.loadProgram(self.sender().data())))
                self.recent_file_actions.append(action)
                self.menuRecentFiles.addAction(action)

            self.updateRecentFilesMenu(STATUS.recent_files)
            STATUS.recent_files_changed.connect(self.updateRecentFilesMenu)

    def updateRecentFilesMenu(self, recent_files):
        for i, fname in enumerate(recent_files):
            text = "&{} {}".format(i + 1, os.path.split(fname)[1])
            action = self.recent_file_actions[i]
            action.setText(text)
            action.setData(fname)
            action.setVisible(True)

#==============================================================================
# helper functions
#==============================================================================


#==============================================================================
#  QtDesigner property setters/getters
#==============================================================================

    # Whether to show a confirmation prompt when closing the main window
    def getPromptBeforeExit(self):
        return self.prompt_at_exit
    def setPromptBeforeExit(self, value):
        self.prompt_at_exit = value
    promptAtExit = pyqtProperty(bool, getPromptBeforeExit, setPromptBeforeExit)

    # Max number of recent files to display in menu
    def getMaxRecentFiles(self):
        return STATUS.max_recent_files
    def setMaxRecentFiles(self, number):
        STATUS.max_recent_files = number
    maxNumRecentFiles = pyqtProperty(int, getMaxRecentFiles, setMaxRecentFiles)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
