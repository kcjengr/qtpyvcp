#!/usr/bin/env python

from qtpy.QtWidgets import QAction
from qtpy.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension

class ExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None):
        super(ExtensionFactory, self).__init__(parent)

    def createExtension(self, obj, iid, parent):

        # For now check the iid for TaskMenu...
        if iid == "org.qt-project.Qt.Designer.TaskMenu":
            return TaskMenuExtension(obj, parent)
        # In the future we can expand to the others such as Property and etc
        # When the time comes...  we will need a new Extension and
        # the equivalent for TaskMenuExtension classes for the
        # property editor and an elif statement in here to instantiate it...


class TaskMenuExtension(QPyDesignerTaskMenuExtension):
    def __init__(self, widget, parent):
        super(TaskMenuExtension, self).__init__(parent)

        self.widget = widget
        self.__actions = None
        self.__extensions = []
        extensions = getattr(widget, 'extensions', None)

        if extensions is not None:
            for ex in extensions:
                extension = ex(self.widget)
                self.__extensions.append(extension)

    def taskActions(self):
        if self.__actions is None:
            self.__actions = []
            for ex in self.__extensions:
                self.__actions.extend(ex.actions())

        return self.__actions

    def preferredEditAction(self):
        if self.__actions is None:
            self.taskActions()
        if self.__actions:
            return self.__actions[0]


class _PluginExtension(object):
    def __init__(self, widget):
        self.widget = widget
        self._actions = []

    def addTaskMenuAction(self, action_name, callback):
        action = QAction(action_name, self.widget)
        action.triggered.connect(callback)
        self._actions.append(action)

    def actions(self):
        return self._actions
