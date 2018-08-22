"""
Main Application Module

Contains the VCPApplication class with core function and VCP loading logic.
"""
import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, qApp

class VCPApplication(QApplication):

    def __init__(self, vcp=None, ini=None, command_line_args=[], display_args=[],
                 perfmon=False, hide_nav_bar=False, hide_menu_bar=False,
                 hide_status_bar=False, stylesheet_path=None,
                 fullscreen=False):
        super(VCPApplication, self).__init__(command_line_args)

        qApp = QApplication.instance()

        from QtPyVCP.core import Status, Action, Prefs, Info
        from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

        self.status = Status()
        self.action = Action()
        self.prefs = Prefs()
        self.info = Info()

        print vcp, command_line_args

        ui_file = None
        if vcp is not None and os.path.exists(vcp):
            if os.path.isfile(vcp):
                print "VCP does exist"
                directory, filename = os.path.split(vcp)
                name, ext = os.path.splitext(filename)
                if ext == '.ui':
                    print "is a UI file"
                    ui_file = vcp
                elif ext == '.py':
                    print "is a python file"
            elif os.path.isdir(vcp):
                print "VCP is a directory"


        window = VCPMainWindow(ui_file=ui_file)
        window.show()
        self.window = window
