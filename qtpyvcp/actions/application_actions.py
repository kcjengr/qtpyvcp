from qtpy.QtWidgets import QApplication

import qtpyvcp
from qtpyvcp.lib.decorators import action

MAIN_WINDOW = qtpyvcp.WINDOWS.get('mainwindow')

@action('window.maximize')
def maximize_mainwindow():
    MAIN_WINDOW.showMaximized()

@action('window.minimize')
def minimize_mainwindow():
    MAIN_WINDOW.showMinimized()

@action('window.maximize.toggle')
def toggle_window_maximized():
    MAIN_WINDOW.showMinimized()

@action('window.close')
def close_mainwindow():
    MAIN_WINDOW.close()

@action('application.quit')
def quit_application():
    QApplication.instance().quit()
