import os
import sys
import linuxcnc

from qtpy import uic
from qtpy.QtGui import QKeySequence
from qtpy.QtCore import Qt, Slot, QTimer
from qtpy.QtWidgets import QMainWindow, QApplication, QAction, QMessageBox, \
    QMenu, QMenuBar, QLineEdit, QShortcut, QActionGroup

import qtpyvcp
from qtpyvcp import actions
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import getSetting
from qtpyvcp.widgets.dialogs import showDialog as _showDialog
from qtpyvcp.app.launcher import _initialize_object_from_dict

LOG = logger.getLogger(__name__)
INFO = Info()
STATUS = getPlugin('status')

class VCPMainWindow(QMainWindow):

    def __init__(self, parent=None, opts=None, ui_file=None, stylesheet=None,
                 maximize=False, fullscreen=False, position=None, size=None,
                 confirm_exit=True, title=None, menu='default'):

        super(VCPMainWindow, self).__init__(parent)

        if opts is None:
            opts = qtpyvcp.OPTIONS

        self._inifile = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        self._keyboard_jog = self._inifile.find("DISPLAY", "KEYBOARD_JOG") or "false"
        self._keyboard_jog_ctrl_off = self._inifile.find("DISPLAY", "KEYBOARD_JOG_SAFETY_OFF") or "false"
        lathe_val = (self._inifile.find("DISPLAY", "LATHE") or "0").strip().lower()
        back_tool_val = (self._inifile.find("DISPLAY", "BACK_TOOL_LATHE") or "0").strip().lower()
        self._lathe_mode = (lathe_val not in ["0", "false", "no", "n", ""]) or (back_tool_val not in ["0", "false", "no", "n", ""])
        self._back_tool_lathe = back_tool_val not in ["0", "false", "no", "n", ""]
        # keyboard jogging multi key press tracking
        # Key   Purpose
        # ---   ---------------------------------------------
        #  -    Slow jog speed to a fixed %.  e.g. 30%
        #  +    Max rapid speed for jog
        # Ctl   ctrl key needs to be pushed to enable jog
        self.slow_jog = False
        self.rapid_jog = False

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

        # Add a timer to periodically check for focus and stop jogging if not active
        self._jog_active = False  # Track if keyboard jog is currently active
        self._jog_safety_timer = QTimer(self)
        self._jog_safety_timer.timeout.connect(self._jogSafetyCheck)
        self._jog_safety_timer.start(100)  # check every 100ms

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
        self.setStyleSheet("file:///" + stylesheet)

    def stopAllJogAxes(self):
        # Stop all axes (X, Y, Z, and optionally A, B, C)
        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
            try:
                actions.machine.jog.axis(axis, 0)
            except Exception:
                pass
        # Also reset jog state so keyReleaseEvent doesn't expect a key to be held
        self.slow_jog = False
        self.rapid_jog = False

    def showModalDialog(self, dialog_func, *args, **kwargs):
        # Stop all jog axes before showing any modal dialog
        self.stopAllJogAxes()
        return dialog_func(*args, **kwargs)

    def getMenuAction(self, menu, title='notitle', action_name='noaction',
                      shortcut="", args=[], kwargs={}):
        # ToDo: Clean this up, it is very hacky
        env = {'app': QApplication.instance(),
               'win': self,
               'action': actions,
               }

        if action_name is not None:

            if action_name.startswith('settings.'):
                setting_id = action_name[len('settings.'):]
                setting = getSetting(setting_id)

                if setting:
                    if setting.enum_options is not None:
                        submenu = QMenu(parent=self, title=title)

                        group = QActionGroup(self)
                        group.setExclusive(True)
                        group.triggered.connect(lambda a: setting.setValue(a.data()))

                        def update(group, val):
                            for act in group.actions():
                                if act.data() == val:
                                    act.setChecked(True)
                                    break

                        for num, opt in enumerate(setting.enum_options):

                            menu_action = QAction(parent=self, text=opt)
                            menu_action.setCheckable(True)
                            if setting.value == num:
                                menu_action.setChecked(True)

                            menu_action.setData(num)
                            setting.notify(lambda v: update(group, v))

                            menu_action.setActionGroup(group)
                            submenu.addAction(menu_action)
                        menu.addMenu(submenu)

                    elif setting.value_type == bool:
                        # works for bool settings
                        menu_action = QAction(parent=self, text=title)
                        menu_action.setCheckable(True)
                        menu_action.triggered.connect(setting.setValue)
                        menu_action.setShortcut(shortcut)
                        setting.notify(menu_action.setChecked)
                        menu.addAction(menu_action)

                    return

            try:
                menu_action = QAction(parent=self, text=title)

                mod, action = action_name.split('.', 1)
                method = getattr(env.get(mod, self), action)
                if menu_action.isCheckable():
                    menu_action.triggered.connect(method)
                else:
                    menu_action.triggered.connect(lambda checked: method(*args, **kwargs))

                menu_action.setShortcut(shortcut)
                menu.addAction(menu_action)
                return
            except:
                pass

            try:
                menu_action = QAction(parent=self, text=title)
                actions.bindWidget(menu_action, action_name)
                menu_action.setShortcut(shortcut)
                menu.addAction(menu_action)
                return
            except actions.InvalidAction:
                LOG.exception('Error binding menu action %s', action_name)

        menu_action = QAction(parent=self, text=title)
        msg = "The <b>{}</b> action specified for the " \
              "<b>{}</b> menu item could not be triggered. " \
              "Check the YAML config file for errors." \
              .format(action_name or '', title.replace('&', ''))
        # Use showModalDialog to ensure jogging is stopped
        menu_action.triggered.connect(lambda: self.showModalDialog(QMessageBox.critical, self, "Menu Action Error!", msg))
        menu.addAction(menu_action)

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
                    self.getMenuAction(menu, title, item.get('action'),
                                       item.get('shortcut', ''),
                                       item.get('args', []),
                                       item.get('kwargs', {}))

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
        # Use showModalDialog to ensure jogging is stopped
        if os.getenv('DESIGNER', False):
            self.close()
        elif self.confirm_exit:
            quit_msg = "Are you sure you want to exit LinuxCNC?"
            reply = self.showModalDialog(QMessageBox.question, self, 'Exit LinuxCNC?',
                                         quit_msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                QApplication.instance().quit()
            else:
                event.ignore()
        else:
            self.app.quit()

    def keyPressEvent(self, event):
        # super(VCPMainWindow, self).keyPressEvent(event)
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            self.stopAllJogAxes()  # Stop jog if UI is locked (e.g., by modal dialog)
            LOG.debug('Accept keyPressEvent Event')
            event.accept()
            return
        
        if self._keyboard_jog.lower() in ['false', '0', 'f', 'n', 'no']:
            event.accept()
            return
          
        if event.isAutoRepeat():
            return

        if self.app.focusWidget() != None:
            LOG.debug(f"Focus widget = {self.app.focusWidget().objectName()}")
        else:
            LOG.debug(f"Focus widget = None")

        # Determine jog speed: Shift always means rapid jog
        if event.modifiers() & Qt.ShiftModifier:
            speed = actions.machine.MAX_JOG_SPEED / 60
        elif self.rapid_jog:
            speed = actions.machine.MAX_JOG_SPEED / 60
        elif self.slow_jog:
            speed = actions.machine.jog_linear_speed() / 60 / 10.0
        else:
            speed = None

        # Consistent jog safety logic
        if self._keyboard_jog_ctrl_off.lower() in ['true', '1', 't', 'y', 'yes']:
            jog_active = 1
        elif event.modifiers() & Qt.ControlModifier:
            jog_active = 1
        else:
            jog_active = 0

        LOG.debug("GLOBAL - Key event processing")

        jog_started = False
        # Only jog if jog_active is set
        if jog_active:
            if self._lathe_mode:
                # Invert X axis for LATHE=1 and not BACK_TOOL_LATHE=1
                x_sign = -1 if (not self._back_tool_lathe and self._lathe_mode) else 1
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('X', 1 * x_sign, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('X', -1 * x_sign, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('Z', -1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('Z', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Y', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Y', -1, speed=speed)
                    jog_started = True
            else:
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('Y', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('Y', -1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('X', -1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('X', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Z', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Z', -1, speed=speed)
                    jog_started = True

        # Handle jog speed keys regardless of jog_active
        if event.key() == Qt.Key_Minus:
            self.slow_jog = True
            self.rapid_jog = False
        elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
            self.rapid_jog = True
            self.slow_jog = False

        if jog_started:
            self._jog_active = True

    def keyReleaseEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            self.stopAllJogAxes()  # Stop jog if UI is locked (e.g., by modal dialog)
            LOG.debug('Accept keyReleaseEvent Event')
            event.accept()
            return

        if self._keyboard_jog.lower() in ['false', '0', 'f', 'n', 'no']:
            event.accept()
            return
        
        if event.isAutoRepeat():
            return

        jog_stopped = False
        if self._lathe_mode:
            x_sign = -1 if (not self._back_tool_lathe and self._lathe_mode) else 1
            if event.key() == Qt.Key_Up:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Down:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Left:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Right:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageUp:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageDown:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Minus:
                self.slow_jog = False
            elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                self.rapid_jog = False
        else:
            if event.key() == Qt.Key_Up:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Down:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Left:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Right:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageUp:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageDown:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Minus:
                self.slow_jog = False
            elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                self.rapid_jog = False
        if jog_stopped:
            self._jog_active = False

    def mousePressEvent(self, event):
        #print('Button press')
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept mouse Press Event')
            event.accept()
            return 
        focused_widget = self.focusWidget()
        if focused_widget is not None:
            focused_widget.clearFocus()

    def mouseReleaseEvent(self, event):
        if STATUS.isLocked():
            LOG.debug('Accept mouse Release Event')
            event.accept()
            return 
        super().mouseReleaseEvent(event)

    def focusChangedEvent(self, old_w, new_w):
        # Only handle QLineEdit selection, no jog stop needed here anymore
        if issubclass(new_w.__class__, QLineEdit):
            QTimer.singleShot(0, new_w.selectAll)

    def _jogSafetyCheck(self):
        # Only stop axes if keyboard jog is currently active and window is not focused
        if self._jog_active and not self.isActiveWindow():
            self.stopAllJogAxes()
            self._jog_active = False

# ==============================================================================
#  menu action slots
# ==============================================================================

    @Slot()
    def openFile(self):
        self.showModalDialog(_showDialog, 'open_file')

    @Slot(str)
    def showDialog(self, dialog_name):
        self.showModalDialog(_showDialog, dialog_name)

# ==============================================================================
# menu functions
# ==============================================================================



# ==============================================================================
# helper functions
# ==============================================================================

    def loadSplashGcode(self):
        # Load backplot splash code
        splash_code = INFO.getOpenFile()
        #print(splash_code)
        if splash_code is not None and os.path.isfile(splash_code):
            # Load after startup to not cause hang and 'Can't set mode while machine is running' error
            QTimer.singleShot(200, lambda: actions.program.load(splash_code, add_to_recents=False))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
