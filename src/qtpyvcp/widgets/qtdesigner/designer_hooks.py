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
        print("DEBUG: DesignerHooks.__init__ called")
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

        print(f"DEBUG: Setting form_editor: {editor}")
        self.__form_editor = editor
        self.setup_hooks()

    def setup_hooks(self):
        self.__set_stylesheet_hook()

    def __set_stylesheet_hook(self):
        print(f"DEBUG: Setting stylesheet hook, form_editor: {self.form_editor}")
        if self.form_editor:
            fwman = self.form_editor.formWindowManager()
            print(f"DEBUG: Form window manager: {fwman}")
            if fwman:
                print("DEBUG: Connecting formWindowAdded signal")
                fwman.formWindowAdded.connect(self.__new_form_added)

    def __new_form_added(self, form_window_interface):
        # Apply stylesheet to the main container after a delay to ensure all widgets are loaded
        print("DEBUG: New form added, scheduling stylesheet application to main container")
        QTimer.singleShot(1000, lambda: self.__apply_stylesheet_to_main_container(form_window_interface))
        # Apply again after 2 seconds to catch any late-created widgets
        QTimer.singleShot(2000, lambda: self.__apply_stylesheet_to_main_container(form_window_interface))

    def __apply_stylesheet_to_main_container(self, form_window_interface):
        print("DEBUG: Applying stylesheet to main container")
        import os
        qss_env = os.getenv('QSS_STYLESHEET')
        print(f"DEBUG: QSS_STYLESHEET env var: {qss_env}")
        main_container = form_window_interface.mainContainer()
        print(f"DEBUG: Main container: {main_container}, type: {type(main_container)}")
        if main_container:
            print(f"DEBUG: Main container children: {len(main_container.children())}")
            # Debug: Print some widget info
            for i, child in enumerate(main_container.children()[:10]):  # First 10 children
                print(f"DEBUG: Child {i}: {child}, class: {child.__class__.__name__}")
                if hasattr(child, 'actionName'):
                    print(f"DEBUG: Child {i} has actionName: {child.actionName}")
                if hasattr(child, 'property'):
                    try:
                        action_name = child.property('actionName')
                        if action_name:
                            print(f"DEBUG: Child {i} actionName property: {action_name}")
                    except:
                        pass
            stylesheet.apply_stylesheet(widget=main_container)
            print("DEBUG: Stylesheet applied to main container")

    def __apply_stylesheet_to_app(self):
        print("DEBUG: __apply_stylesheet_to_app called")
        stylesheet.apply_stylesheet()
