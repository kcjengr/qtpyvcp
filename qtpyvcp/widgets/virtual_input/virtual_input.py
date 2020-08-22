import os

import linuxcnc
from qtpy import uic, QtWidgets
from qtpy.QtCore import Slot, Qt, QEvent, QPoint
from qtpy.QtGui import QInputMethodEvent, QGuiApplication, QKeyEvent
from qtpy.QtWidgets import QWidget, QAbstractButton, QAbstractSpinBox


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
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.BypassWindowManagerHint)
        uic.loadUi(ui_file, self)

    @Slot(QAbstractButton)
    def on_buttonGroup_buttonPressed(self, btn):
        event = QInputMethodEvent()
        event.setCommitString(btn.text())
        QGuiApplication.sendEvent(self.focus_object, event)

    @Slot()
    def on_space_key_pressed(self):
        event = QInputMethodEvent()
        event.setCommitString(' ')
        QGuiApplication.sendEvent(self.focus_object, event)

    @Slot()
    def on_enter_key_pressed(self):
        self.send_key_(Qt.Key_Enter)

    @Slot()
    def on_esc_key_pressed(self):
        self.send_key_(Qt.Key_Escape)
        self.hide()

    @Slot()
    def on_backspace_key_pressed(self):
        self.send_key_(Qt.Key_Backspace)

    @Slot()
    def on_left_key_pressed(self):
        self.send_key_(Qt.Key_Left)

    @Slot()
    def on_right_key_pressed(self):
        self.send_key_(Qt.Key_Right)

    @Slot()
    def on_up_key_pressed(self):
        self.send_key_(Qt.Key_Up)

    @Slot()
    def on_down_key_pressed(self):
        self.send_key_(Qt.Key_Down)

    @Slot()
    def on_tab_key_pressed(self):
        self.send_key_(Qt.Key_Tab)

    @Slot()
    def on_home_key_pressed(self):
        self.send_key_(Qt.Key_Home)

    @Slot()
    def on_end_key_pressed(self):
        self.send_key_(Qt.Key_End)

    @Slot()
    def on_page_up_key_pressed(self):
        self.send_key_(Qt.Key_PageUp)

    @Slot()
    def on_page_down_key_pressed(self):
        self.send_key_(Qt.Key_PageDown)

    @Slot()
    def on_caps_key_pressed(self):
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
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        pos = obj.mapToGlobal(QPoint(0, obj.height()))

        if pos.y() + self.height() > screen.height():
            pos.setY(pos.y() - self.height() - obj.height())
        if pos.x() + self.width() > screen.width():
            pos.setX(pos.x() - self.width() + obj.width())
        if pos.x() + self.width() > screen.width():
            pos.setX(pos.x() - (pos.x() + self.width() - screen.width()))

        self.move(pos.x(), pos.y())

    def send_key_(self, key):
        event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
        QGuiApplication.postEvent(self.focus_object, event)

        event = QKeyEvent(QEvent.KeyRelease, key, Qt.NoModifier)
        QGuiApplication.postEvent(self.focus_object, event)
