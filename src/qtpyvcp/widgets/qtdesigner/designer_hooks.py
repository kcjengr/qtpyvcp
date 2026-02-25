# Copyright (c) 2017-2018, SLAC National Accelerator Laboratory

# This file has been adapted from PyDM, and can be redistributed and/or
# modified in accordance with terms in conditions set forth in the BSD
# 3-Clause License. You can find the complete licence text in the LICENCES
# directory.

# Links:
#   PyDM Project: https://github.com/slaclab/pydm
#   PyDM Licence: https://github.com/slaclab/pydm/blob/master/LICENSE.md

from PySide6.QtCore import QTimer

from PySide6.QtWidgets import QWidget

from . import stylesheet

class DesignerHooks(object):
    """Class that handles the integration with QtPyVCP and Qt Designer
    by hooking up slots to signals provided by FormEditor and other classes.
    """
    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.__form_editor = None
        self.__initialized = True

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(DesignerHooks)
            cls.__instance.__initialized = False
        return cls.__instance

    @property
    def form_editor(self):
        return self.__form_editor

    @form_editor.setter
    def form_editor(self, editor):
        if self.form_editor is not None:
            return

        if not editor:
            return

        self.__form_editor = editor
        self.setup_hooks()

    def setup_hooks(self):
        self.__set_stylesheet_hook()

    def __set_stylesheet_hook(self):
        if self.form_editor:
            fwman = self.form_editor.formWindowManager()
            if fwman:
                fwman.formWindowAdded.connect(self.__new_form_added)
                
                # Apply stylesheet to any existing form windows
                for i in range(fwman.formWindowCount()):
                    form_window = fwman.formWindow(i)
                    self.__new_form_added(form_window)
                
                # Also check again after a delay in case .ui file loads later
                QTimer.singleShot(2000, lambda: self.__check_for_delayed_forms(fwman))
    
    def __check_for_delayed_forms(self, fwman):
        for i in range(fwman.formWindowCount()):
            form_window = fwman.formWindow(i)
            self.__new_form_added(form_window)

    def __new_form_added(self, form_window_interface):
        # Apply stylesheet to formContainer (preview wrapper) not mainContainer (actual widget)
        # This prevents Designer from saving the stylesheet to the .ui file
        QTimer.singleShot(500, lambda: self.__apply_stylesheet_to_form_container(form_window_interface))

    def __apply_stylesheet_to_form_container(self, form_window_interface):
        # Use formContainer() instead of mainContainer() - this is the preview wrapper
        # that doesn't affect the actual widget properties saved to .ui file
        try:
            form_container = form_window_interface.formContainer()
            if form_container:
                stylesheet.apply_stylesheet(widget=form_container)
        except AttributeError:
            # Qt6 might have renamed this method, fallback to mainContainer
            main_container = form_window_interface.mainContainer()
            if main_container:
                stylesheet.apply_stylesheet(widget=main_container)
