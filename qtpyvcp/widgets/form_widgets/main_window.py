import os
import sys

from qtpy import uic
from qtpy.QtGui import QKeySequence
from qtpy.QtCore import Qt, Slot, QTimer
from qtpy.QtWidgets import QMainWindow, QApplication, QAction, QMessageBox, \
    QMenu, QMenuBar, QLineEdit, QShortcut

import qtpyvcp
from qtpyvcp import actions
from qtpyvcp.utilities import logger
from qtpyvcp.core import Prefs, Info
from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets.dialogs import showDialog as _showDialog
from qtpyvcp.vcp_launcher import _initialize_object_from_dict

LOG = logger.getLogger(__name__)
PREFS = Prefs()
INFO = Info()


class VCPMainWindow(QMainWindow):

    def __init__(self, parent=None, opts=None, ui_file=None, stylesheet=None,
                 maximize=False, fullscreen=False, position=None, size=None,
                 confirm_exit=True, title=None, menu='default'):

        super(VCPMainWindow, self).__init__(parent)

        if opts is None:
            opts = qtpyvcp.OPTIONS

        self.setWindowTitle(title)

        self.app = QApplication.instance()

        self.confirm_exit = confirm_exit if opts.confirm_exit is None else opts.confirm_exit

        # Load the UI file AFTER defining variables, otherwise the values
        # set in QtDesigner get overridden by the default values
        if ui_file is not None:
            self.loadUi(ui_file)
            self.initUi()

        if menu is not None:
            try:
                # delete any preexisting menuBar added in QtDesigner
                # because it shadows the QMainWindow.menuBar() method
                del self.menuBar
            except AttributeError:
                pass

            if menu == 'default':
                menu = qtpyvcp.CONFIG.get('default_menubar', [])

            self.setMenuBar(self.buildMenuBar(menu))

        if title is not None:
            self.setWindowTitle(title)

        if stylesheet is not None:
            self.loadStylesheet(stylesheet)

        maximize = opts.maximize if opts.maximize is not None else maximize
        if maximize:
            QTimer.singleShot(0, self.showMaximized)

        fullscreen = opts.fullscreen if opts.fullscreen is not None else fullscreen
        if fullscreen:
            QTimer.singleShot(0, self.showFullScreen)

        if opts.hide_menu_bar:
            self.menuBar().hide()

        size = opts.size or size
        if size:
            try:
                width, height = size.lower().split('x')
                self.resize(int(width), int(height))
            except:
                LOG.exception('Error parsing --size argument: %s', size)

        pos = opts.position or position
        if pos:
            try:
                xpos, ypos = pos.lower().split('x')
                self.move(int(xpos), int(ypos))
            except:
                LOG.exception('Error parsing --position argument: %s', pos)

        QShortcut(QKeySequence("F11"), self, self.toggleFullscreen)
        self.app.focusChanged.connect(self.focusChangedEvent)

    def loadUi(self, ui_file):
        """Loads a window layout from a QtDesigner .ui file.

        Args:
            ui_file (str) : Path to a .ui file to load.
        """
        # TODO: Check for compiled *_ui.py files and load from that if exists
        uic.loadUi(ui_file, self)

    def loadStylesheet(self, stylesheet):
        """Loads a QSS stylesheet containing styles to be applied
        to specific Qt and/or QtPyVCP widget classes.

        Args:
            stylesheet (str) : Path to a .qss stylesheet
        """
        LOG.info("Loading QSS stylesheet file: yellow<{}>".format(stylesheet))
        with open(stylesheet, 'r') as fh:
            self.setStyleSheet(fh.read())

    def getMenuAction(self, menu_action, title='notitle', action_name='noaction',
                      args=[], kwargs={}):
        # ToDo: Clean this up, it is very hacky
        env = {'app': QApplication.instance(),
               'win': self,
               'action': actions,
               }

        if action_name is not None:
            try:
                mod, action = action_name.split('.', 1)
                method = getattr(env.get(mod, self), action)
                if menu_action.isCheckable():
                    menu_action.triggered.connect(method)
                else:
                    menu_action.triggered.connect(lambda checked: method(*args, **kwargs))
                return
            except:
                pass

            try:
                actions.bindWidget(menu_action, action_name)
                return
            except actions.InvalidAction:
                LOG.exception('Error binding menu action %s', action_name)

        msg = "The <b>{}</b> action specified for the " \
              "<b>{}</b> menu item could not be triggered. " \
              "Check the YAML config file for errors." \
              .format(action_name or '', title.replace('&', ''))
        menu_action.triggered.connect(lambda: QMessageBox.critical(self, "Menu Action Error!", msg))

    def buildMenuBar(self, menus):
        """Recursively build menu bar.

        Args:
            menus (list) : List of dicts and lists containing the
                items to add to the menu.

        Returns:
            QMenuBar
        """

        def recursiveAddItems(menu, items):

            for item in items:

                if item == 'separator':
                    menu.addSeparator()
                    continue

                if not isinstance(item, dict):
                    LOG.warn("Skipping unrecognized menu item: %s", item)
                    continue

                title = item.get('title') or ''
                items = item.get('items')
                provider = item.get('provider')
                args = item.get('args') or []
                kwargs = item.get('kwargs') or {}

                if items is not None:
                    new_menu = QMenu(parent=self, title=title)
                    recursiveAddItems(new_menu, items)
                    menu.addMenu(new_menu)

                elif provider is not None:
                    new_menu = _initialize_object_from_dict(item, parent=menu)
                    new_menu.setTitle(title)
                    menu.addMenu(new_menu)

                else:
                    act = QAction(parent=self, text=title)
                    self.getMenuAction(act, title, item.get('action'),
                                       item.get('args', []),
                                       item.get('kwargs', {}))
                    act.setShortcut(item.get('shortcut', ''))
                    menu.addAction(act)

        menu_bar = QMenuBar(self)
        recursiveAddItems(menu_bar, menus)
        return menu_bar

    def initUi(self):
        self.loadSplashGcode()

    @Slot()
    def toggleFullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        """Catch close event and show confirmation dialog."""
        if os.getenv('DESIGNER', False):
            self.close()

        elif self.confirm_exit:
            quit_msg = "Are you sure you want to exit LinuxCNC?"
            reply = QMessageBox.question(self, 'Exit LinuxCNC?',
                                         quit_msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                QApplication.instance().quit()
            else:
                event.ignore()
        else:
            self.app.quit()

    def keyPressEvent(self, event):
        # super(VCPMainWindow, self).keyPressEvent(event)
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key_Up:
            actions.machine.jog.axis('Y', 1)
        elif event.key() == Qt.Key_Down:
            actions.machine.jog.axis('Y', -1)
        elif event.key() == Qt.Key_Left:
            actions.machine.jog.axis('X', -1)
        elif event.key() == Qt.Key_Right:
            actions.machine.jog.axis('X', 1)
        elif event.key() == Qt.Key_PageUp:
            actions.machine.jog.axis('Z', 1)
        elif event.key() == Qt.Key_PageDown:
            actions.machine.jog.axis('Z', -1)
        #else:
            #print 'Unhandled key press event'

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key_Up:
            actions.machine.jog.axis('Y', 0)
        elif event.key() == Qt.Key_Down:
            actions.machine.jog.axis('Y', 0)
        elif event.key() == Qt.Key_Left:
            actions.machine.jog.axis('X', 0)
        elif event.key() == Qt.Key_Right:
            actions.machine.jog.axis('X', 0)
        elif event.key() == Qt.Key_PageUp:
            actions.machine.jog.axis('Z', 0)
        elif event.key() == Qt.Key_PageDown:
            actions.machine.jog.axis('Z', 0)
        #else:
            #print 'Unhandled key release event'

    def mousePressEvent(self, event):
        #print 'Button press'
        focused_widget = self.focusWidget()
        if focused_widget is not None:
            focused_widget.clearFocus()

    def focusChangedEvent(self, old_w, new_w):
        if issubclass(new_w.__class__, QLineEdit):
            #print "QLineEdit got focus: ", new_w
            QTimer.singleShot(0, new_w.selectAll)

# ==============================================================================
#  menu action slots
# ==============================================================================

    @Slot()
    def openFile(self):
        _showDialog('open_file')

    @Slot(str)
    def showDialog(self, dialog_name):
        _showDialog(dialog_name)

# ==============================================================================
# menu functions
# ==============================================================================



# ==============================================================================
# helper functions
# ==============================================================================

    def loadSplashGcode(self):
        # Load backplot splash code
        splash_code = INFO.getOpenFile()
        #print splash_code
        if splash_code is not None and os.path.isfile(splash_code):
            # Load after startup to not cause hang and 'Can't set mode while machine is running' error
            QTimer.singleShot(200, lambda: actions.program.load(splash_code, add_to_recents=False))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
