# Copyright (c) 2017-2018, SLAC National Accelerator Laboratory

# This file has been adapted from PyDM, and can be redistributed and/or
# modified in accordance with terms in conditions set forth in the BSD
# 3-Clause License. You can find the complete licence text in the LICENCES
# directory.

# Links:
#   PyDM Project: https://github.com/slaclab/pydm
#   PyDM Licence: https://github.com/slaclab/pydm/blob/master/LICENSE.md

import sip
from qtpy.QtCore import QObject, QVariant
from qtpy.QtWidgets import QAction
from qtpy.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension, \
    QPyDesignerPropertySheetExtension, QDesignerPropertySheetExtension,\
    QDesignerFormWindowInterface

Q_TYPEID = {
    'QDesignerTaskMenuExtension':      'org.qt-project.Qt.Designer.TaskMenu',
    'QDesignerContainerExtension':     'org.qt-project.Qt.Designer.Container',
    'QDesignerPropertySheetExtension': 'org.qt-project.Qt.Designer.PropertySheet'
}

class ExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None):
        super(ExtensionFactory, self).__init__(parent)

    def createExtension(self, obj, iid, parent):
        if iid == Q_TYPEID['QDesignerTaskMenuExtension']:
            return TaskMenuExtension(obj, parent)

        if iid == Q_TYPEID['QDesignerPropertySheetExtension']:
            return PropertySheetExtension(obj, parent)


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


class PropertySheetExtension(object):
    def __init__(self, widget, parent):

        self.parent = parent
        self.widget = widget

        print "initing propery extentions"

        self.widget = widget
        self.formWindow = QDesignerFormWindowInterface.findFormWindow(self.widget)

        # sheet = sip.cast(widget.widget, QDesignerPropertySheetExtension)
        # propertyIndex = sheet.indexOf('windowTitle')
        #
        #
        # sheet.setChanged(propertyIndex, True)


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


# I chatted with some of the Tormach reps for a bit at FabTech, but they were
# really hard to get any info out of and acted as if PathPilot was realy
# propritary. given that they