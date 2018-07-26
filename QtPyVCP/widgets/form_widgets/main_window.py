#!/usr/bin/env python
# coding: utf-8

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
import time

from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSlot, pyqtProperty, QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QAction, QMessageBox, QFileDialog, QMenu, QLineEdit

from PyQt5 import QtWidgets, QtGui

from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

from QtPyVCP.core import Status, Action, Prefs, Info
STATUS = Status()
ACTION = Action()
PREFS = Prefs()
INFO = Info()

from QtPyVCP.utilities import action

from QtPyVCP.widgets.dialogs.open_file_dialog import OpenFileDialog

from QtPyVCP.utilities import action


class VCPMainWindow(QMainWindow):

    def __init__(self, parent=None, ui_file=None):
        super(VCPMainWindow, self).__init__(parent=None)

        # QtDesigner settable vars
        self.prompt_at_exit = True

        # Variables
        self.recent_file_actions = []
        self.log_file_path = ''
        self.actions = []
        self.open_file_dialog = OpenFileDialog(self)

        # Load the UI file AFTER defining variables, otherwise the values
        # set in QtDesigner get overridden by the default values
        if ui_file is not None:
            uic.loadUi(ui_file, self)

        STATUS.init_ui.emit()
        self.initUi()

    def initUi(self):
        print "initiating"
        self.loadSplashGcode()
        self.initRecentFileMenu()
        self.initHomingMenu()

        s = time.time()

        menus = self.findChildren(QMenu)
        for menu in menus:
            menu_actions = menu.actions()
            for menu_action in menu_actions:
                if menu_action.isSeparator():
                    continue
                data = menu_action.objectName().split('_', 2)
                if data[0] == "action" and len(data) > 1:
                    try:
                        action_class =  getattr(action, data[1])
                        action_instance = action_class(menu_action, action_type=data[2])
                        # print "ACTION: ", action_instance
                    except:
                        LOG.warn("Could not connect action", exc_info=True)
                        continue
                    self.actions.append(action_instance)

        print "action time ", time.time() - s

    @pyqtSlot()
    def on_power_clicked(self):
        action.Home.unhomeAxis('x')

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
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key_Up:
            print 'Move Up'
            action.Jogging.autoJog('Y', 1)
        elif event.key() == Qt.Key_Down:
            print 'Move Down'
            action.Jogging.autoJog('Y', -1)
        elif event.key() == Qt.Key_Left:
            print 'Move Left'
            action.Jogging.autoJog('X', -1)
        elif event.key() == Qt.Key_Right:
            print 'Move Right'
            action.Jogging.autoJog('X', 1)
        elif event.key() == Qt.Key_PageUp:
            print 'Page Up'
            action.Jogging.autoJog('Z', 1)
        elif event.key() == Qt.Key_PageDown:
            print 'Page Down'
            action.Jogging.autoJog('Z', -1)
        else:
            print 'Unhandled key press event'

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key_Up:
            print 'Move Up'
            action.Jogging.autoJog('Y', 0)
        elif event.key() == Qt.Key_Down:
            print 'Move Down'
            action.Jogging.autoJog('Y', 0)
        elif event.key() == Qt.Key_Left:
            print 'Move Left'
            action.Jogging.autoJog('X', 0)
        elif event.key() == Qt.Key_Right:
            print 'Move Right'
            action.Jogging.autoJog('X', 0)
        elif event.key() == Qt.Key_PageUp:
            print 'Page Up'
            action.Jogging.autoJog('Z', 0)
        elif event.key() == Qt.Key_PageDown:
            print 'Page Down'
            action.Jogging.autoJog('Z', 0)
        else:
            print 'Unhandled key release event'


    def mousePressEvent(self, event):
        print 'Button press'
        focused_widget = self.focusWidget()
        if focused_widget is not None:
            focused_widget.clearFocus()

    def focusChangedEvent(self, new_w, old_w):
        print "focus changed"
        if isinstance(new_w, QLineEdit):
            print "Line edit got focus"

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
            fname = fname.encode('utf-8')
            text = "&{} {}".format(i + 1, os.path.split(fname)[1])
            action = self.recent_file_actions[i]
            action.setText(text)
            action.setData(fname)
            action.setVisible(True)


    def initHomingMenu(self):
        if hasattr(self, 'menuHoming'):

            # remove any actions that were added in QtDesigner
            for menu_action in self.menuHoming.actions():
                self.menuHoming.removeAction(menu_action)

            # Register the submenu with the action (so it will be disabled
            # if the actions are not valid), but don't connect it to method
            home_action = action.Home(widget=self.menuHoming, method=None)

            menu_action = QAction(self)
            menu_action.setText("Home &All")
            home_action = action.Home(widget=menu_action, method='homeAll', axis='all')
            self.menuHoming.addAction(menu_action)

            # add homing actions for each axis
            for aletter in INFO.AXIS_LETTER_LIST:
                menu_action = QAction(self)
                menu_action.setText("Home &{}".format(aletter.upper()))
                home_action = action.Home(widget=menu_action, method='homeAxis', axis=aletter)
                self.menuHoming.addAction(menu_action)
                self.actions.append(menu_action)

#==============================================================================
# helper functions
#==============================================================================

    def loadSplashGcode(self):
        # Load backplot splash code
        path = os.path.realpath(os.path.join(__file__, '../../../..', 'sim/example_gcode/qtpyvcp.ngc'))
        splash_code = INFO.getOpenFile() or path
        if splash_code is not None:
            # Load after startup to not cause delay
            QTimer.singleShot(0, lambda: ACTION.loadProgram(splash_code, add_to_recents=False))


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
