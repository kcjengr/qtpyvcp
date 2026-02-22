import os

import linuxcnc

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Slot, Qt, QEvent, QPoint, QFile
from PySide6.QtGui import QInputMethodEvent, QGuiApplication, QKeyEvent
from PySide6.QtWidgets import QWidget, QAbstractButton, QAbstractSpinBox, QApplication
from qtpyvcp.utilities.pyside_ui_loader import PySide6Ui


class VirtualInput(QWidget):
    """VirtualInput

    This class provides support for a virtual num pad and keyboard.
    If the TOUCHSCREEN value is set to True, 1, or yes in the DISPLAY
    section of the INI file, the input panel will be shown for controls
    that can be edited.

    At the moment the panel to show is chosen heuristically if the control
    has text, and setText methods. The num pad is shown if the control is a SpinBox.
    """

    def __init__(self, ui_file, parent=None):
        super(VirtualInput, self).__init__(parent)

        self.caps_on = False
        self.focus_object = None
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.BypassWindowManagerHint)
   
        file_path = os.path.join(os.path.dirname(__file__), ui_file)
        #ui_file = QFile(file_path)
        #ui_file.open(QFile.ReadOnly)
        
        #loader = QUiLoader()
        #self.ui = loader.load(ui_file, self)
        #self.ui.show()
        form_class, base_class = PySide6Ui(file_path).load()
        self.ui = form_class()
        self.ui.setupUi(self)

    @Slot(QAbstractButton)
    def on_buttonGroup_buttonPressed(self, btn):
        event = QInputMethodEvent()
        event.setCommitString(btn.text())
        QGuiApplication.sendEvent(self.focus_object, event)

    @Slot()
    def space_key_pressed(self):
        event = QInputMethodEvent()
        event.setCommitString(' ')
        QGuiApplication.sendEvent(self.focus_object, event)

    @Slot()
    def enter_key_pressed(self):
        self.send_key_(Qt.Key_Enter)

    @Slot()
    def esc_key_pressed(self):
        self.send_key_(Qt.Key_Escape)
        self.hide()

    @Slot()
    def backspace_key_pressed(self):
        self.send_key_(Qt.Key_Backspace)

    @Slot()
    def left_key_pressed(self):
        self.send_key_(Qt.Key_Left)

    @Slot()
    def right_key_pressed(self):
        self.send_key_(Qt.Key_Right)

    @Slot()
    def up_key_pressed(self):
        self.send_key_(Qt.Key_Up)

    @Slot()
    def down_key_pressed(self):
        self.send_key_(Qt.Key_Down)

    @Slot()
    def tab_key_pressed(self):
        self.send_key_(Qt.Key_Tab)

    @Slot()
    def home_key_pressed(self):
        self.send_key_(Qt.Key_Home)

    @Slot()
    def end_key_pressed(self):
        self.send_key_(Qt.Key_End)

    @Slot()
    def page_up_key_pressed(self):
        self.send_key_(Qt.Key_PageUp)

    @Slot()
    def page_down_key_pressed(self):
        self.send_key_(Qt.Key_PageDown)

    @Slot()
    def caps_key_pressed(self):
        self.caps_on = not self.caps_on
        for btn in self.buttonGroup.buttons():
            if self.caps_on:
                btn.setText(btn.text().upper())
            else:
                btn.setText(btn.text().lower())

    def set_focus_object(self, value):
        self.focus_object = value
        self.position_keyboard_to_object(self.focus_object)

    def activate(self, obj):
        self.set_focus_object(obj)
        self.show()

    def position_keyboard_to_object(self, obj):
        screen = QApplication.primaryScreen().geometry()
        pos = obj.mapToGlobal(QPoint(0, obj.height()))

        if pos.y() + self.height() > screen.height():
            pos.setY(pos.y() - self.height() - obj.height())
        if pos.x() + self.width() > screen.width():
            pos.setX(pos.x() - self.width() + obj.width())
        if pos.x() + self.width() > screen.width():
            pos.setX(pos.x() - (pos.x() + self.width() - screen.width()))

        self.move(pos.x(), pos.y())

    def send_key_(self, key):
        event = QKeyEvent(QEvent.KeyPress, key, Qt.KeyboardModifier.NoModifier)
        QGuiApplication.postEvent(self.focus_object, event)

        event = QKeyEvent(QEvent.KeyRelease, key, Qt.KeyboardModifier.NoModifier)
        QGuiApplication.postEvent(self.focus_object, event)
